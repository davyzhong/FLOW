from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import boto3  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.routes.investigations import get_investigation_session
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.publishing import (
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
from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import (
    PublicationAttempt,
    ReportSnapshot,
)
from flow_api.infrastructure.object_store import ObjectStore
from flow_api.publishing.publication import PublicationService
from flow_api.publishing.service import PublishingFreezeError
from flow_api.settings import get_settings

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
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
    )
    return ObjectStore(client=client, bucket=settings.s3_bucket)


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(status_code=http_status, detail=detail.model_dump(mode="json"))


def _service() -> PublicationService:
    """Deterministic in-process renderers for pptx/xlsx/html.

    PDF printing requires the pinned-Chromium printer; attempts without one
    are recorded as failed and remain retryable.
    """
    return PublicationService()


@router.post(
    "/snapshots/{report_snapshot_id}/publish",
    response_model=PublishResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": PublishingErrorResponse},
    },
)
def publish_report(
    report_snapshot_id: UUID,
    request: PublishRequest,
    session: SessionDependency,
) -> PublishResponse:
    service = _service()
    try:
        outcomes = service.publish(session, report_snapshot_id, formats=tuple(request.formats))
    except PublishingFreezeError as error:
        raise _error(status.HTTP_409_CONFLICT, "freeze_blocked", str(error)) from error
    except Exception as error:  # noqa: BLE001
        raise _error(status.HTTP_404_NOT_FOUND, "publishing_failed", str(error)[:200]) from error
    return PublishResponse(
        report_snapshot_id=str(report_snapshot_id),
        outcomes=outcomes,
    )


@router.get(
    "/snapshots/{report_snapshot_id}/attempts",
    response_model=PublicationAttemptsResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": PublishingErrorResponse},
    },
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
        attempt.status == "succeeded"
        and stored is not None
        and attempt.format in FORMAT_EXTENSIONS
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
)
def freeze_report_snapshot_route(
    request: ReportSnapshotFreezeRequest,
    session: SessionDependency,
) -> ReportSnapshotCreatedResponse:
    """从已发布指标快照与已批准 findings 冻结报告快照（append-only 身份）。"""
    from flow_api.publishing.service import freeze_report_snapshot as _freeze

    try:
        report, _view = _freeze(
            session, metric_snapshot_id=UUID(request.metric_snapshot_id)
        )
    except PublishingFreezeError as error:
        raise _error(status.HTTP_409_CONFLICT, "freeze_blocked", str(error)) from error
    session.commit()
    return ReportSnapshotCreatedResponse(
        id=str(report.id),
        metric_snapshot_id=str(report.metric_snapshot_id),
        version=int(report.version),
        title=report.title,
        created_at=report.created_at.isoformat(timespec="seconds") if report.created_at else None,
    )


@router.get("/snapshots", response_model=ReportSnapshotListResponse)
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
)
def download_publication_attempt(attempt_id: UUID, session: SessionDependency) -> Response:
    """下载成功产物的持久化字节：服务端命名 + sha 校验 + no-store/nosniff。"""
    attempt = session.get(PublicationAttempt, attempt_id)
    if attempt is None:
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
    payload = store.read_by_sha(stored.sha256)
    if hashlib.sha256(payload).hexdigest() != stored.sha256:
        raise _error(
            status.HTTP_409_CONFLICT,
            "integrity_check_failed",
            "下载内容与登记的 sha256 不一致，已拒绝提供",
        )
    extension = FORMAT_EXTENSIONS[attempt.format]
    filename = f"flow-report-{attempt.report_snapshot_id}-{attempt.sequence}.{extension}"
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
