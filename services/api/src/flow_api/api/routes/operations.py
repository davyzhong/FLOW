"""O2：经营轨六主题概览 typed 只读端点（D050/OP-0 分层，缺失不补造）。"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.schemas.publishing import (
    PublicationAttemptLine,
    PublicationAttemptsResponse,
    PublishRequest,
    PublishResponse,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.logging import log_event
from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import PublicationAttempt
from flow_api.infrastructure.models.statement import StatementReport
from flow_api.operations.engine import (
    OperationsOverview,
    OperationsSnapshotLine,
    OperationsSnapshotList,
    PublicOperatingPeriodList,
    build_operations_overview,
    build_public_operating_overview,
    list_public_operating_periods,
)
from flow_api.publication.four_stage import (
    AuditContext,
    PublicationError,
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
from flow_api.publishing.objective_freeze import (
    ObjectiveFreezeError,
    ObjectiveReportSnapshot,
)
from flow_api.security.audit import AuditUnavailable
from flow_api.security.authorization import Action
from flow_api.security.route_policy import (
    LOADERS,
    AuthorizationContext,
    require_action,
)

router = APIRouter(prefix="/operations", tags=["operations"])


def get_operations_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_operations_session)]


@router.get(
    "/public-periods",
    response_model=PublicOperatingPeriodList,
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_PUBLIC_READ,
                LOADERS["load_public_operations_catalog"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_public_operating_periods() -> PublicOperatingPeriodList:
    """列出公开经营事实的真实期间；不合成月度期间。"""

    return PublicOperatingPeriodList(periods=list_public_operating_periods())


@router.get(
    "/public/{stock_code}/{period_label}",
    response_model=OperationsOverview,
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_PUBLIC_READ,
                LOADERS["load_public_operations_disclosure"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_public_operating_overview(
    stock_code: Annotated[str, Path(max_length=32)],
    period_label: Annotated[str, Path(max_length=64)],
) -> OperationsOverview:
    """读取没有完整财报的公开经营期间，只呈现严格同期间事实。"""

    try:
        return build_public_operating_overview(stock_code=stock_code, selected_period=period_label)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "operating_period_not_found",
                "message": "未找到该公司的公开经营披露期间",
            },
        ) from error


@router.get(
    "/overview/{report_id}",
    response_model=OperationsOverview,
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_OVERVIEW_READ,
                LOADERS["load_public_statement_report"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_operations_overview(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> OperationsOverview:
    """六主题经营概览：L1 出数，L2/L3 typed not_applicable（U 遗留/O2）。"""
    report = session.get(StatementReport, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "statement_report_not_found", "message": "财报不存在"},
        )
    return build_operations_overview(session, report_id=str(report.id))


@router.get(
    "/snapshots",
    response_model=OperationsSnapshotList,
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_SNAPSHOT_READ,
                LOADERS["load_public_operations_snapshot_collection"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def list_operations_snapshots(session: SessionDependency) -> OperationsSnapshotList:
    rows = session.execute(
        select(ObjectiveReportSnapshot, StatementReport)
        .join(
            StatementReport,
            ObjectiveReportSnapshot.statement_report_id == StatementReport.id,
        )
        .where(ObjectiveReportSnapshot.report_type == "operations_overview")
        .order_by(ObjectiveReportSnapshot.created_at.desc())
    ).all()
    return OperationsSnapshotList(
        snapshots=[
            OperationsSnapshotLine(
                id=str(snapshot.id),
                statement_report_id=str(report.id),
                version=snapshot.version,
                company_name=report.company_name,
                stock_code=report.stock_code,
                period_label=report.period_label,
                payload_hash=snapshot.payload_hash,
                created_at=(
                    snapshot.created_at.isoformat(timespec="seconds")
                    if snapshot.created_at
                    else None
                ),
            )
            for snapshot, report in rows
        ]
    )


# ---------------------------------------------------------------------------
# §7 四阶段：资源校验器（binding 模块注册）+ 渲染器闭包
# ---------------------------------------------------------------------------

from flow_api.operations.four_stage_binding import _verify_operations_snapshot  # noqa: E402,F401


def _operations_renderers(payload: dict[str, Any]) -> RendererRegistry:
    """路由层渲染闭包：html 直出，pdf 走 pinned-Chromium 打印机（§7.2 无 Session）。"""
    from flow_api.operations.renderers import (
        render_operations_html,
        render_operations_pptx,
        render_operations_xlsx,
    )

    html_bytes = render_operations_html(payload).encode("utf-8")
    return {
        PublicationFormat.HTML: lambda prepared, plan: html_bytes,
        PublicationFormat.XLSX: lambda prepared, plan: render_operations_xlsx(payload),
        PublicationFormat.PPTX: lambda prepared, plan: render_operations_pptx(payload),
        PublicationFormat.PDF: lambda prepared, plan: _default_pdf_printer(html_bytes),
    }


def _default_pdf_printer(html: bytes) -> bytes:
    import tempfile
    from pathlib import Path

    from flow_api.statements.objective_report_pdf import print_pdf

    with tempfile.TemporaryDirectory() as temporary_directory:
        output = Path(temporary_directory) / "operations.pdf"
        print_pdf(
            html.decode("utf-8"),
            out_path=output,
            footer_left="FLOW 经营分析概览",
        )
        return output.read_bytes()


def _operations_audit_context(auth: AuthorizationContext, snapshot_id: str) -> AuditContext:
    return AuditContext(
        actor_id=auth.principal.actor_id,
        role=auth.principal.role,
        enterprise_id=auth.principal.enterprise_id,
        correlation_id=auth.correlation_id,
        action=Action.OPERATIONS_REPORT_PUBLISH,
        resource_scope="public",
        resource_type="operations_snapshot",
        resource_id=snapshot_id,
        model_boundary=None,
    )


def _operations_object_store() -> Any:
    from flow_api.infrastructure.object_store import ObjectStore
    from flow_api.infrastructure.s3_client import build_s3_client
    from flow_api.settings import get_settings

    settings = get_settings()
    return ObjectStore(client=build_s3_client(settings), bucket=settings.s3_bucket)


_DEP_PUBLISH_OPERATIONS = require_action(
    Action.OPERATIONS_REPORT_PUBLISH,
    LOADERS["load_public_statement_report"],
    session_provider=get_operations_session,
)


@router.post(
    "/overview/{report_id}/publish",
    response_model=PublishResponse,
    dependencies=[Depends(_DEP_PUBLISH_OPERATIONS)],
)
def publish_operations_overview(
    session: SessionDependency,
    report_id: Annotated[UUID, Path()],
    request: PublishRequest,
    auth: Annotated[AuthorizationContext, Depends(_DEP_PUBLISH_OPERATIONS)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PublishResponse:
    from flow_api.operations.freeze import freeze_operations_overview

    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "idempotency_key_required",
                "message": "发布必须携带 1–128 字节可打印 ASCII 的 Idempotency-Key（§7.1）",
            },
        )
    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
        session.commit()
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        log_event(
            logging.getLogger("flow.operations"),
            logging.WARNING,
            "operations.publish_blocked",
            report_id=str(report_id),
            code=error.code,
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error

    unknown = [f for f in request.formats if f not in ("pptx", "xlsx", "html", "pdf")]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "unsupported_format",
                "message": f"不支持的发布格式：{sorted(unknown)}",
            },
        )
    formats = tuple(
        sorted((PublicationFormat(f) for f in request.formats), key=lambda f: f.value)
    )
    pub_request = PublicationRequest(
        publication_id=request.publication_id,
        idempotency_key=idempotency_key,
        resource_type="operations_snapshot",
        resource_id=str(snapshot.id),
        enterprise_id=None,
        source_payload_sha256=canonical_source_sha256(snapshot.payload),
        formats=formats,
    )
    audit_context = _operations_audit_context(auth, str(snapshot.id))
    try:
        prepared = prepare_intent(session, pub_request, audit_context)
        session.commit()
    except PublicationError:
        session.rollback()
        raise
    except AuditUnavailable:
        session.rollback()
        raise
    except Exception as error:  # noqa: BLE001 - intent commit 失败/不确定
        session.rollback()
        raise PublicationIntentNotDurable(f"intent 未持久化: {error}") from error
    try:
        outcome = execute_object(
            prepared,
            _operations_renderers(snapshot.payload),
            ProtocolObjectStore(_operations_object_store()),
        )
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
    log_event(
        logging.getLogger("flow.operations"),
        logging.INFO,
        "operations.published" if finalized.status == "published" else "operations.publish_failed",
        report_id=str(report_id),
        snapshot_id=str(snapshot.id),
        publication_id=str(finalized.publication_id),
        status=finalized.status,
    )
    return PublishResponse(
        report_snapshot_id=str(snapshot.id),
        outcomes={oc.format.value: oc.status.value for oc in finalized.outcomes},
        publication_id=str(finalized.publication_id),
        status=finalized.status,
    )


@router.get(
    "/snapshots/{snapshot_id}/attempts",
    response_model=PublicationAttemptsResponse,
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_ATTEMPT_READ,
                LOADERS["load_public_operations_snapshot"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def operations_publication_attempts(
    session: SessionDependency, snapshot_id: Annotated[UUID, Path()]
) -> PublicationAttemptsResponse:
    snapshot = session.get(ObjectiveReportSnapshot, snapshot_id)
    if snapshot is None or snapshot.report_type != "operations_overview":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "operations_snapshot_not_found",
                "message": "经营报告快照不存在",
            },
        )
    attempts = session.scalars(
        select(PublicationAttempt)
        .where(PublicationAttempt.objective_report_snapshot_id == snapshot.id)
        .order_by(PublicationAttempt.sequence)
    ).all()
    lines: list[PublicationAttemptLine] = []
    for attempt in attempts:
        stored = (
            session.get(StoredObject, attempt.stored_object_id)
            if attempt.stored_object_id
            else None
        )
        lines.append(
            PublicationAttemptLine(
                attempt_id=str(attempt.id),
                sequence=attempt.sequence,
                format=attempt.format,
                status=attempt.status,
                stored_object_id=(
                    str(attempt.stored_object_id) if attempt.stored_object_id else None
                ),
                error_message=attempt.error_message,
                size_bytes=stored.size_bytes if stored else None,
                content_type=stored.content_type if stored else None,
                created_at=(
                    attempt.created_at.isoformat(timespec="seconds") if attempt.created_at else None
                ),
                download_available=attempt.status == "succeeded" and stored is not None,
                stored_sha256=stored.sha256 if stored else None,
            )
        )
    return PublicationAttemptsResponse(report_snapshot_id=str(snapshot.id), attempts=lines)


@router.post(
    "/overview/{report_id}/freeze",
    responses={404: {"content": {}}, 422: {"content": {}}},
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_SNAPSHOT_FREEZE,
                LOADERS["load_public_statement_report"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def freeze_operations_snapshot(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> dict[str, str | int]:
    """六主题概览冻结：过 U5 客观资格合同后幂等落快照（O3 slice-2）。"""
    from flow_api.operations.freeze import freeze_operations_overview

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return {
        "snapshot_id": str(snapshot.id),
        "version": snapshot.version,
        "report_type": snapshot.report_type,
        "payload_hash": snapshot.payload_hash,
    }


@router.get(
    "/overview/{report_id}/html",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_RENDER_AND_FREEZE,
                LOADERS["load_public_statement_report"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_operations_overview_html(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_html

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    html = render_operations_html(snapshot.payload)
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"cache-control": "no-store", "x-content-type-options": "nosniff"},
    )


@router.get(
    "/overview/{report_id}/xlsx",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_RENDER_AND_FREEZE,
                LOADERS["load_public_statement_report"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_operations_overview_xlsx(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_xlsx

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return Response(
        content=render_operations_xlsx(snapshot.payload),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "content-disposition": 'attachment; filename="flow-operations.xlsx"',
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
    )


@router.get(
    "/overview/{report_id}/pptx",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_RENDER_AND_FREEZE,
                LOADERS["load_public_statement_report"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_operations_overview_pptx(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_pptx

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return Response(
        content=render_operations_pptx(snapshot.payload),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "content-disposition": 'attachment; filename="flow-operations.pptx"',
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
    )


@router.get(
    "/overview/{report_id}/pdf",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
    dependencies=[
        Depends(
            require_action(
                Action.OPERATIONS_RENDER_AND_FREEZE,
                LOADERS["load_public_statement_report"],
                session_provider=get_operations_session,
            )
        )
    ],
)
def get_operations_overview_pdf(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    import tempfile
    from pathlib import Path

    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_html
    from flow_api.statements.objective_report_pdf import print_pdf

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    html = render_operations_html(snapshot.payload)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "operations.pdf"
        try:
            print_pdf(
                html,
                out_path=out,
                footer_left=f"FLOW 经营分析概览 · {snapshot.payload_hash[:16]}",
            )
            data = out.read_bytes()
        except RuntimeError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "chromium_unavailable", "message": str(error)},
            ) from error
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"cache-control": "no-store", "x-content-type-options": "nosniff"},
    )


__all__ = ["get_operations_session", "router"]
