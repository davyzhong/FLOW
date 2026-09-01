from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.infrastructure.models.analytics import (
    AnalysisDriver,
    AnalysisResult,
    AnalysisRun,
    DriverContribution,
    Evidence,
    Finding,
    FindingScoreComponent,
)
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotService

from .intake_service_support import intake_session_fixture
from .metric_snapshot_support import metric_session_fixture
from .test_metric_source_repository import _publish_reference

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")
ANALYSIS_POLICY = REPOSITORY_ROOT / "services/api/config/analysis/flow-logistics-v1.yaml"


@pytest.fixture(name="analysis_session")
def analysis_session_fixture(metric_session: Session) -> Iterator[Session]:
    yield metric_session
    metric_session.rollback()
    for model in (
        Evidence,
        FindingScoreComponent,
        DriverContribution,
        Finding,
        AnalysisDriver,
        AnalysisResult,
        AnalysisRun,
    ):
        metric_session.execute(delete(model))
    metric_session.commit()


def publish_snapshot(session: Session):
    _, batch, _ = _publish_reference(session)
    return MetricSnapshotService().create_snapshot(
        session, batch_id=batch.id, as_of_month=202608, catalog=CATALOG
    )


def publish_analysis_run(session: Session) -> AnalysisRun:
    snapshot = publish_snapshot(session)
    policy = load_analysis_policy(Path(ANALYSIS_POLICY))
    return AnalysisRunService().create_run(
        session, snapshot_id=snapshot.id, loaded_policy=policy
    )


_metric_session_fixture = metric_session_fixture
_intake_session_fixture = intake_session_fixture
