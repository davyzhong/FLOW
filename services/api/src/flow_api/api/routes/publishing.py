from __future__ import annotations

import hashlib
import logging
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.api.routes.investigations import get_investigation_session
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.publishing import (
    FreezeCandidateLine,
    FreezeCandidateListResponse,
    PublicationAttemptLine,
    PublicationAttemptsResponse,
    PublishingErrorResponse,
    PublishRequest,
    PublishResponse,
    ReportSnapshotCreatedResponse,
    ReportSnapshotFreezeRequest,
    ReportSnapshotLine,
    ReportSnapshotListResponse,
)
from flow_api.infrastructure.logging import log_event
from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot
from flow_api.infrastructure.models.canonical import Period
from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import (
    PublicationAttempt,
    ReportSnapshot,
)
from flow_api.infrastructure.object_store import (
    ImmutableObjectConflictError,
    ImmutableObjectNotFoundError,
    ObjectStore,
)
from flow_api.infrastructure.s3_client import build_s3_client
from flow_api.publication.four_stage import (
    AuditContext,
    FinalizedPublication,
    PublicationError,
    PublicationErrorCode,
    PublicationFormat,
    PublicationIntentNotDurable,
    PublicationOutcomeNotDurable,
    PublicationRequest,
    RendererRegistry,
    build_publication_failure,
    canonical_source_sha256,
    execute_object,
    finalize_failure,
    finalize_success,
    prepare_intent,
)
from flow_api.publication.store_adapter import ProtocolObjectStore
from flow_api.publishing.four_stage_binding import (  # noqa: F401
    _enterprise_of_report_snapshot,
)
from flow_api.publishing.service import PublishingFreezeError, build_report_view
from flow_api.security.audit import AuditUnavailable
from flow_api.security.authorization import Action
from flow_api.security.route_policy import (
    LOADERS,
    AuthorizationContext,
    require_action,
)
from flow_api.settings import get_settings

logger = logging.getLogger("flow.publishing")


router = APIRouter(prefix="/publishing", tags=["publishing"])

SessionDependency = Annotated[Session, Depends(get_investigation_session)]

FORMAT_EXTENSIONS = {"pptx": "pptx", "xlsx": "xlsx", "html": "html", "pdf": "pdf"}
FORMAT_CONTENT_TYPES = {
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "html": "text/html; charset=utf-8",
    "pdf": "application/pdf",
}


@lru_cache
def get_publication_object_store() -> ObjectStore:
    settings = get_settings()
    return ObjectStore(client=build_s3_client(settings), bucket=settings.s3_bucket)


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(status_code=http_status, detail=detail.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# §7 四阶段：资源校验器（binding 模块注册）+ 渲染器闭包
# ---------------------------------------------------------------------------


def _publishing_renderers(view: Any) -> RendererRegistry:
    """路由层构建渲染闭包（§7.2：execute_object 无 Session，数据经闭包注入）。"""
    from flow_api.publishing.renderers import RENDERERS

    return {
        PublicationFormat.HTML: lambda prepared, plan: RENDERERS["html"](view),
        PublicationFormat.XLSX: lambda prepared, plan: RENDERERS["xlsx"](view),
        PublicationFormat.PPTX: lambda prepared, plan: RENDERERS["pptx"](view),
    }


def _audit_context(
    auth: AuthorizationContext, resource_type: str, resource_id: str
) -> AuditContext:
    return AuditContext(
        actor_id=auth.principal.actor_id,
        role=auth.principal.role,
        enterprise_id=auth.principal.enterprise_id,
        correlation_id=auth.correlation_id,
        action=auth.action,
        resource_scope=auth.resource.scope,
        resource_type=resource_type,
        resource_id=resource_id,
        model_boundary=None,
    )


def _publication_http_error(error: PublicationError) -> HTTPException:
    return _error(
        error.http_status,
        error.error_code.value,
        str(error)[:200],
    )


def _run_four_stage(
    session: Session,
    pub_request: PublicationRequest,
    audit_context: AuditContext,
    renderers: RendererRegistry,
    object_store: Any = None,
) -> FinalizedPublication:
    """四阶段编排（§7.3）：两次 caller commit + 失败语义映射。

    intent commit 失败 → 503 publication_intent_not_durable（0 对象写）；
    outcome commit 失败 → 503 publication_outcome_not_durable（按 publication_id 对账）。
    """
    try:
        prepared = prepare_intent(session, pub_request, audit_context)
        session.commit()
    except PublicationError:
        session.rollback()
        raise
    except AuditUnavailable:
        session.rollback()
        raise
    except Exception as error:  # noqa: BLE001 - commit 失败/不确定
        session.rollback()
        raise PublicationIntentNotDurable(f"intent 未持久化: {error}") from error
    try:
        outcome = execute_object(prepared, renderers, object_store)
        failure = build_publication_failure(outcome)
        if failure is None:
            finalized = finalize_success(session, prepared, outcome, audit_context)
        else:
            finalized = finalize_failure(session, prepared, outcome, failure, audit_context)
        session.commit()
    except AuditUnavailable:
        session.rollback()
        raise
    except PublicationError:
        session.rollback()
        raise
    except Exception as error:  # noqa: BLE001
        session.rollback()
        raise PublicationOutcomeNotDurable(
            f"outcome 未持久化，按 publication_id {prepared.publication_id} 对账: {error}"
        ) from error
    return finalized


_DEP_PUBLISH_REPORT = require_action(
    Action.PUBLISHING_REPORT_PUBLISH,
    LOADERS["load_report_snapshot_batch_scope_or_deny_legacy"],
    session_provider=get_investigation_session,
)


@router.post(
    "/snapshots/{report_snapshot_id}/publish",
    response_model=PublishResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": PublishingErrorResponse},
        status.HTTP_409_CONFLICT: {"model": PublishingErrorResponse},
    },
    dependencies=[Depends(_DEP_PUBLISH_REPORT)],
)
def publish_report(
    report_snapshot_id: UUID,
    request: PublishRequest,
    session: SessionDependency,
    auth: Annotated[AuthorizationContext, Depends(_DEP_PUBLISH_REPORT)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PublishResponse:
    if not idempotency_key:
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            "idempotency_key_required",
            "发布必须携带 1–128 字节可打印 ASCII 的 Idempotency-Key（§7.1）",
        )
    report = session.get(ReportSnapshot, report_snapshot_id)
    if report is None:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "publishing_not_found",
            f"report snapshot does not exist: {report_snapshot_id}",
        )
    try:
        view = build_report_view(session, report)
    except PublishingFreezeError as error:
        raise _error(status.HTTP_409_CONFLICT, "freeze_blocked", str(error)) from error
    frozen = report.frozen_view or {}
    view_payload = frozen.get("view") if isinstance(frozen, dict) else {}
    if not isinstance(view_payload, dict):
        view_payload = {}
    unknown = [f for f in request.formats if f not in FORMAT_EXTENSIONS]
    if unknown:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "unsupported_format",
            f"不支持的发布格式：{sorted(unknown)}",
        )
    formats = tuple(
        sorted((PublicationFormat(f) for f in request.formats), key=lambda f: f.value)
    )
    pub_request = PublicationRequest(
        publication_id=request.publication_id,
        idempotency_key=idempotency_key,
        resource_type="report_snapshot",
        resource_id=str(report_snapshot_id),
        enterprise_id=_enterprise_of_report_snapshot(session, report),
        source_payload_sha256=canonical_source_sha256(view_payload),
        formats=formats,
    )
    audit_context = _audit_context(auth, "report_snapshot", str(report_snapshot_id))
    try:
        finalized = _run_four_stage(
            session,
            pub_request,
            audit_context,
            _publishing_renderers(view),
            ProtocolObjectStore(get_publication_object_store()),
        )
    except PublicationError as error:
        code = error.error_code.value
        if code == PublicationErrorCode.FREEZE_CONFLICT.value:
            log_event(
                logger,
                logging.WARNING,
                "publication.blocked",
                report_snapshot_id=str(report_snapshot_id),
                code=code,
            )
        else:
            log_event(
                logger,
                logging.ERROR,
                "publication.failed",
                report_snapshot_id=str(report_snapshot_id),
                code=code,
                detail=str(error)[:200],
            )
        raise _publication_http_error(error) from error
    except AuditUnavailable as error:
        raise _error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "audit_unavailable",
            f"发布审计未 durable，请求被拒绝（fail closed）: {error}",
        ) from error
    log_event(
        logger,
        logging.INFO,
        "publication.succeeded"
        if finalized.status == "published"
        else "publication.finished_failed",
        report_snapshot_id=str(report_snapshot_id),
        publication_id=str(finalized.publication_id),
        status=finalized.status,
    )
    return PublishResponse(
        report_snapshot_id=str(report_snapshot_id),
        outcomes={oc.format.value: oc.status.value for oc in finalized.outcomes},
        publication_id=str(finalized.publication_id),
        status=finalized.status,
    )


@router.get(
    "/snapshots/{report_snapshot_id}/attempts",
    response_model=PublicationAttemptsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": PublishingErrorResponse},
    },
    dependencies=[
        Depends(
            require_action(
                Action.PUBLISHING_ATTEMPT_READ,
                LOADERS["load_report_snapshot_batch_scope_or_deny_legacy"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def publication_attempts(
    report_snapshot_id: UUID,
    session: SessionDependency,
) -> PublicationAttemptsResponse:
    report = session.get(ReportSnapshot, report_snapshot_id)
    if report is None:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "publishing_not_found",
            f"report snapshot does not exist: {report_snapshot_id}",
        )
    attempts = session.scalars(
        select(PublicationAttempt)
        .where(PublicationAttempt.report_snapshot_id == report.id)
        .order_by(PublicationAttempt.sequence)
    ).all()
    return PublicationAttemptsResponse(
        report_snapshot_id=str(report.id),
        attempts=[
            _attempt_line(session, attempt)  #
            for attempt in attempts
        ],
    )


def _attempt_line(session: Session, attempt: PublicationAttempt) -> PublicationAttemptLine:
    stored = (
        session.get(StoredObject, attempt.stored_object_id) if attempt.stored_object_id else None
    )
    download_available = (
        attempt.status == "succeeded" and stored is not None and attempt.format in FORMAT_EXTENSIONS
    )
    return PublicationAttemptLine(
        attempt_id=str(attempt.id),
        sequence=int(attempt.sequence),
        format=str(attempt.format),
        status=str(attempt.status),
        stored_object_id=str(attempt.stored_object_id) if attempt.stored_object_id else None,
        error_message=attempt.error_message,
        size_bytes=stored.size_bytes if stored else None,
        content_type=stored.content_type if stored else None,
        created_at=(
            attempt.created_at.isoformat(timespec="seconds") if attempt.created_at else None
        ),
        download_available=download_available,
        stored_sha256=stored.sha256 if stored else None,
    )


@router.post(
    "/snapshots",
    response_model=ReportSnapshotCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": PublishingErrorResponse}},
    dependencies=[
        Depends(
            require_action(
                Action.PUBLISHING_SNAPSHOT_FREEZE,
                LOADERS["load_body_metric_snapshot_batch_scope_or_deny_legacy"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def freeze_report_snapshot_route(
    request: ReportSnapshotFreezeRequest,
    session: SessionDependency,
) -> ReportSnapshotCreatedResponse:
    """从已发布指标快照与已批准 findings 冻结报告快照（append-only 身份）。"""
    from flow_api.publishing.service import freeze_report_snapshot as _freeze

    try:
        report, _view = _freeze(session, metric_snapshot_id=UUID(request.metric_snapshot_id))
    except PublishingFreezeError as error:
        log_event(
            logger,
            logging.WARNING,
            "report.freeze_blocked",
            metric_snapshot_id=request.metric_snapshot_id,
        )
        raise _error(status.HTTP_409_CONFLICT, "freeze_blocked", str(error)) from error
    session.commit()
    log_event(
        logger,
        logging.INFO,
        "report.snapshot_frozen",
        report_id=str(report.id),
        metric_snapshot_id=request.metric_snapshot_id,
        version=report.version,
    )
    return ReportSnapshotCreatedResponse(
        id=str(report.id),
        metric_snapshot_id=str(report.metric_snapshot_id),
        version=int(report.version),
        title=report.title,
        created_at=report.created_at.isoformat(timespec="seconds") if report.created_at else None,
    )


@router.get(
    "/freeze-candidates",
    response_model=FreezeCandidateListResponse,
    dependencies=[
        Depends(
            require_action(
                Action.PUBLISHING_CANDIDATE_READ,
                LOADERS["load_single_enterprise"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def list_freeze_candidates(session: SessionDependency) -> FreezeCandidateListResponse:
    """已发布指标快照及已批准 Finding 数，供冻结表单选择。"""
    approved_counts = (
        select(Finding.metric_snapshot_id, func.count().label("approved"))
        .where(Finding.status == "approved")
        .group_by(Finding.metric_snapshot_id)
        .subquery()
    )
    rows = session.execute(
        select(MetricSnapshot, Period, approved_counts.c.approved)
        .join(Period, MetricSnapshot.as_of_period_id == Period.id)
        .outerjoin(
            approved_counts,
            MetricSnapshot.id == approved_counts.c.metric_snapshot_id,
        )
        .where(MetricSnapshot.status == "published")
        .order_by(Period.month_key.desc(), MetricSnapshot.created_at.desc())
    ).all()
    return FreezeCandidateListResponse(
        candidates=[
            FreezeCandidateLine(
                metric_snapshot_id=str(snapshot.id),
                batch_id=str(snapshot.batch_id),
                period_label=f"{period.year}-{period.month:02d}" if period else None,
                version=int(snapshot.version),
                approved_findings=int(approved or 0),
                created_at=(
                    snapshot.created_at.isoformat(timespec="seconds")
                    if snapshot.created_at
                    else None
                ),
            )
            for snapshot, period, approved in rows
        ]
    )


@router.get(
    "/snapshots",
    response_model=ReportSnapshotListResponse,
    dependencies=[
        Depends(
            require_action(
                Action.PUBLISHING_SNAPSHOT_READ,
                LOADERS["load_single_enterprise"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def list_report_snapshots(session: SessionDependency) -> ReportSnapshotListResponse:
    reports = session.scalars(
        select(ReportSnapshot).order_by(ReportSnapshot.created_at.desc())
    ).all()
    return ReportSnapshotListResponse(
        snapshots=[
            ReportSnapshotLine(
                id=str(report.id),
                metric_snapshot_id=str(report.metric_snapshot_id),
                version=int(report.version),
                title=report.title,
                created_at=(
                    report.created_at.isoformat(timespec="seconds") if report.created_at else None
                ),
            )
            for report in reports
        ]
    )


@router.get(
    "/attempts/{attempt_id}/download",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": PublishingErrorResponse},
        status.HTTP_409_CONFLICT: {"model": PublishingErrorResponse},
    },
    dependencies=[
        Depends(
            require_action(
                Action.PUBLISHING_ARTIFACT_DOWNLOAD,
                LOADERS["load_attempt_parent_scope_or_deny_legacy"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def download_publication_attempt(attempt_id: UUID, session: SessionDependency) -> Response:
    """下载成功产物的持久化字节：服务端命名 + sha 校验 + no-store/nosniff。"""
    attempt = session.get(PublicationAttempt, attempt_id)
    if attempt is None:
        log_event(
            logger,
            logging.WARNING,
            "download.blocked",
            attempt_id=str(attempt_id),
            code="publication_not_found",
        )
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "publication_not_found",
            f"publication attempt does not exist: {attempt_id}",
        )
    if attempt.status != "succeeded" or attempt.stored_object_id is None:
        raise _error(
            status.HTTP_409_CONFLICT,
            "download_not_available",
            f"attempt {attempt_id} has no downloadable object (status={attempt.status})",
        )
    stored = session.get(StoredObject, attempt.stored_object_id)
    if stored is None:
        raise _error(
            status.HTTP_409_CONFLICT,
            "download_not_available",
            f"attempt {attempt_id} references a missing stored object",
        )
    store = get_publication_object_store()
    try:
        payload = (
            store.read_by_key(stored.object_key, stored.sha256)
            if stored.object_key
            else store.read_by_sha(stored.sha256)
        )
    except ImmutableObjectNotFoundError as error:
        log_event(
            logger,
            logging.ERROR,
            "download.missing_object",
            attempt_id=str(attempt_id),
            sha256=stored.sha256,
        )
        raise _error(
            status.HTTP_409_CONFLICT,
            "download_not_available",
            "登记的发布产物已不在对象存储中，请重新发布",
        ) from error
    except ImmutableObjectConflictError as error:
        raise _error(
            status.HTTP_409_CONFLICT,
            "integrity_check_failed",
            "对象存储内容与登记的 sha256 不一致，已拒绝提供",
        ) from error
    if hashlib.sha256(payload).hexdigest() != stored.sha256:
        log_event(
            logger,
            logging.ERROR,
            "download.integrity_failed",
            attempt_id=str(attempt_id),
            sha256=stored.sha256,
        )
        raise _error(
            status.HTTP_409_CONFLICT,
            "integrity_check_failed",
            "下载内容与登记的 sha256 不一致，已拒绝提供",
        )
    extension = FORMAT_EXTENSIONS[attempt.format]
    parent_id = attempt.report_snapshot_id or attempt.objective_report_snapshot_id
    report_family = "flow-operations" if attempt.objective_report_snapshot_id else "flow-report"
    filename = f"{report_family}-{parent_id}-{attempt.sequence}.{extension}"
    log_event(
        logger,
        logging.INFO,
        "download.served",
        attempt_id=str(attempt_id),
        format=str(attempt.format),
        sha256=stored.sha256,
        size=len(payload),
    )
    return Response(
        content=payload,
        media_type=stored.content_type
        or FORMAT_CONTENT_TYPES.get(str(attempt.format), "application/octet-stream"),
        headers={
            "content-disposition": f'attachment; filename="{filename}"',
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
    )


__all__ = ["get_investigation_session", "router"]
