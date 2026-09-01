from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
)
from flow_api.infrastructure.models.publishing import (
    PublicationAttempt,
    ReportSnapshot,
)
from flow_api.publishing.publication import PublicationService

router = APIRouter(prefix="/publishing", tags=["publishing"])

SessionDependency = Annotated[Session, Depends(get_investigation_session)]


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
            PublicationAttemptLine(
                sequence=int(attempt.sequence),
                format=str(attempt.format),
                status=str(attempt.status),
                stored_object_id=(
                    str(attempt.stored_object_id) if attempt.stored_object_id else None
                ),
                error_message=attempt.error_message,
            )
            for attempt in attempts
        ],
    )


__all__ = ["get_investigation_session", "router"]
