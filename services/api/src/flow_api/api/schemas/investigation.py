"""Public typed request and response schemas for Investigation."""

from pydantic import BaseModel, ConfigDict

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.investigation.models import (
    ConclusionUpsertRequest,
    EvidenceDecisionRequest,
    FindingTransitionRequest,
    InvestigationContext,
    MutationAcknowledgement,
)


class InvestigationContextResponse(InvestigationContext):
    """Read-only evidence-first Investigation context."""


class InvestigationSourceCellResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_id: str
    source_file_name: str
    sheet_name: str
    source_row: int
    source_column: str
    canonical_field: str
    raw_value: dict[str, object]
    transformed_value: dict[str, object]


class EvidenceDecisionResponse(MutationAcknowledgement):
    """Acknowledgement of an evidence review decision."""


class ConclusionResponse(MutationAcknowledgement):
    """Acknowledgement of a stored Finance BP conclusion."""


class FindingTransitionResponse(MutationAcknowledgement):
    """Acknowledgement of a governed Finding state transition."""


class InvestigationErrorResponse(BaseModel):
    detail: ErrorDetail


__all__ = [
    "ConclusionResponse",
    "ConclusionUpsertRequest",
    "EvidenceDecisionRequest",
    "EvidenceDecisionResponse",
    "FindingListItem",
    "FindingListResponse",
    "FindingTransitionRequest",
    "FindingTransitionResponse",
    "InvestigationContextResponse",
    "InvestigationSourceCellResponse",
    "InvestigationErrorResponse",
    "MutationAcknowledgement",
]


class FindingListItem(BaseModel):
    """调查列表项：携带 Investigation 身份交接所需的全部标识（D036）。"""

    finding_id: str
    title: str
    status: str
    finding_type: str | None
    impact_amount: str
    comparison_basis: str | None
    total_score: str | None
    batch_id: str | None
    metric_snapshot_id: str
    analysis_run_id: str | None
    created_at: str | None


class FindingListResponse(BaseModel):
    findings: list[FindingListItem]
