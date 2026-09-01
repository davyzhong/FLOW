from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.dashboard.fixture import DASHBOARD_MONTHS, bootstrap_dashboard_demo
from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.service import DashboardService
from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.intake import AnalysisBatch

from .analysis_run_support import (
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
from .intake_service_support import clean


def test_dashboard_demo_bootstrap_is_complete_and_idempotent(
    analysis_session: Session,
) -> None:
    first = bootstrap_dashboard_demo(
        analysis_session,
        repository_root=REPOSITORY_ROOT,
    )
    second = bootstrap_dashboard_demo(
        analysis_session,
        repository_root=REPOSITORY_ROOT,
    )

    assert second == first
    assert len(first.metric_snapshot_ids) == len(DASHBOARD_MONTHS) == 12
    dashboard = DashboardService().get_overview(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
    )
    assert dashboard.state == "ready"
    assert dashboard.context.batch_id == first.batch_id
    assert dashboard.context.metric_snapshot_id == first.metric_snapshot_ids[-1]
    assert dashboard.context.analysis_run_id == first.analysis_run_id


def test_intake_cleanup_removes_published_dashboard_graph() -> None:
    with Session(get_engine(), expire_on_commit=False) as session:
        publication = bootstrap_dashboard_demo(
            session,
            repository_root=REPOSITORY_ROOT,
        )
        session.commit()

        clean(session)

        assert session.scalar(
            select(AnalysisBatch.id).where(
                AnalysisBatch.id == publication.batch_id
            )
        ) is None
