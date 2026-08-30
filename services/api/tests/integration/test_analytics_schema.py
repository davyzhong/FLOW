from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.analytics import (
    Conclusion,
    DriverContribution,
    Evidence,
    Finding,
    MetricDefinition,
    MetricSnapshot,
    MetricValue,
    ReviewEvent,
)
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.infrastructure.models.publishing import (
    PublicationAttempt,
    ReportSnapshot,
    ReportSnapshotItem,
)

ALL_MODELS = (
    PublicationAttempt,
    ReportSnapshotItem,
    ReportSnapshot,
    Conclusion,
    ReviewEvent,
    Evidence,
    DriverContribution,
    Finding,
    MetricValue,
    MetricSnapshot,
    MetricDefinition,
    AnalysisBatch,
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


def analytics_seed(session: Session) -> dict[str, object]:
    suffix = uuid4().hex[:8]
    batch = AnalysisBatch(name=f"Analytics {suffix}", status="published")
    definition = MetricDefinition(
        metric_code=f"revenue_{suffix}",
        version=1,
        name="Revenue",
        business_definition="Recognized operating revenue",
        formula="sum(revenue)",
        aggregation="sum",
        unit="CNY",
    )
    snapshot = MetricSnapshot(batch=batch, version=1, engine_version="flow-metrics/1")
    value = MetricValue(
        metric_snapshot=snapshot,
        metric_definition=definition,
        value=Decimal("100.1234"),
        comparison_type="month",
    )
    finding = Finding(
        metric_snapshot=snapshot,
        metric_definition=definition,
        title="Revenue below budget",
        status="candidate",
        impact_amount=Decimal("-20.5000"),
        confidence=Decimal("0.8500"),
    )
    session.add_all([value, finding])
    session.commit()
    return {
        "batch": batch,
        "definition": definition,
        "snapshot": snapshot,
        "value": value,
        "finding": finding,
    }


def test_report_snapshot_references_one_metric_snapshot(session: Session) -> None:
    seed = analytics_seed(session)
    finding = seed["finding"]
    snapshot = seed["snapshot"]
    report = ReportSnapshot(
        metric_snapshot=snapshot,
        version=1,
        title="August Finance BP Review",
        template_code="finance_bp_monthly",
        items=[
            ReportSnapshotItem(
                position=1,
                object_type="finding",
                object_id=str(finding.id),
            )
        ],
    )
    session.add(report)
    session.commit()

    assert report.metric_snapshot_id == snapshot.id
    assert report.items[0].object_id == str(finding.id)


def test_snapshot_versions_and_metric_values_are_immutable_keys(session: Session) -> None:
    seed = analytics_seed(session)
    assert seed["value"].value == Decimal("100.1234")
    session.add(MetricSnapshot(batch=seed["batch"], version=1, engine_version="other"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_states_driver_order_and_object_types_are_constrained(session: Session) -> None:
    seed = analytics_seed(session)
    finding = seed["finding"]
    session.add_all(
        [
            DriverContribution(
                finding=finding,
                position=1,
                driver_code="volume",
                contribution_amount=Decimal("-10.0000"),
                contribution_ratio=Decimal("0.5000"),
            ),
            DriverContribution(
                finding=finding,
                position=1,
                driver_code="price",
                contribution_amount=Decimal("-10.5000"),
                contribution_ratio=Decimal("0.5000"),
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "insert into evidence "
                "(id, finding_id, status, evidence_type, object_type, object_id) "
                "values (:id, :finding, 'unknown', 'calculation', 'spreadsheet', 'x')"
            ),
            {"id": uuid4(), "finding": finding.id},
        )
        session.commit()


def test_reviews_conclusions_and_publication_attempts_are_versioned(session: Session) -> None:
    seed = analytics_seed(session)
    finding = seed["finding"]
    report = ReportSnapshot(
        metric_snapshot=seed["snapshot"],
        version=1,
        title="Review",
        template_code="finance_bp_monthly",
    )
    review = ReviewEvent(
        finding=finding,
        sequence=1,
        reviewer="finance.bp@example.com",
        decision="approved",
    )
    session.add_all(
        [
            Evidence(
                finding=finding,
                status="verified",
                evidence_type="calculation",
                object_type="metric",
                object_id=str(seed["value"].id),
            ),
            review,
            Conclusion(
                finding=finding,
                verified_facts="Revenue variance confirmed",
                analysis_judgment="Primarily volume-driven",
                open_questions="Customer forecast timing",
                recommendation="Validate pipeline recovery",
            ),
            report,
        ]
    )
    session.commit()
    review.comment = "history must not be rewritten"
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
    session.rollback()

    session.add_all(
        [
            PublicationAttempt(report_snapshot=report, sequence=1, format="pptx", status="failed"),
            PublicationAttempt(
                report_snapshot=report, sequence=2, format="pptx", status="succeeded"
            ),
        ]
    )
    session.commit()

    assert len(report.publication_attempts) == 2
