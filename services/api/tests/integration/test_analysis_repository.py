from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from flow_api.analysis.repositories import (
    AnalysisSourceRepository,
    AnalysisSourceUnavailableError,
)
from flow_api.infrastructure.models.analytics import MetricSnapshot

from .analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from .analysis_run_support import publish_snapshot


def test_repository_reads_only_snapshot_bound_published_source(
    analysis_session: Session,
) -> None:
    snapshot = publish_snapshot(analysis_session)
    bundle = AnalysisSourceRepository().get_bound_source(analysis_session, snapshot.id)

    assert bundle.snapshot_id == snapshot.id
    assert bundle.import_version_id == snapshot.import_version_id
    assert len(bundle.operating_rows) == 3072
    assert len(bundle.financial_rows) == 432
    assert len(bundle.ar_rows) == 1920
    assert len(bundle.metric_values) > 15
    assert len(bundle.source_digests) == 3
    assert all(len(digest) == 64 for digest in bundle.source_digests.values())
    assert bundle.operating_rows == tuple(
        sorted(bundle.operating_rows, key=lambda row: (row.month_key, row.fact_id))
    )


def test_repository_rejects_missing_and_unpublished_snapshot(
    analysis_session: Session,
) -> None:
    repository = AnalysisSourceRepository()
    with pytest.raises(AnalysisSourceUnavailableError) as missing:
        repository.get_bound_source(analysis_session, uuid4())
    assert missing.value.code == "snapshot_not_found"

    published = publish_snapshot(analysis_session)
    building = MetricSnapshot(
        batch_id=published.batch_id,
        import_version_id=published.import_version_id,
        as_of_period_id=published.as_of_period_id,
        version=2,
        engine_version="flow-metrics/test",
        definition_set_id="flow.metrics.test",
        definition_set_hash="c" * 64,
        fingerprint="d" * 64,
        status="building",
    )
    analysis_session.add(building)
    analysis_session.flush()

    with pytest.raises(AnalysisSourceUnavailableError) as unpublished:
        repository.get_bound_source(analysis_session, building.id)
    assert unpublished.value.code == "snapshot_not_published"
