from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.repositories import DashboardSourceRepository
from flow_api.dashboard.service import DashboardService
from flow_api.infrastructure.models.canonical import CustomerSegment, LogisticsProduct

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


def test_dimension_views_exclude_catalog_dimensions_without_current_snapshot_facts(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    analysis_session.add_all(
        [
            LogisticsProduct(code="NO_FACT_PRODUCT", name="无本批次事实产品"),
            CustomerSegment(code="NO_FACT_SEGMENT", name="无本批次事实客群"),
        ]
    )
    analysis_session.commit()

    overview = DashboardService().get_overview(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
    )

    product_dimension = next(
        item for item in overview.filter_options.dimensions
        if item.dimension == "logistics_product"
    )
    segment_dimension = next(
        item for item in overview.filter_options.dimensions
        if item.dimension == "customer_segment"
    )
    assert any(item.code == "NO_FACT_PRODUCT" for item in product_dimension.options)
    assert any(item.code == "NO_FACT_SEGMENT" for item in segment_dimension.options)
    assert len(overview.product_table.rows) == 8
    assert all(row.revenue.status == "available" for row in overview.product_table.rows)
    assert [row.code for row in overview.margin_matrix.rows] == [
        "KEY_ACCOUNT",
        "DOMESTIC",
    ]
    assert len(overview.margin_matrix.columns) == 8
    assert len(overview.margin_matrix.cells) == 16


def test_empty_product_fact_scope_is_degraded_not_vacuously_complete(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    bundle = DashboardSourceRepository().get_latest(analysis_session)

    table = DashboardService()._product_table(bundle, ())

    assert table.status == "degraded"
    assert table.comparison_label == "不可用"
