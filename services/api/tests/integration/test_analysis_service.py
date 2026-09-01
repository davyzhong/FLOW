from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.infrastructure.models.analytics import (
    AnalysisResult,
    AnalysisRun,
    Evidence,
    Finding,
    FindingScoreComponent,
)

from .analysis_run_support import ANALYSIS_POLICY, analysis_session_fixture, publish_snapshot
from .analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)

_analysis_session_fixture = analysis_session_fixture


def test_service_publishes_five_results_findings_and_verified_evidence(
    analysis_session: Session,
) -> None:
    snapshot = publish_snapshot(analysis_session)
    policy = load_analysis_policy(Path(ANALYSIS_POLICY))
    service = AnalysisRunService()

    run = service.create_run(
        analysis_session, snapshot_id=snapshot.id, loaded_policy=policy
    )
    retry = service.create_run(
        analysis_session, snapshot_id=snapshot.id, loaded_policy=policy
    )

    assert run.id == retry.id
    assert run.status == "published"
    assert run.import_version_id == snapshot.import_version_id
    results = tuple(
        analysis_session.scalars(
            select(AnalysisResult)
            .where(AnalysisResult.analysis_run_id == run.id)
            .order_by(AnalysisResult.playbook_code)
        )
    )
    assert {result.playbook_code for result in results} == {
        "revenue_vpm",
        "fulfillment_cost_rve",
        "gross_profit_bridge",
        "operating_profit_bridge",
        "ar_cash_impact",
    }
    assert all(result.status == "complete" for result in results)
    assert all(
        abs(result.reconciliation_difference) <= result.reconciliation_tolerance
        for result in results
    )

    findings = tuple(
        analysis_session.scalars(
            select(Finding)
            .where(Finding.analysis_run_id == run.id)
            .order_by(Finding.total_score.desc(), func.abs(Finding.impact_amount).desc())
        )
    )
    assert {finding.finding_type for finding in findings} >= {
        "revenue_growth",
        "fulfillment_cost_increase",
        "operating_profit_deterioration",
        "ar_cash_deterioration",
    }
    assert all(finding.status == "candidate" for finding in findings)
    assert all(finding.confidence == 1 for finding in findings)
    assert all(len(finding.score_components) == 4 for finding in findings)
    assert all(len(finding.fingerprint or "") == 64 for finding in findings)
    assert (
        analysis_session.scalar(
            select(func.count()).select_from(FindingScoreComponent)
        )
        == len(findings) * 4
    )
    assert (
        analysis_session.scalar(select(func.count()).select_from(Evidence))
        == len(findings) * 5
    )
    assert all(
        status == "verified"
        for status in analysis_session.scalars(select(Evidence.status))
    )
    assert analysis_session.scalar(select(func.count()).select_from(AnalysisRun)) == 1
