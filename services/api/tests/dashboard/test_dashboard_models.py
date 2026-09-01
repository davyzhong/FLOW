from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from flow_api.dashboard.models import (
    ActiveFilters,
    DashboardContext,
    DashboardOverview,
    DashboardValue,
    DataStatus,
    FilterOptions,
    FindingItem,
    MarginMatrix,
    MetricCard,
    ProductPerformance,
    ProfitBridge,
    TrendPanel,
)


def _id(value: int) -> UUID:
    return UUID(int=value)


def _available(value: str = "1.0000") -> DashboardValue:
    return DashboardValue(
        status="available",
        exact_value=value,
        display_value=value,
        semantic_direction="neutral",
    )


def _unavailable() -> DashboardValue:
    return DashboardValue(
        status="unavailable",
        unavailable_code="comparison_not_published",
        unavailable_message="当前口径未发布该比较值",
        display_value="—",
        semantic_direction="neutral",
    )


def _cards() -> tuple[MetricCard, ...]:
    codes = (
        "orders",
        "revenue",
        "revenue_per_order",
        "gross_margin",
        "fulfillment_cost_rate",
        "operating_profit",
        "ar_balance",
        "operating_cash_flow",
    )
    return tuple(
        MetricCard(
            metric_code=code,
            title=code,
            category="经营",
            unit="CNY" if code != "orders" else "order",
            primary=_available(),
            budget=_unavailable(),
            yoy=_available("0.100000"),
            ytd_budget=_unavailable(),
            companion=None,
        )
        for code in codes
    )


def _overview() -> DashboardOverview:
    return DashboardOverview(
        state="ready",
        context=DashboardContext(
            batch_id=_id(1),
            import_version_id=_id(2),
            metric_snapshot_id=_id(3),
            analysis_run_id=_id(4),
            as_of_month="2026-08",
            metric_definition_set_id="flow.metrics.logistics.v1",
            metric_definition_set_hash="a" * 64,
            metric_engine_version="flow.metrics.engine.v1",
            analysis_policy_id="flow.analysis.logistics.v1",
            analysis_policy_hash="b" * 64,
            analysis_engine_version="flow-analysis/1",
            generated_at="2026-09-01T00:00:00Z",
        ),
        filter_options=FilterOptions(dimensions=(), supported_combinations=((),)),
        active_filters=ActiveFilters(period_view="month", is_total_scope=True),
        data_status=DataStatus(
            batch_status="published",
            import_status="published",
            quality_status="passed",
            blocking_issue_count=0,
            warning_issue_count=0,
            acknowledged_warning_count=0,
            reconciliation_status="passed",
            metric_snapshot_status="published",
            analysis_run_status="published",
            freshness_status="fresh",
        ),
        metric_cards=_cards(),
        trends=TrendPanel(
            status="partial_series",
            coverage_count=0,
            expected_count=12,
            missing_months=(
                "2025-09",
                "2025-10",
                "2025-11",
                "2025-12",
                "2026-01",
                "2026-02",
                "2026-03",
                "2026-04",
                "2026-05",
                "2026-06",
                "2026-07",
                "2026-08",
            ),
            points=(),
        ),
        profit_bridge=ProfitBridge(
            status="complete",
            comparison_basis="prior_year",
            impact=_available("-77484.3599"),
            reconciliation_status="passed",
            reconciliation_difference="0.0000",
            drivers=(),
        ),
        findings=(),
        product_table=ProductPerformance(
            status="complete", comparison_label="同比", rows=()
        ),
        margin_matrix=MarginMatrix(
            status="complete",
            comparison_label="同比",
            rows=(),
            columns=(),
            cells=(),
        ),
        highlights=(),
        degradations=(),
    )


def test_dashboard_value_forbids_float_and_enforces_availability_state() -> None:
    with pytest.raises(ValidationError, match="float values are forbidden"):
        DashboardValue(
            status="available",
            exact_value=1.2,
            display_value="1.2",
            semantic_direction="neutral",
        )

    with pytest.raises(ValidationError, match="available value requires"):
        DashboardValue(
            status="available",
            display_value="—",
            semantic_direction="neutral",
        )

    with pytest.raises(ValidationError, match="unavailable value cannot expose"):
        DashboardValue(
            status="unavailable",
            exact_value="1.0000",
            display_value="—",
            unavailable_code="comparison_not_published",
            unavailable_message="missing",
            semantic_direction="neutral",
        )


def test_dashboard_requires_the_eight_metric_cards_in_stable_order() -> None:
    overview = _overview()

    assert [card.metric_code for card in overview.metric_cards] == [
        "orders",
        "revenue",
        "revenue_per_order",
        "gross_margin",
        "fulfillment_cost_rate",
        "operating_profit",
        "ar_balance",
        "operating_cash_flow",
    ]

    with pytest.raises(ValidationError, match="exactly eight metric cards"):
        overview.model_copy(update={"metric_cards": overview.metric_cards[:-1]}).model_validate(
            overview.model_copy(update={"metric_cards": overview.metric_cards[:-1]}).model_dump()
        )


def test_dashboard_models_are_frozen_and_serialize_decimals_as_strings() -> None:
    overview = _overview()

    with pytest.raises(ValidationError):
        overview.metric_cards[0].primary.exact_value = Decimal("2")  # type: ignore[misc]

    payload = overview.model_dump(mode="json")
    assert payload["metric_cards"][0]["primary"]["exact_value"] == "1.0000"
    assert payload["context"]["metric_snapshot_id"] == str(_id(3))


def test_filtered_dashboard_findings_must_be_labelled_global_scope() -> None:
    overview = _overview()
    finding = FindingItem(
        finding_id=_id(10),
        finding_type="revenue_growth",
        title="收入增长",
        impact=_available("2356634.0957"),
        total_score="82.000000",
        comparison_basis="prior_year",
        evidence_verified=5,
        evidence_total=5,
        scope="global",
        investigation_path="/investigations/00000000-0000-0000-0000-00000000000a",
    )
    filtered = overview.model_copy(
        update={
            "active_filters": ActiveFilters(
                period_view="month",
                customer_segment_id=_id(20),
                is_total_scope=False,
            ),
            "findings": (finding,),
        }
    )

    assert filtered.findings[0].scope == "global"
