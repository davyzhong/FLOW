"""Public typed schemas for the governed Copilot API."""

from pydantic import BaseModel, Field

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.copilot.models import StructuredAnswer


class InvestigationQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    actor: str = Field(min_length=1)
    batch_id: str | None = None
    metric_snapshot_id: str | None = None
    analysis_run_id: str | None = None


class MappingExplanationRequest(BaseModel):
    import_version_id: str = Field(min_length=1)
    actor: str = Field(min_length=1)


class ReportOutlineRequest(BaseModel):
    batch_id: str = Field(min_length=1)
    actor: str = Field(min_length=1)


class CopilotInteractionResponse(BaseModel):
    interaction_id: str
    outcome: str
    context_digest: str
    provider: str
    model: str
    template_version: str
    answer: StructuredAnswer


class CopilotErrorResponse(BaseModel):
    detail: ErrorDetail


__all__ = [
    "CopilotErrorResponse",
    "CopilotInteractionResponse",
    "InvestigationQuestionRequest",
    "MappingExplanationRequest",
    "ReportOutlineRequest",
    "StructuredAnswer",
]
