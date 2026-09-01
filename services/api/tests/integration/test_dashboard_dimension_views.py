from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

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


def _without_ids(payload: dict[str, object], *fields: str) -> dict[str, object]:
    result = dict(payload)
    for field in fields:
        result.pop(field)
    return result


def test_dimension_views_use_exact_product_and_segment_product_metric_grains(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    expected = json.loads(ORACLE.read_text(encoding="utf-8"))

    views = DashboardService().get_dimension_views(analysis_session)

    assert views.product_table.status == "complete"
    assert views.product_table.comparison_label == "同比"
    assert len(views.product_table.rows) == 8
    for actual, oracle in zip(
        views.product_table.rows, expected["product_table"]["rows"], strict=True
    ):
        assert _without_ids(
            actual.model_dump(mode="json"), "logistics_product_id"
        ) == _without_ids(oracle, "logistics_product_id")

    matrix = views.margin_matrix
    assert matrix.status == "complete"
    assert matrix.comparison_label == "同比"
    assert [item.code for item in matrix.rows] == ["KEY_ACCOUNT", "DOMESTIC"]
    assert [item.code for item in matrix.columns] == [
        "B2C",
        "B2B",
        "WAREHOUSE",
        "CROSS_BORDER",
        "COLD_CHAIN",
        "REVERSE",
        "M2C",
        "SAME_DAY",
    ]
    assert len(matrix.cells) == 16
    for actual, oracle in zip(matrix.cells, expected["margin_matrix"]["cells"], strict=True):
        assert _without_ids(
            actual.model_dump(mode="json"),
            "customer_segment_id",
            "logistics_product_id",
        ) == _without_ids(
            oracle,
            "customer_segment_id",
            "logistics_product_id",
        )


def test_dimension_views_do_not_allocate_organization_budget_or_profit(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    views = DashboardService().get_dimension_views(analysis_session)

    assert views.product_table.comparison_label == "同比"
    assert views.margin_matrix.comparison_label == "同比"
    assert all(
        row.revenue_comparison.status == "available"
        and row.gross_margin_comparison.status == "available"
        for row in views.product_table.rows
    )
    assert all(cell.comparison.status == "available" for cell in views.margin_matrix.cells)
    assert not any(
        "operating_profit" in field
        for field in views.product_table.rows[0].model_fields_set
    )
