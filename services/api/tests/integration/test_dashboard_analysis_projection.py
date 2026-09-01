from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.service import DashboardService

from .analysis_run_support import (
    REPOSITORY_ROOT,
    publish_analysis_run,
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

ORACLE = Path(REPOSITORY_ROOT) / "fixtures/expected/dashboard_overview_v1.json"


def test_analysis_projection_preserves_bridge_finding_rank_evidence_and_handoff(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)
    expected = json.loads(ORACLE.read_text(encoding="utf-8"))
    service = DashboardService()

    projection = service.get_analysis_projection(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
    )

    assert projection.profit_bridge.model_dump(mode="json") == expected["profit_bridge"]
    assert [item.finding_type for item in projection.findings] == [
        "fulfillment_cost_increase",
        "revenue_growth",
        "ar_cash_deterioration",
        "operating_profit_deterioration",
    ]
    for actual, oracle in zip(projection.findings, expected["findings"], strict=True):
        payload = actual.model_dump(mode="json")
        payload.pop("finding_id")
        payload.pop("investigation_path")
        oracle = dict(oracle)
        oracle.pop("finding_id")
        oracle.pop("investigation_path")
        assert payload == oracle
        assert str(actual.finding_id) in actual.investigation_path
        assert f"analysis_run_id={run.id}" in actual.investigation_path
        assert f"metric_snapshot_id={run.metric_snapshot_id}" in actual.investigation_path
        assert "batch_id=" in actual.investigation_path

    assert tuple(item.finding_id for item in projection.highlights) == tuple(
        item.finding_id for item in projection.findings[:3]
    )


def test_dimension_filter_keeps_findings_global_and_does_not_rerank(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    service = DashboardService()
    total = service.get_analysis_projection(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
    )
    core = service.get_core(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
    )
    segment_id = core.filter_options.dimensions[1].options[0].id
    filtered = service.get_analysis_projection(
        analysis_session,
        filters=ActiveFilters(
            period_view="month",
            customer_segment_id=segment_id,
            is_total_scope=False,
        ),
    )

    assert tuple(item.finding_id for item in filtered.findings) == tuple(
        item.finding_id for item in total.findings
    )
    assert all(item.scope == "global" for item in filtered.findings)
