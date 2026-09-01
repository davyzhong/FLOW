from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from integration.analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from integration.intake_service_support import (
    intake_session_fixture as intake_session_fixture,  # noqa: F401
)
from integration.metric_snapshot_support import (
    metric_session_fixture as metric_session_fixture,  # noqa: F401
)
from integration.test_metric_source_repository import _publish_reference
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.copilot.service import CopilotService  # noqa: F401
from flow_api.infrastructure.models.analytics import (
    AnalysisRun,
    Finding,
)
from flow_api.infrastructure.models.copilot import CopilotInteraction
from flow_api.infrastructure.models.publishing import (
    PublicationAttempt,
    ReportSnapshot,
    ReportSnapshotItem,
)
from flow_api.investigation.state_machines import apply_finding_decision
from flow_api.metrics.catalog import load_metric_catalog

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")
ANALYSIS_POLICY = REPOSITORY_ROOT / "services/api/config/analysis/flow-logistics-v1.yaml"

PUBLISHING_MODELS = (
    CopilotInteraction,
    PublicationAttempt,
    ReportSnapshotItem,
    ReportSnapshot,
)


@pytest.fixture(name="publishing_session")
def publishing_session_fixture(analysis_session: Session) -> Iterator[Session]:
    yield analysis_session
    analysis_session.rollback()
    for model in PUBLISHING_MODELS:
        for instance in analysis_session.scalars(select(model)):
            analysis_session.delete(instance)
    analysis_session.commit()


def publish_snapshot(session: Session):
    _, batch, _ = _publish_reference(session)
    from flow_api.metrics.service import MetricSnapshotService

    return MetricSnapshotService().create_snapshot(
        session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )


def publish_analysis_run(session: Session) -> AnalysisRun:
    snapshot = publish_snapshot(session)
    policy = load_analysis_policy(Path(ANALYSIS_POLICY))
    return AnalysisRunService().create_run(
        session, snapshot_id=snapshot.id, loaded_policy=policy
    )


def approve_top_findings(session: Session, count: int = 1, run_id=None) -> None:
    from flow_api.infrastructure.models.analytics import Conclusion, Evidence

    query = select(Finding).order_by(Finding.total_score.desc())
    if run_id is not None:
        query = query.where(Finding.analysis_run_id == run_id)
    findings = session.scalars(query).all()
    assert findings, "analysis run produced no findings"
    for finding in findings[:count]:
        evidence = session.scalars(
            select(Evidence).where(Evidence.finding_id == finding.id)
        ).all()
        assert evidence and all(item.status == "verified" for item in evidence)
        session.add(
            Conclusion(
                finding=finding,
                verified_facts="已验证事实：低毛利业务占比上升，履约成本上涨。",
                analysis_judgment="判断：成本上升为最大驱动，规模仍有贡献。",
                open_questions="待确认：两家承运商报价审批单。",
                recommendation="建议：对 Top 3 承运商重新议价。",
            )
        )
        session.flush()
        apply_finding_decision(session, finding, "submitted", reviewer="陈晨", comment=None)
        apply_finding_decision(session, finding, "approved", reviewer="王总", comment=None)
    session.commit()


def fresh_approved_report(session: Session):
    """Run the whole governed pipeline on a fresh batch and freeze a report."""
    from flow_api.publishing.service import freeze_report_snapshot

    run = publish_analysis_run(session)
    session.commit()
    approve_top_findings(session, count=1, run_id=run.id)
    snapshot_id = session.scalar(
        select(Finding.metric_snapshot_id)
        .where(Finding.analysis_run_id == run.id)
        .limit(1)
    )
    assert snapshot_id is not None
    report, view = freeze_report_snapshot(session, metric_snapshot_id=snapshot_id)
    session.commit()
    return report, view
