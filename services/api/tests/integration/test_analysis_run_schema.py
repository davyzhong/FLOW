from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.analytics import (
    AnalysisDriver,
    AnalysisResult,
    AnalysisRun,
    Evidence,
    Finding,
    FindingScoreComponent,
    MetricSnapshot,
)
from flow_api.infrastructure.models.canonical import Period
from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion

ALL_MODELS = (
    Evidence,
    FindingScoreComponent,
    Finding,
    AnalysisDriver,
    AnalysisResult,
    AnalysisRun,
    MetricSnapshot,
    ImportVersion,
    AnalysisBatch,
    Period,
)


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        yield database_session
        database_session.rollback()
        for model in ALL_MODELS:
            database_session.execute(delete(model))
        database_session.commit()


def _snapshot(session: Session) -> MetricSnapshot:
    suffix = uuid4().hex[:8]
    batch = AnalysisBatch(name=f"Analysis run {suffix}", status="published")
    import_version = ImportVersion(
        batch=batch,
        sequence=1,
        status="published",
        is_published=True,
        summary={},
    )
    period = Period(month_key=202608, year=2026, quarter=3, month=8)
    snapshot = MetricSnapshot(
        batch=batch,
        import_version=import_version,
        as_of_period=period,
        version=1,
        engine_version="flow-metrics/1",
        definition_set_id="flow.metrics.test.v1",
        definition_set_hash="a" * 64,
        fingerprint="b" * 64,
        status="published",
    )
    session.add(snapshot)
    session.flush()
    return snapshot


def _run(session: Session) -> AnalysisRun:
    snapshot = _snapshot(session)
    run = AnalysisRun(
        metric_snapshot=snapshot,
        import_version_id=snapshot.import_version_id,
        policy_id="flow.analysis.test.v1",
        policy_set_hash="c" * 64,
        engine_version="flow-analysis/1",
        fingerprint="d" * 64,
        status="building",
    )
    session.add(run)
    session.flush()
    return run


def _result(run: AnalysisRun, code: str = "revenue_vpm") -> AnalysisResult:
    return AnalysisResult(
        analysis_run=run,
        playbook_code=code,
        playbook_version=1,
        status="complete",
        comparison_basis="prior_year",
        impact_amount=Decimal("-20.0000"),
        unit="CNY",
        reconciliation_difference=Decimal("0.0000"),
        reconciliation_tolerance=Decimal("0.0100"),
        required_fields=["revenue"],
        available_fields=["revenue"],
        missing_fields=[],
        source_record_count=2,
        calculation_trace={"formula": "test"},
    )


def test_analysis_run_persists_results_drivers_findings_scores_and_evidence(
    session: Session,
) -> None:
    run = _run(session)
    result = _result(run)
    driver = AnalysisDriver(
        analysis_result=result,
        position=1,
        driver_code="volume",
        calculation_method="test",
        contribution_amount=Decimal("-20.0000"),
        contribution_ratio=Decimal("1.000000"),
        calculation_trace={"exact": "-20"},
    )
    finding = Finding(
        metric_snapshot_id=run.metric_snapshot_id,
        analysis_run=run,
        analysis_result=result,
        finding_type="revenue_growth",
        title="Revenue change",
        status="candidate",
        fact_statement="Revenue changed by -20",
        comparison_basis="prior_year",
        impact_amount=Decimal("-20.0000"),
        confidence=Decimal("1.0000"),
        business_meaning="Scale changed",
        total_score=Decimal("80.000000"),
        policy_version="flow.analysis.test.v1",
        fingerprint="e" * 64,
        qualification_trace={"passed": True},
    )
    score = FindingScoreComponent(
        finding=finding,
        component_code="materiality",
        raw_value=Decimal("20.000000"),
        normalized_score=Decimal("20.000000"),
        weight=Decimal("0.400000"),
        weighted_score=Decimal("8.000000"),
        calculation_trace={"high": "100"},
    )
    evidence = Evidence(
        finding=finding,
        status="verified",
        evidence_type="invariant",
        object_type="invariant",
        object_id="analysis-result:test",
        evidence_digest="f" * 64,
        verification_trace={"verified": True},
    )
    session.add_all([driver, finding, score, evidence])
    run.status = "published"
    session.commit()

    assert run.results[0].drivers[0].contribution_ratio == Decimal("1.000000")
    assert finding.score_components[0].weighted_score == Decimal("8.000000")
    assert evidence.verification_trace == {"verified": True}


def test_run_result_driver_and_score_constraints_are_enforced(session: Session) -> None:
    run = _run(session)
    session.add_all([_result(run), _result(run)])
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    run = _run(session)
    result = _result(run)
    session.add_all(
        [
            AnalysisDriver(
                analysis_result=result,
                position=1,
                driver_code="volume",
                contribution_amount=Decimal("-10"),
            ),
            AnalysisDriver(
                analysis_result=result,
                position=1,
                driver_code="price",
                contribution_amount=Decimal("-10"),
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_published_run_results_drivers_and_scores_are_append_only(session: Session) -> None:
    run = _run(session)
    result = _result(run)
    driver = AnalysisDriver(
        analysis_result=result,
        position=1,
        driver_code="volume",
        contribution_amount=Decimal("-20"),
    )
    finding = Finding(
        metric_snapshot_id=run.metric_snapshot_id,
        analysis_run=run,
        analysis_result=result,
        finding_type="revenue_growth",
        title="Revenue",
        status="candidate",
        fact_statement="Revenue changed",
        comparison_basis="prior_year",
        impact_amount=Decimal("-20"),
        confidence=Decimal("1"),
        total_score=Decimal("80"),
        policy_version="test",
        fingerprint="e" * 64,
        qualification_trace={},
    )
    score = FindingScoreComponent(
        finding=finding,
        component_code="materiality",
        raw_value=Decimal("20"),
        normalized_score=Decimal("20"),
        weight=Decimal("0.4"),
        weighted_score=Decimal("8"),
        calculation_trace={},
    )
    session.add_all([driver, finding, score])
    run.status = "published"
    session.commit()

    result.impact_amount = Decimal("-19")
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
    session.rollback()

    session.delete(driver)
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
    session.rollback()

    score.weight = Decimal("0.5")
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
