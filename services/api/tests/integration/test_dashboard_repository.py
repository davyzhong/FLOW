from __future__ import annotations

import re
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from flow_api.dashboard.repositories import (
    DashboardSourceRepository,
    DashboardSourceUnavailableError,
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
from .analysis_run_support import publish_analysis_run


def test_repository_loads_the_published_dashboard_bundle(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)

    bundle = DashboardSourceRepository().get_latest(analysis_session)

    assert bundle.run.id == run.id
    assert bundle.run.status == "published"
    assert bundle.snapshot.id == run.metric_snapshot_id
    assert bundle.snapshot.status == "published"
    assert bundle.import_version.id == run.import_version_id
    assert bundle.import_version.status == "published"
    assert bundle.batch.id == bundle.snapshot.batch_id
    assert bundle.as_of_period.month_key == 202608
    assert len(bundle.metric_values) > 15
    assert [result.playbook_code for result in bundle.analysis_results] == sorted(
        result.playbook_code for result in bundle.analysis_results
    )
    assert all(
        [driver.position for driver in result.drivers]
        == sorted(driver.position for driver in result.drivers)
        for result in bundle.analysis_results
    )
    assert len(bundle.findings) >= 4
    assert bundle.dimension_options.organizations
    assert bundle.dimension_options.customer_segments
    assert bundle.dimension_options.logistics_products
    assert bundle.dimension_options.regions
    assert bundle.quality.blocking_issue_count == 0
    assert bundle.quality.reconciliation_status == "passed"

    bundle.snapshot.import_version_id = uuid4()
    with pytest.raises(DashboardSourceUnavailableError) as mismatch:
        DashboardSourceRepository().get_by_run_id(analysis_session, run.id)
    assert mismatch.value.code == "run_import_mismatch"


def test_repository_rejects_missing_run(analysis_session: Session) -> None:
    with pytest.raises(DashboardSourceUnavailableError) as unavailable:
        DashboardSourceRepository().get_latest(analysis_session)
    assert unavailable.value.code == "no_published_run"

    with pytest.raises(DashboardSourceUnavailableError) as missing:
        DashboardSourceRepository().get_by_run_id(analysis_session, uuid4())

    assert missing.value.code == "run_not_found"


def test_repository_query_boundary_excludes_raw_and_canonical_facts(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    statements: list[str] = []
    engine = analysis_session.get_bind()

    def capture(
        _connection: object,
        _cursor: object,
        statement: str,
        _parameters: object,
        _context: object,
        _executemany: object,
    ) -> None:
        statements.append(statement.lower())

    event.listen(engine, "before_cursor_execute", capture)
    try:
        DashboardSourceRepository().get_latest(analysis_session)
    finally:
        event.remove(engine, "before_cursor_execute", capture)

    sql = "\n".join(statements)
    assert statements
    for forbidden_table in (
        "stored_object",
        "source_file",
        "source_record",
        "fact_operating_actual",
        "fact_financial_actual",
        "fact_budget",
        "fact_ar_collection",
    ):
        assert re.search(
            rf'\b(?:from|join)\s+"?{re.escape(forbidden_table)}"?\b', sql
        ) is None
