from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricDefinitionDependency,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.canonical import Period
from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        yield database_session
        database_session.rollback()
        for model in (
            MetricValue,
            MetricDefinitionDependency,
            MetricSnapshot,
            MetricDefinition,
            ImportVersion,
            AnalysisBatch,
            Period,
        ):
            database_session.execute(delete(model))
        database_session.commit()


def _seed(session: Session):
    suffix = uuid4().hex[:8]
    batch = AnalysisBatch(name=f"Metric snapshot {suffix}", status="published")
    import_version = ImportVersion(
        batch=batch,
        sequence=1,
        status="published",
        is_published=True,
        summary={},
    )
    period = Period(month_key=202608, year=2026, quarter=3, month=8)
    revenue = MetricDefinition(
        metric_code=f"revenue_{suffix}",
        version=1,
        name="Revenue",
        business_definition="Revenue",
        formula="sum",
        aggregation="sum",
        unit="CNY",
    )
    margin = MetricDefinition(
        metric_code=f"margin_{suffix}",
        version=1,
        name="Margin",
        business_definition="Margin",
        formula="ratio",
        aggregation="ratio",
        unit="ratio",
    )
    dependency = MetricDefinitionDependency(
        metric_definition=margin,
        dependency_definition=revenue,
        position=1,
    )
    snapshot = MetricSnapshot(
        batch=batch,
        import_version=import_version,
        as_of_period=period,
        version=1,
        engine_version="flow.metrics.engine.v1",
        definition_set_id="flow.metrics.logistics.v1",
        definition_set_hash="a" * 64,
        fingerprint="b" * 64,
        status="published",
    )
    value = MetricValue(
        metric_snapshot=snapshot,
        metric_definition=revenue,
        comparison_type="actual_ytd",
        period_id=period.id,
        value=Decimal("100.1235"),
        exact_value="100.123456",
        calculation_trace={"dependencies": [], "source_fact_count": 8},
    )
    session.add_all([dependency, value])
    session.commit()
    return dependency, snapshot, value


def test_schema_has_snapshot_identity_dependency_and_trace_columns() -> None:
    inspector = inspect(get_engine())
    assert "metric_definition_dependency" in inspector.get_table_names()
    snapshot_columns = {column["name"] for column in inspector.get_columns("metric_snapshot")}
    assert {
        "import_version_id",
        "as_of_period_id",
        "definition_set_id",
        "definition_set_hash",
        "fingerprint",
        "status",
    } <= snapshot_columns
    value_columns = {column["name"] for column in inspector.get_columns("metric_value")}
    assert {"exact_value", "calculation_trace"} <= value_columns


def test_snapshot_identity_hash_status_and_dependency_order_are_constrained(
    session: Session,
) -> None:
    _, snapshot, _ = _seed(session)
    duplicate = MetricSnapshot(
        batch_id=snapshot.batch_id,
        import_version_id=snapshot.import_version_id,
        as_of_period_id=snapshot.as_of_period_id,
        version=snapshot.version,
        engine_version="different",
        definition_set_id="different",
        definition_set_hash="c" * 64,
        fingerprint="d" * 64,
        status="building",
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    other_batch = AnalysisBatch(name="Wrong metric batch", status="published")
    other_import = ImportVersion(
        batch=other_batch,
        sequence=1,
        status="published",
        is_published=True,
        summary={},
    )
    session.add(other_import)
    session.commit()
    session.add(
        MetricSnapshot(
            batch_id=snapshot.batch_id,
            import_version_id=other_import.id,
            as_of_period_id=snapshot.as_of_period_id,
            version=2,
            engine_version="x",
            definition_set_id="x",
            definition_set_hash="c" * 64,
            fingerprint="d" * 64,
            status="building",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "insert into metric_snapshot "
                "(id, batch_id, import_version_id, as_of_period_id, version, engine_version, "
                "definition_set_id, definition_set_hash, fingerprint, status) values "
                "(:id, :batch, :import_version, :period, 2, 'x', 'x', 'short', :fingerprint, 'bad')"
            ),
            {
                "id": uuid4(),
                "batch": snapshot.batch_id,
                "import_version": snapshot.import_version_id,
                "period": snapshot.as_of_period_id,
                "fingerprint": "f" * 64,
            },
        )
        session.commit()


def test_published_snapshot_values_and_dependencies_are_append_only(
    session: Session,
) -> None:
    dependency, snapshot, value = _seed(session)
    snapshot.engine_version = "rewritten"
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
    session.rollback()

    value.exact_value = "999"
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
    session.rollback()

    dependency.position = 2
    with pytest.raises(ValueError, match="append-only"):
        session.flush()
    session.rollback()

    for item in (value, snapshot, dependency):
        session.delete(item)
        with pytest.raises(ValueError, match="append-only"):
            session.flush()
        session.rollback()
