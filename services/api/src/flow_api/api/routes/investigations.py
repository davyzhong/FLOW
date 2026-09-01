from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.investigation import (
    ConclusionResponse,
    ConclusionUpsertRequest,
    EvidenceDecisionRequest,
    EvidenceDecisionResponse,
    FindingTransitionRequest,
    FindingTransitionResponse,
    InvestigationContextResponse,
    InvestigationErrorResponse,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.investigation.repositories import (
    InvestigationIdentityMismatchError,
    InvestigationNotFoundError,
)
from flow_api.investigation.service import InvestigationService
from flow_api.investigation.state_machines import ReviewBlockedError

router = APIRouter(prefix="/investigations", tags=["investigations"])


def get_investigation_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_investigation_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(status_code=http_status, detail=detail.model_dump(mode="json"))


@router.get(
    "/{finding_id}",
    response_model=InvestigationContextResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
        status.HTTP_409_CONFLICT: {"model": InvestigationErrorResponse},
    },
)
def investigation_context(
    finding_id: UUID,
    session: SessionDependency,
    batch_id: Annotated[UUID | None, Query()] = None,
    metric_snapshot_id: Annotated[UUID | None, Query()] = None,
    analysis_run_id: Annotated[UUID | None, Query()] = None,
    source_record_limit: Annotated[int, Query(ge=1, le=100)] = 12,
) -> InvestigationContextResponse:
    try:
        context = InvestigationService().get_context(
            session,
            finding_id,
            batch_id=batch_id,
            metric_snapshot_id=metric_snapshot_id,
            analysis_run_id=analysis_run_id,
            source_record_limit=source_record_limit,
        )
    except InvestigationNotFoundError as error:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "investigation_not_found",
            str(error),
        ) from error
    except InvestigationIdentityMismatchError as error:
        raise _error(
            status.HTTP_409_CONFLICT,
            "investigation_identity_mismatch",
            str(error),
        ) from error
    return InvestigationContextResponse.model_validate(context.model_dump())


@router.post(
    "/{finding_id}/evidence/{evidence_id}/decision",
    response_model=EvidenceDecisionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
        status.HTTP_409_CONFLICT: {"model": InvestigationErrorResponse},
    },
)
def decide_evidence(
    finding_id: UUID,
    evidence_id: UUID,
    request: EvidenceDecisionRequest,
    session: SessionDependency,
) -> EvidenceDecisionResponse:
    try:
        acknowledgement = InvestigationService().decide_evidence(
            session, finding_id, evidence_id, request
        )
    except ReviewBlockedError as error:
        raise _error(status.HTTP_409_CONFLICT, error.code, error.message) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return EvidenceDecisionResponse.model_validate(acknowledgement.model_dump())


@router.put(
    "/{finding_id}/conclusion",
    response_model=ConclusionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
    },
)
def save_conclusion(
    finding_id: UUID,
    request: ConclusionUpsertRequest,
    session: SessionDependency,
) -> ConclusionResponse:
    try:
        acknowledgement = InvestigationService().save_conclusion(session, finding_id, request)
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return ConclusionResponse.model_validate(acknowledgement.model_dump())


@router.post(
    "/{finding_id}/transition",
    response_model=FindingTransitionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
        status.HTTP_409_CONFLICT: {"model": InvestigationErrorResponse},
    },
)
def transition_finding(
    finding_id: UUID,
    request: FindingTransitionRequest,
    session: SessionDependency,
) -> FindingTransitionResponse:
    try:
        acknowledgement = InvestigationService().transition_finding(session, finding_id, request)
    except ReviewBlockedError as error:
        raise _error(status.HTTP_409_CONFLICT, error.code, error.message) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return FindingTransitionResponse.model_validate(acknowledgement.model_dump())


__all__ = ["get_investigation_session", "router"]
