from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from flow_api.api.routes.investigations import get_investigation_session
from flow_api.api.schemas.copilot import (
    CopilotErrorResponse,
    CopilotInteractionResponse,
    InvestigationQuestionRequest,
    MappingExplanationRequest,
    ReportOutlineRequest,
)
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.copilot.providers import DeterministicProvider
from flow_api.copilot.service import (
    CopilotInteractionResult,
    CopilotService,
    CopilotValidationError,
)
from flow_api.investigation.repositories import (
    InvestigationIdentityMismatchError,
    InvestigationNotFoundError,
)

router = APIRouter(prefix="/copilot", tags=["copilot"])

SessionDependency = Annotated[Session, Depends(get_investigation_session)]


def _service() -> CopilotService:
    """Return the configured copilot service.

    V1 ships the deterministic offline provider; a live provider requires an
    explicit settings flag and is never used in tests or CI.
    """
    return CopilotService(provider=DeterministicProvider())


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(status_code=http_status, detail=detail.model_dump(mode="json"))


@router.post(
    "/investigations/{finding_id}/ask",
    response_model=CopilotInteractionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": CopilotErrorResponse},
        status.HTTP_409_CONFLICT: {"model": CopilotErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CopilotErrorResponse},
    },
)
def ask_investigation_question(
    finding_id: UUID,
    request: InvestigationQuestionRequest,
    session: SessionDependency,
) -> CopilotInteractionResponse:
    service = _service()
    try:
        result = service.answer_investigation_question(
            session,
            finding_id,
            question=request.question,
            actor=request.actor,
            batch_id=(
                UUID(request.batch_id) if request.batch_id else None
            ),
            metric_snapshot_id=(
                UUID(request.metric_snapshot_id) if request.metric_snapshot_id else None
            ),
            analysis_run_id=(
                UUID(request.analysis_run_id) if request.analysis_run_id else None
            ),
        )
    except CopilotValidationError as error:
        session.commit()
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "copilot_validation_failed",
            "; ".join(error.reasons),
        ) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    except InvestigationIdentityMismatchError as error:
        raise _error(
            status.HTTP_409_CONFLICT, "investigation_identity_mismatch", str(error)
        ) from error
    return _interaction_response(result)


@router.post(
    "/explain-mapping",
    response_model=CopilotInteractionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": CopilotErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CopilotErrorResponse},
    },
)
def explain_mapping(
    request: MappingExplanationRequest,
    session: SessionDependency,
) -> CopilotInteractionResponse:
    service = _service()
    try:
        result = service.explain_mapping(
            session,
            UUID(request.import_version_id),
            actor=request.actor,
        )
    except CopilotValidationError as error:
        session.commit()
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "copilot_validation_failed",
            "; ".join(error.reasons),
        ) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return _interaction_response(result)


@router.post(
    "/report-outline",
    response_model=CopilotInteractionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": CopilotErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": CopilotErrorResponse},
    },
)
def draft_report_outline(
    request: ReportOutlineRequest,
    session: SessionDependency,
) -> CopilotInteractionResponse:
    service = _service()
    try:
        result = service.draft_report_outline(
            session,
            UUID(request.batch_id),
            actor=request.actor,
        )
    except CopilotValidationError as error:
        session.commit()
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "copilot_validation_failed",
            "; ".join(error.reasons),
        ) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return _interaction_response(result)


def _interaction_response(result: CopilotInteractionResult) -> CopilotInteractionResponse:
    return CopilotInteractionResponse(
        interaction_id=result.interaction_id,
        outcome=result.outcome,
        context_digest=result.context_digest,
        provider=result.response.provider,
        model=result.response.model,
        template_version=result.response.template_version,
        answer=result.response.answer,
    )


__all__ = ["get_investigation_session", "router"]
