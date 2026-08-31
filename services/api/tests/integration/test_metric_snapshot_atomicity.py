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
from flow_api.infrastructure.models.intake import QualityIssue
from flow_api.intake.service import IntakeService
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotBlockedError, MetricSnapshotService

from .intake_service_support import STANDARD, intake_inputs
from .metric_snapshot_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .metric_snapshot_support import metric_session_fixture as _metric_session_fixture  # noqa: F401
from .test_metric_source_repository import _publish_reference

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")


def test_mid_write_failure_leaves_no_snapshot_or_values(metric_session: Session) -> None:
    _, batch, _ = _publish_reference(metric_session)

    def fail_after_values() -> None:
        raise RuntimeError("injected metric write failure")

    with pytest.raises(RuntimeError, match="injected"):
        MetricSnapshotService().create_snapshot(
            metric_session,
            batch_id=batch.id,
            as_of_month=202608,
            catalog=CATALOG,
            failure_hook=fail_after_values,
        )

    assert metric_session.scalar(select(func.count()).select_from(MetricSnapshot)) == 0
    assert metric_session.scalar(select(func.count()).select_from(MetricValue)) == 0
    assert metric_session.scalar(select(func.count()).select_from(MetricDefinition)) == 0
    assert (
        metric_session.scalar(
            select(func.count()).select_from(MetricDefinitionDependency)
        )
        == 0
    )


def test_corrected_published_import_creates_new_version_without_mutating_old(
    metric_session: Session,
) -> None:
    intake, batch, first_import = _publish_reference(metric_session)
    service = MetricSnapshotService()
    first = service.create_snapshot(
        metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )
    first_values = tuple(
        (value.id, value.exact_value)
        for value in service.get_snapshot_values(metric_session, first.id)
    )

    stored, proposal, candidate, report = intake_inputs(STANDARD)
    source = intake.attach_source(batch.id, stored)
    mapping = intake.propose_mapping(source.id, proposal)
    correction = intake.create_correction(source.id, mapping.id, candidate, report)
    for issue in metric_session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == correction.id,
            QualityIssue.severity == "warning",
        )
    ):
        intake.acknowledge_warning(issue.id, actor="finance.bp", reason="verified")
    intake.publish_import(correction.id)
    metric_session.flush()

    second = service.create_snapshot(
        metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )

    assert first.import_version_id == first_import.id
    assert second.import_version_id == correction.id
    assert second.id != first.id
    assert second.version == 2
    assert first.status == "published"
    assert tuple(
        (value.id, value.exact_value)
        for value in service.get_snapshot_values(metric_session, first.id)
    ) == first_values


def test_ineligible_batch_is_reported_as_typed_snapshot_blocker(
    metric_session: Session,
) -> None:
    batch = IntakeService(metric_session).create_batch("No published import")
    with pytest.raises(MetricSnapshotBlockedError) as blocked:
        MetricSnapshotService().create_snapshot(
            metric_session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
        )
    assert blocked.value.reasons == ("no_published_import",)
