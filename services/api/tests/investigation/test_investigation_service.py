from __future__ import annotations

import uuid

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
from flow_api.investigation.models import (
    ConclusionUpsertRequest,
    EvidenceDecisionRequest,
    FindingTransitionRequest,
)
from flow_api.investigation.repositories import InvestigationIdentityMismatchError
from flow_api.investigation.service import InvestigationService
from flow_api.investigation.state_machines import ReviewBlockedError


def top_finding(session: Session) -> Finding:
    finding = session.scalars(select(Finding).order_by(Finding.total_score.desc())).first()
    assert finding is not None
    return finding


def test_context_projects_identity_drivers_evidence_and_lineage(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)
    finding = top_finding(analysis_session)
    context = InvestigationService().get_context(
        analysis_session,
        finding.id,
        batch_id=run.metric_snapshot.batch_id,
        metric_snapshot_id=run.metric_snapshot_id,
        analysis_run_id=run.id,
    )
    assert context.identity.analysis_run_id == str(run.id)
    assert context.finding.finding_id == str(finding.id)
    assert context.result is not None
    assert context.metric.engine_version == "flow-analysis/1"
    assert context.metric.formula
    assert len(context.drivers) >= 1
    assert [driver.position for driver in context.drivers] == list(
        range(1, len(context.drivers) + 1)
    )
    assert len(context.evidence) == 5
    assert {item.status for item in context.evidence} == {"verified"}
    assert len(context.source_records) >= 1
    record = context.source_records[0]
    assert record.sheet_name
    assert record.source_row >= 1
    assert record.source_file_name.endswith(".xlsx")
    assert context.conclusion.exists is False
    assert "conclusion_incomplete" in context.eligibility_blockers
    assert "finding_not_submitted" in context.eligibility_blockers


def test_context_rejects_identity_mismatch(analysis_session: Session) -> None:
    publish_analysis_run(analysis_session)
    finding = top_finding(analysis_session)
    assert finding.analysis_run_id is not None
    with pytest.raises(InvestigationIdentityMismatchError):
        InvestigationService().get_context(
            analysis_session,
            finding.id,
            batch_id=finding.metric_snapshot.batch_id,
            metric_snapshot_id=finding.metric_snapshot_id,
            analysis_run_id=uuid.uuid4(),
        )


def test_review_cycle_blocks_and_allows_approval(analysis_session: Session) -> None:
    publish_analysis_run(analysis_session)
    service = InvestigationService()
    finding = top_finding(analysis_session)
    context = service.get_context(analysis_session, finding.id)
    evidence_id = uuid.UUID(context.evidence[0].evidence_id)

    service.decide_evidence(
        analysis_session,
        finding.id,
        evidence_id,
        EvidenceDecisionRequest(decision="rejected", reviewer="陈晨", comment="口径存疑"),
    )

    blocked = service.get_context(analysis_session, finding.id)
    assert "evidence_rejected" in blocked.eligibility_blockers
    service.transition_finding(
        analysis_session,
        finding.id,
        FindingTransitionRequest(decision="submitted", reviewer="陈晨"),
    )
    with pytest.raises(ReviewBlockedError) as error:
        service.transition_finding(
            analysis_session,
            finding.id,
            FindingTransitionRequest(decision="approved", reviewer="王总"),
        )
    assert error.value.code == "evidence_rejected"

    service.decide_evidence(
        analysis_session,
        finding.id,
        evidence_id,
        EvidenceDecisionRequest(decision="verified", reviewer="陈晨", comment="审批单已归档"),
    )
    with pytest.raises(ReviewBlockedError) as error:
        service.transition_finding(
            analysis_session,
            finding.id,
            FindingTransitionRequest(decision="approved", reviewer="王总"),
        )
    assert error.value.code == "conclusion_incomplete"

    service.save_conclusion(
        analysis_session,
        finding.id,
        ConclusionUpsertRequest(
            verified_facts="低毛利业务占比上升，结构影响为负。",
            analysis_judgment="利润缺口的首要原因是增长结构。",
            open_questions="两家战略客户折扣审批单待归档。",
            recommendation="对快消与运输业务重新定价。",
            editor="陈晨",
        ),
    )
    approved = service.transition_finding(
        analysis_session,
        finding.id,
        FindingTransitionRequest(decision="approved", reviewer="王总", comment="同意签发"),
    )
    assert approved.status == "approved"
    final = service.get_context(analysis_session, finding.id)
    assert final.eligibility_blockers == ()
    assert final.conclusion.exists is True
    decisions = [review.decision for review in final.reviews]
    assert decisions == [
        "evidence_rejected",
        "submitted",
        "evidence_verified",
        "approved",
    ]


def test_evidence_rows_exist_for_top_finding(analysis_session: Session) -> None:
    publish_analysis_run(analysis_session)
    finding = top_finding(analysis_session)
    context = InvestigationService().get_context(analysis_session, finding.id)
    assert all(item.status == "verified" for item in context.evidence)
    rows = analysis_session.scalars(select(Evidence).where(Evidence.finding_id == finding.id))
    assert rows.first() is not None
