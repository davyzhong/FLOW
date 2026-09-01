"""Public typed request and response schemas for Investigation."""

from pydantic import BaseModel

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
    "FindingTransitionRequest",
    "FindingTransitionResponse",
    "InvestigationContextResponse",
    "InvestigationErrorResponse",
    "MutationAcknowledgement",
]
