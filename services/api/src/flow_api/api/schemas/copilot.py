"""Public typed schemas for the governed Copilot API."""

from pydantic import BaseModel, Field

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.copilot.models import StructuredAnswer


class InvestigationQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    # §3.3：actor 只来自 Principal；body 可省略，冲突值 → 409 actor_conflict
    actor: str | None = Field(default=None, max_length=128)
    batch_id: str | None = None
    metric_snapshot_id: str | None = None
    analysis_run_id: str | None = None


class MappingExplanationRequest(BaseModel):
    import_version_id: str = Field(min_length=1)
    # §3.3：actor 只来自 Principal；body 可省略，冲突值 → 409 actor_conflict
    actor: str | None = Field(default=None, max_length=128)


class ReportOutlineRequest(BaseModel):
    batch_id: str = Field(min_length=1)
    # §3.3：actor 只来自 Principal；body 可省略，冲突值 → 409 actor_conflict
    actor: str | None = Field(default=None, max_length=128)


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
