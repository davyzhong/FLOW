from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.dashboard.fixture import DASHBOARD_MONTHS, publish_dashboard_snapshot_series
from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.repositories import DashboardSourceRepository
from flow_api.dashboard.service import DashboardService
from flow_api.infrastructure.models.analytics import MetricSnapshot, MetricValue

from .analysis_run_support import (
    ANALYSIS_POLICY,
    CATALOG,
    REPOSITORY_ROOT,
)
from .analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from .test_metric_source_repository import _publish_reference

ORACLE = Path(REPOSITORY_ROOT) / "fixtures/expected/dashboard_overview_v1.json"


def test_published_snapshot_series_projects_exact_trend_and_partial_degradation(
    analysis_session: Session,
) -> None:
    _, batch, published_import = _publish_reference(analysis_session)
    snapshots = publish_dashboard_snapshot_series(
        analysis_session, batch_id=batch.id, catalog=CATALOG
    )
    retry = publish_dashboard_snapshot_series(
        analysis_session, batch_id=batch.id, catalog=CATALOG
    )
    policy = load_analysis_policy(Path(ANALYSIS_POLICY))
    run = AnalysisRunService().create_run(
        analysis_session,
        snapshot_id=snapshots[-1].id,
        loaded_policy=policy,
    )

    assert tuple(snapshot.id for snapshot in retry) == tuple(
        snapshot.id for snapshot in snapshots
    )
    assert tuple(snapshot.as_of_period.month_key for snapshot in snapshots) == DASHBOARD_MONTHS
    assert all(snapshot.status == "published" for snapshot in snapshots)
    assert all(snapshot.import_version_id == published_import.id for snapshot in snapshots)
    assert len({snapshot.definition_set_hash for snapshot in snapshots}) == 1
    assert len({snapshot.engine_version for snapshot in snapshots}) == 1

    service = DashboardService()
    ready = service.get_trends(analysis_session)
    expected = json.loads(ORACLE.read_text(encoding="utf-8"))["trends"]
    actual = ready.model_dump(mode="json")
    assert actual["coverage_count"] == 12
    assert actual["missing_months"] == []
    for actual_point, expected_point in zip(
        actual["points"], expected["points"], strict=True
    ):
        actual_point.pop("metric_snapshot_id")
        expected_point = dict(expected_point)
        expected_point.pop("metric_snapshot_id")
        assert actual_point == expected_point

    missing_snapshot = snapshots[1]
    analysis_session.execute(
        delete(MetricValue).where(
            MetricValue.metric_snapshot_id == missing_snapshot.id
        )
    )
    analysis_session.execute(
        delete(MetricSnapshot).where(MetricSnapshot.id == missing_snapshot.id)
    )
    analysis_session.flush()

    partial = service.get_trends(analysis_session)
    assert partial.status == "partial_series"
    assert partial.coverage_count == 11
    assert partial.missing_months == ("2025-10",)
    assert all(point.metric_snapshot_id != missing_snapshot.id for point in partial.points)

    core = service.get_core(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
        now=datetime(2026, 9, 1, tzinfo=UTC),
    )
    assert core.context.analysis_run_id == run.id

    source = DashboardSourceRepository().get_latest(analysis_session)
    assert source.snapshot.id == snapshots[-1].id
