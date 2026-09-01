import json
from dataclasses import replace
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.repositories import AnalysisSourceRepository
from flow_api.analysis.service import AnalysisRunService, calculate_analysis_results
from flow_api.infrastructure.models.analytics import (
    AnalysisDriver,
    AnalysisResult,
    Finding,
)

from .analysis_run_support import ANALYSIS_POLICY, analysis_session_fixture, publish_snapshot
from .analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)

_analysis_session_fixture = analysis_session_fixture
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
ORACLE = json.loads(
    (REPOSITORY_ROOT / "fixtures/expected/analysis_results_v1.json").read_text(
        encoding="utf-8"
    )
)


def test_published_run_matches_frozen_analysis_oracle(analysis_session: Session) -> None:
    snapshot = publish_snapshot(analysis_session)
    run = AnalysisRunService().create_run(
        analysis_session,
        snapshot_id=snapshot.id,
        loaded_policy=load_analysis_policy(Path(ANALYSIS_POLICY)),
    )
    results = tuple(
        analysis_session.scalars(
            select(AnalysisResult).where(AnalysisResult.analysis_run_id == run.id)
        )
    )

    for result in results:
        expected = ORACLE["results"][result.playbook_code]
        drivers = tuple(
            analysis_session.scalars(
                select(AnalysisDriver)
                .where(AnalysisDriver.analysis_result_id == result.id)
                .order_by(AnalysisDriver.position)
            )
        )
        assert result.status == expected["status"]
        assert str(result.impact_amount) == expected["impact_amount"]
        assert [
            {"code": driver.driver_code, "amount": str(driver.contribution_amount)}
            for driver in drivers
        ] == expected["drivers"]
        assert abs(result.reconciliation_difference) <= result.reconciliation_tolerance

    findings = tuple(
        analysis_session.scalars(
            select(Finding)
            .where(Finding.analysis_run_id == run.id)
            .order_by(
                Finding.total_score.desc(),
                func.abs(Finding.impact_amount).desc(),
                Finding.fingerprint,
            )
        )
    )
    assert [finding.finding_type for finding in findings] == ORACLE["finding_rank"]
    assert [str(finding.total_score) for finding in findings] == ORACLE["finding_scores"]


def test_removed_mix_and_aging_fields_degrade_without_findings(
    analysis_session: Session,
) -> None:
    snapshot = publish_snapshot(analysis_session)
    bundle = AnalysisSourceRepository().get_bound_source(analysis_session, snapshot.id)
    product_id = bundle.operating_rows[0].logistics_product_id
    comparison_start = bundle.source.comparison_start_month
    comparison_end = bundle.source.comparison_end_month
    without_comparison_product = replace(
        bundle,
        operating_rows=tuple(
            row
            for row in bundle.operating_rows
            if not (
                comparison_start <= row.month_key <= comparison_end
                and row.logistics_product_id == product_id
            )
        ),
    )
    tolerance = load_analysis_policy(
        Path(ANALYSIS_POLICY)
    ).policy.reconciliation_tolerance
    degraded_mix = calculate_analysis_results(
        without_comparison_product, tolerance=tolerance
    )
    by_code = {result.playbook_code: result for result in degraded_mix}
    assert by_code["revenue_vpm"].degradation_code == "unmatched_mix_cell"
    assert by_code["gross_profit_bridge"].degradation_code == "upstream_result_degraded"
    assert by_code["operating_profit_bridge"].degradation_code == "upstream_result_degraded"
    assert all(not result.drivers for result in degraded_mix if result.status == "degraded")

    end_months = {bundle.source.analysis_end_month, bundle.source.comparison_end_month}
    without_aging = replace(
        bundle,
        ar_rows=tuple(
            replace(row, aging_bucket=None) if row.month_key in end_months else row
            for row in bundle.ar_rows
        ),
    )
    degraded_ar = calculate_analysis_results(
        without_aging, tolerance=tolerance
    )
    ar_result = next(
        result for result in degraded_ar if result.playbook_code == "ar_cash_impact"
    )
    assert ar_result.status == "degraded"
    assert ar_result.degradation_code == "missing_required_field"
    assert ar_result.drivers == ()
