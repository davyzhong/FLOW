from __future__ import annotations

import pytest
from integration.analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import publish_analysis_run
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import Evidence, Finding
from flow_api.investigation.state_machines import (
    FINDING_DECISIONS,
    REVIEWABLE_EVIDENCE_DECISIONS,
    ReviewBlockedError,
    apply_evidence_decision,
    apply_finding_decision,
    decide_evidence_transition,
    decide_finding_transition,
)


class TestFindingTransitions:
    def test_allowed_transitions_resolve_to_expected_states(self) -> None:
        assert decide_finding_transition("candidate", "submitted") == "in_review"
        assert (
            decide_finding_transition(
                "in_review",
                "approved",
                evidence_statuses=("verified",),
                conclusion_complete=True,
            )
            == "approved"
        )
        assert decide_finding_transition("in_review", "rejected") == "rejected"
        assert decide_finding_transition("in_review", "returned") == "candidate"
        assert decide_finding_transition("approved", "returned") == "in_review"

    def test_forbidden_transitions_are_rejected(self) -> None:
        for current, decision in (
            ("candidate", "approved"),
            ("candidate", "rejected"),
            ("candidate", "returned"),
            ("approved", "approved"),
            ("approved", "submitted"),
            ("rejected", "submitted"),
            ("rejected", "approved"),
            ("rejected", "returned"),
        ):
            with pytest.raises(ReviewBlockedError) as error:
                decide_finding_transition(current, decision)
            assert error.value.code == "invalid_transition"

    def test_unknown_decision_is_rejected(self) -> None:
        with pytest.raises(ReviewBlockedError) as error:
            decide_finding_transition("candidate", "unknown")
        assert error.value.code == "invalid_transition"

    def test_approval_requires_all_evidence_verified(self) -> None:
        with pytest.raises(ReviewBlockedError) as error:
            decide_finding_transition(
                "in_review",
                "approved",
                evidence_statuses=("verified", "pending"),
                conclusion_complete=True,
            )
        assert error.value.code == "evidence_pending"

        with pytest.raises(ReviewBlockedError) as error:
            decide_finding_transition(
                "in_review",
                "approved",
                evidence_statuses=("verified", "rejected"),
                conclusion_complete=True,
            )
        assert error.value.code == "evidence_rejected"

    def test_approval_requires_complete_conclusion(self) -> None:
        with pytest.raises(ReviewBlockedError) as error:
            decide_finding_transition(
                "in_review",
                "approved",
                evidence_statuses=("verified",),
                conclusion_complete=False,
            )
        assert error.value.code == "conclusion_incomplete"

    def test_decision_vocabulary_is_frozen(self) -> None:
        assert FINDING_DECISIONS == ("submitted", "approved", "rejected", "returned")
        assert REVIEWABLE_EVIDENCE_DECISIONS == ("verified", "rejected")


class TestEvidenceTransitions:
    def test_allowed_evidence_transitions(self) -> None:
        assert decide_evidence_transition("pending", "verified") == "verified"
        assert decide_evidence_transition("pending", "rejected") == "rejected"
        assert decide_evidence_transition("rejected", "verified") == "verified"
        assert decide_evidence_transition("verified", "rejected") == "rejected"

    def test_unknown_evidence_status_is_rejected(self) -> None:
        with pytest.raises(ReviewBlockedError) as error:
            decide_evidence_transition("unknown", "verified")
        assert error.value.code == "invalid_transition"

    def test_invalid_evidence_transition_is_rejected(self) -> None:
        with pytest.raises(ReviewBlockedError) as error:
            decide_evidence_transition("verified", "verified")
        assert error.value.code == "invalid_transition"


class TestSessionBoundAppliers:
    def test_apply_finding_decision_appends_sequenced_review_event(
        self, analysis_session: Session
    ) -> None:
        publish_analysis_run(analysis_session)
        finding = analysis_session.scalars(
            select(Finding).order_by(Finding.total_score.desc())
        ).first()
        assert finding is not None
        first = apply_finding_decision(
            analysis_session, finding, "submitted", reviewer="陈晨", comment=None
        )
        second = apply_finding_decision(
            analysis_session, finding, "returned", reviewer="王总", comment="补预算口径"
        )
        assert first.sequence == 1
        assert second.sequence == 2
        assert second.decision == "returned"
        assert finding.status == "candidate"

    def test_apply_evidence_decision_updates_status_and_appends_event(
        self, analysis_session: Session
    ) -> None:
        publish_analysis_run(analysis_session)
        finding = analysis_session.scalars(
            select(Finding).order_by(Finding.total_score.desc())
        ).first()
        assert finding is not None
        evidence = analysis_session.scalars(
            select(Evidence).where(Evidence.finding_id == finding.id)
        ).first()
        assert evidence is not None
        event = apply_evidence_decision(
            analysis_session, evidence, "rejected", reviewer="陈晨", comment="口径存疑"
        )
        assert evidence.status == "rejected"
        assert event.decision == "evidence_rejected"
        assert event.sequence >= 1


def test_approval_rejects_empty_evidence_set() -> None:
    with pytest.raises(ReviewBlockedError, match="evidence"):
        decide_finding_transition(
            "in_review", "approved", evidence_statuses=(), conclusion_complete=True
        )


def test_empty_evidence_is_visible_as_eligibility_blocker() -> None:
    from flow_api.investigation.service import InvestigationService

    assert "evidence_pending" in InvestigationService()._eligibility_blockers(
        "in_review",
        (),
        True,
    )
