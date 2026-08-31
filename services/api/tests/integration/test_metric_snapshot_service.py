from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    MetricDefinition,
    MetricDefinitionDependency,
    MetricSnapshot,
    MetricValue,
)
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import (
    MetricDefinitionConflictError,
    MetricSnapshotService,
)

from .metric_snapshot_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .metric_snapshot_support import metric_session_fixture as _metric_session_fixture  # noqa: F401
from .test_metric_source_repository import _publish_reference

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")


def test_service_publishes_complete_snapshot_and_retry_is_idempotent(
    metric_session: Session,
) -> None:
    _, batch, published_import = _publish_reference(metric_session)
    service = MetricSnapshotService()

    first = service.create_snapshot(
        metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )
    second = service.create_snapshot(
        metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )
    values = service.get_snapshot_values(metric_session, first.id)

    assert first.id == second.id
    assert first.status == "published"
    assert first.import_version_id == published_import.id
    assert first.version == 1
    assert len(values) > 15
    assert values == tuple(
        sorted(
            values,
            key=lambda value: (
                value.metric_definition.metric_code,
                value.comparison_type,
                str(value.period_id),
                str(value.organization_id or ""),
                str(value.customer_id or ""),
                str(value.customer_segment_id or ""),
                str(value.logistics_product_id or ""),
                str(value.region_id or ""),
            ),
        )
    )
    assert metric_session.scalar(select(func.count()).select_from(MetricSnapshot)) == 1
    assert metric_session.scalar(select(func.count()).select_from(MetricDefinition)) == 15
    assert metric_session.scalar(
        select(func.count()).select_from(MetricDefinitionDependency)
    ) == sum(len(metric.dependencies) for metric in CATALOG.metrics)
    assert all(value.exact_value for value in values)
    assert all("source_fact_count" in value.calculation_trace for value in values)


def test_service_rejects_conflicting_content_for_stable_definition_identity(
    metric_session: Session,
) -> None:
    _, batch, _ = _publish_reference(metric_session)
    metric_session.add(
        MetricDefinition(
            metric_code="revenue",
            version=1,
            name="Conflicting revenue",
            business_definition="wrong",
            formula="wrong",
            aggregation="sum",
            unit="CNY",
            definition_config={},
        )
    )
    metric_session.commit()

    with pytest.raises(MetricDefinitionConflictError):
        MetricSnapshotService().create_snapshot(
            metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
        )

    assert metric_session.scalar(select(func.count()).select_from(MetricSnapshot)) == 0
    assert metric_session.scalar(select(func.count()).select_from(MetricValue)) == 0


def test_engine_identity_change_creates_new_snapshot_version(
    metric_session: Session,
) -> None:
    _, batch, _ = _publish_reference(metric_session)
    service = MetricSnapshotService()
    first = service.create_snapshot(
        metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )
    upgraded_catalog = CATALOG.model_copy(
        update={"engine_version": "flow.metrics.engine.v2"}
    )

    second = service.create_snapshot(
        metric_session,
        batch_id=batch.id,
        as_of_month=202608,
        catalog=upgraded_catalog,
    )
    retry = service.create_snapshot(
        metric_session,
        batch_id=batch.id,
        as_of_month=202608,
        catalog=upgraded_catalog,
    )

    assert second.id != first.id
    assert second.version == 2
    assert second.engine_version == "flow.metrics.engine.v2"
    assert retry.id == second.id
    assert first.status == "published"
    assert metric_session.scalar(select(func.count()).select_from(MetricSnapshot)) == 2
