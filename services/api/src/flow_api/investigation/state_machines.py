from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    Conclusion,
    Evidence,
    Finding,
    ReviewEvent,
)

FindingStatus = Literal["candidate", "in_review", "approved", "rejected"]
FindingDecision = Literal["submitted", "approved", "rejected", "returned"]
EvidenceDecision = Literal["verified", "rejected"]
EvidenceStatus = Literal["pending", "verified", "rejected"]

FINDING_DECISIONS: tuple[FindingDecision, ...] = (
    "submitted",
    "approved",
    "rejected",
    "returned",
)
REVIEWABLE_EVIDENCE_DECISIONS: tuple[EvidenceDecision, ...] = ("verified", "rejected")

EVIDENCE_EVENT_DECISIONS: dict[EvidenceDecision, str] = {
    "verified": "evidence_verified",
    "rejected": "evidence_rejected",
}

FINDING_TRANSITIONS: dict[tuple[str, FindingDecision], FindingStatus] = {
    ("candidate", "submitted"): "in_review",
    ("in_review", "approved"): "approved",
    ("in_review", "rejected"): "rejected",
    ("in_review", "returned"): "candidate",
    ("approved", "returned"): "in_review",
}

EVIDENCE_TRANSITIONS: dict[tuple[str, EvidenceDecision], EvidenceStatus] = {
    ("pending", "verified"): "verified",
    ("pending", "rejected"): "rejected",
    ("rejected", "verified"): "verified",
    ("verified", "rejected"): "rejected",
}

CONCLUSION_SECTIONS = (
    "verified_facts",
    "analysis_judgment",
    "open_questions",
    "recommendation",
)


class ReviewBlockedError(Exception):
    """A review transition is not allowed under the governed state machine."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def decide_finding_transition(
    current_status: str,
    decision: str,
    *,
    evidence_statuses: Sequence[str] = (),
    conclusion_complete: bool = False,
) -> FindingStatus:
    target = FINDING_TRANSITIONS.get((current_status, decision))  # type: ignore[arg-type]
    if target is None:
        raise ReviewBlockedError(
            "invalid_transition",
            f"finding cannot move from {current_status} by {decision}",
        )
    if decision == "approved":
        if any(status != "verified" for status in evidence_statuses):
            blocked = next(
                status for status in evidence_statuses if status in ("pending", "rejected")
            )
            raise ReviewBlockedError(
                f"evidence_{blocked}" if blocked != "verified" else "evidence_blocked",
                "approval requires every evidence row verified",
            )
        if not conclusion_complete:
            raise ReviewBlockedError(
                "conclusion_incomplete",
                "approval requires a conclusion with four non-empty sections",
            )
    return target


def decide_evidence_transition(current_status: str, decision: str) -> EvidenceStatus:
    target = EVIDENCE_TRANSITIONS.get((current_status, decision))  # type: ignore[arg-type]
    if target is None:
        raise ReviewBlockedError(
            "invalid_transition",
            f"evidence cannot move from {current_status} by {decision}",
        )
    return target


def _next_sequence(session: Session, finding_id: object) -> int:
    current = session.scalar(
        select(func.max(ReviewEvent.sequence)).where(ReviewEvent.finding_id == finding_id)  # type: ignore[arg-type]
    )
    return int(current or 0) + 1


def conclusion_is_complete(conclusion: Conclusion | None) -> bool:
    if conclusion is None:
        return False
    return all(
        str(getattr(conclusion, section, "") or "").strip() for section in CONCLUSION_SECTIONS
    )


def apply_finding_decision(
    session: Session,
    finding: Finding,
    decision: str,
    *,
    reviewer: str,
    comment: str | None,
    evidence_statuses: Mapping[object, str] | None = None,
) -> ReviewEvent:
    if evidence_statuses is None:
        statuses = [
            str(status)
            for status in session.scalars(
                select(Evidence.status).where(Evidence.finding_id == finding.id)
            )
        ]
    else:
        statuses = [str(status) for status in evidence_statuses.values()]
    conclusion = session.scalar(select(Conclusion).where(Conclusion.finding_id == finding.id))
    target = decide_finding_transition(
        finding.status,
        decision,
        evidence_statuses=tuple(statuses),
        conclusion_complete=conclusion_is_complete(conclusion),
    )
    event = ReviewEvent(
        finding_id=finding.id,
        sequence=_next_sequence(session, finding.id),
        reviewer=reviewer,
        decision=decision,
        comment=comment,
    )
    session.add(event)
    finding.status = target
    session.flush()
    return event


def apply_evidence_decision(
    session: Session,
    evidence: Evidence,
    decision: str,
    *,
    reviewer: str,
    comment: str | None,
) -> ReviewEvent:
    target = decide_evidence_transition(evidence.status, decision)
    event = ReviewEvent(
        finding_id=evidence.finding_id,
        sequence=_next_sequence(session, evidence.finding_id),
        reviewer=reviewer,
        decision=EVIDENCE_EVENT_DECISIONS[decision],  # type: ignore[index]
        comment=comment,
    )
    session.add(event)
    evidence.status = target
    session.flush()
    return event


__all__ = [
    "CONCLUSION_SECTIONS",
    "EVIDENCE_EVENT_DECISIONS",
    "EVIDENCE_TRANSITIONS",
    "FINDING_DECISIONS",
    "FINDING_TRANSITIONS",
    "REVIEWABLE_EVIDENCE_DECISIONS",
    "ReviewBlockedError",
    "apply_evidence_decision",
    "apply_finding_decision",
    "conclusion_is_complete",
    "decide_evidence_transition",
    "decide_finding_transition",
]
