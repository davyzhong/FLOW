"""CFO 驾驶舱投影服务单元测试（批次 A）。

覆盖不变量：
- 可追溯铁律：每个 KPI 必带 snapshot_id
- unavailable 显式表达，不补零（环比/行业分位首版为 unavailable）
- 管控线状态：突破=breach / 接近=near / 正常=ok / 无参照=not_ready
- 极性：费用类指标为 negative（下降是好事），收入类为 positive
- 结论条：只由已冻结 Finding 生成；无 Finding 时不补造判断
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from flow_api.cockpit.service import (
    CockpitProjectionService,
    _control_status,
    _polarity,
)
from flow_api.dashboard.models import (
    ActiveFilters,
    DashboardContext,
    DataStatus,
)

SNAPSHOT_ID = uuid4()


def _value(
    exact: str | None,
    *,
    direction: str = "positive",
    display: str = "1.0",
) -> SimpleNamespace:
    def _dump(**_kwargs: Any) -> dict[str, Any]:
        return {
            "status": "ready" if exact is not None else "unavailable",
            "exact_value": exact,
            "display_value": display if exact is not None else "—",
            "semantic_direction": direction,
            "unavailable_code": None if exact is not None else "not_published",
            "unavailable_message": None if exact is not None else "未发布",
        }

    return SimpleNamespace(model_dump=_dump)


def _value_dict(
    exact: str | None,
    *,
    direction: str = "positive",
    display: str = "1.0",
) -> dict[str, Any]:
    return {
        "status": "ready" if exact is not None else "unavailable",
        "exact_value": exact,
        "display_value": display if exact is not None else "—",
        "semantic_direction": direction,
        "unavailable_code": None if exact is not None else "not_published",
        "unavailable_message": None if exact is not None else "未发布",
    }


def _card(
    code: str = "revenue",
    *,
    primary_exact: str | None = "100",
    yoy_exact: str | None = "110",
    ytd_exact: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        metric_code=code,
        title="营业收入",
        category="收入",
        unit="万元",
        primary=_value(primary_exact, display="100"),
        budget=_value(None),
        yoy=_value(yoy_exact, display="110"),
        ytd_budget=_value(ytd_exact, display="—") if ytd_exact else None,
        companion=None,
    )


def _finding(impact_direction: str = "positive") -> SimpleNamespace:
    finding_id = uuid4()

    def _impact_dump(**_kwargs: Any) -> dict[str, Any]:
        return _value_dict("0.1", direction=impact_direction, display="10.0%")

    return SimpleNamespace(
        finding_id=finding_id,
        finding_type="variance",
        title="收入结构变化",
        impact=SimpleNamespace(
            semantic_direction=impact_direction,
            model_dump=_impact_dump,
        ),
        total_score="0.8",
        comparison_basis="yoy",
        evidence_verified=3,
        evidence_total=3,
        scope="revenue",
        investigation_path=f"/investigations/{finding_id}",
    )


def _trend_point(month: str, revenue: str) -> SimpleNamespace:
    return SimpleNamespace(
        month=month,
        metric_snapshot_id=SNAPSHOT_ID,
        revenue=_value(revenue, display=revenue),
        operating_profit=_value("10", display="10"),
        gross_margin=_value("0.3", display="30.0%"),
        operating_cash_flow=_value("5", display="5"),
    )


def _overview(
    *,
    cards: list[SimpleNamespace] | None = None,
    findings: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    context = DashboardContext(
        batch_id=uuid4(),
        import_version_id=uuid4(),
        metric_snapshot_id=SNAPSHOT_ID,
        analysis_run_id=uuid4(),
        as_of_month="2026-06",
        metric_definition_set_id="v1.2",
        metric_definition_set_hash="a" * 64,
        metric_engine_version="1.2.0",
        analysis_policy_id="default",
        analysis_policy_hash="b" * 64,
        analysis_engine_version="1.2.0",
        generated_at=datetime(2026, 6, 30, tzinfo=UTC),
    )
    data_status = DataStatus(
        batch_status="ready",
        import_status="ready",
        quality_status="passed",
        blocking_issue_count=0,
        warning_issue_count=0,
        acknowledged_warning_count=0,
        reconciliation_status="passed",
        metric_snapshot_status="published",
        analysis_run_status="published",
        freshness_status="fresh",
    )
    trends = SimpleNamespace(
        status="complete",
        coverage_count=2,
        expected_count=12,
        missing_months=(),
        points=(_trend_point("2026-05", "90"), _trend_point("2026-06", "100")),
        degradation_message=None,
    )
    return SimpleNamespace(
        state="ready",
        context=context,
        data_status=data_status,
        metric_cards=tuple(cards or [_card()]),
        trends=trends,
        findings=tuple(findings or []),
    )


def _service(overview: SimpleNamespace) -> CockpitProjectionService:
    service = CockpitProjectionService()
    stub = SimpleNamespace(
        get_overview=lambda session, filters, now=None, **kw: overview
    )
    object.__setattr__(service, "_dashboard", stub)
    return service


@pytest.fixture
def filters() -> ActiveFilters:
    return ActiveFilters(period_view="ytd", is_total_scope=True)


def _project(overview: SimpleNamespace, filters: ActiveFilters, **kw: Any):
    return _service(overview).overview(SimpleNamespace(), filters=filters, **kw)


# ── 极性 ─────────────────────────────────────────────────────────


def test_polarity_revenue_is_positive() -> None:
    assert _polarity("revenue") == "positive"


def test_polarity_expense_is_negative() -> None:
    assert _polarity("period_expense_ratio") == "negative"
    assert _polarity("asset_debt_ratio") == "negative"
    assert _polarity("ccc") == "negative"


# ── 管控线状态 ─────────────────────────────────────────────────────


def test_control_status_ok_when_well_above_line() -> None:
    value = _value_dict("130", display="130")
    line = _value_dict("90", display="90")
    assert _control_status(value, line, "positive") == "ok"


def test_control_status_breach_when_below_line_positive_polarity() -> None:
    value = _value_dict("80", display="80")
    line = _value_dict("90", display="90")
    assert _control_status(value, line, "positive") == "breach"


def test_control_status_breach_when_above_line_negative_polarity() -> None:
    value = _value_dict("95", display="95")
    line = _value_dict("90", display="90")
    assert _control_status(value, line, "negative") == "breach"


def test_control_status_near_within_120_percent() -> None:
    value = _value_dict("110", display="110")
    line = _value_dict("100", display="100")
    assert _control_status(value, line, "positive") == "near"


def test_control_status_near_negative_polarity_80_percent() -> None:
    value = _value_dict("85", display="85")
    line = _value_dict("100", display="100")
    assert _control_status(value, line, "negative") == "near"


def test_control_status_not_ready_without_line() -> None:
    value = _value_dict("100", display="100")
    assert _control_status(value, None, "positive") == "not_ready"


def test_control_status_not_ready_when_value_unavailable() -> None:
    value = _value_dict(None)
    line = _value_dict("90", display="90")
    assert _control_status(value, line, "positive") == "not_ready"


def test_control_status_not_ready_on_zero_line() -> None:
    value = _value_dict("100", display="100")
    line = _value_dict("0", display="0")
    assert _control_status(value, line, "positive") == "not_ready"


# ── KPI 投影不变量 ─────────────────────────────────────────────────


def test_every_kpi_carries_snapshot_id(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    assert projection.kpi_cards
    for card in projection.kpi_cards:
        assert card.snapshot_id == str(SNAPSHOT_ID)


def test_mom_and_percentile_unavailable_not_zero(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    card = projection.kpi_cards[0]
    assert card.comparisons["mom"]["status"] == "unavailable"
    assert card.comparisons["mom"]["display_value"] == "—"
    assert card.comparisons["percentile"]["status"] == "unavailable"


def test_yoy_is_passed_through(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    yoy = projection.kpi_cards[0].comparisons["yoy"]
    assert yoy["status"] == "ready"
    assert yoy["display_value"] == "110"


def test_caliber_note_always_present(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    for card in projection.kpi_cards:
        assert card.caliber_note


def test_control_status_not_ready_without_budget(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    assert projection.kpi_cards[0].control_status == "not_ready"


def test_control_status_ready_when_budget_line_present(filters: ActiveFilters) -> None:
    overview = _overview(cards=[_card(ytd_exact="100")])
    projection = _project(overview, filters)
    card = projection.kpi_cards[0]
    assert card.control_line is not None
    assert card.control_status in {"ok", "near"}


def test_negative_polarity_expense_metric(filters: ActiveFilters) -> None:
    overview = _overview(cards=[_card(code="period_expense_ratio")])
    projection = _project(overview, filters)
    assert projection.kpi_cards[0].polarity == "negative"


# ── 趋势 ───────────────────────────────────────────────────────────


def test_trend_series_cover_four_metrics(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    keys = {s.key for s in projection.trends[0].series}
    expected = {"revenue", "operating_profit", "gross_margin", "operating_cash_flow"}
    assert keys == expected


def test_trend_points_keep_month_and_display(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters)
    revenue = next(s for s in projection.trends[0].series if s.key == "revenue")
    assert [p["period"] for p in revenue.points] == ["2026-05", "2026-06"]
    assert revenue.points[-1]["display_value"] == "100"
    assert Decimal(str(revenue.points[-1]["value"])) == Decimal("100")


# ── 结论条 ─────────────────────────────────────────────────────────


def test_conclusion_without_findings_does_not_fabricate(filters: ActiveFilters) -> None:
    projection = _project(_overview(findings=[]), filters)
    assert projection.conclusion.findings == []
    assert "不补造" in projection.conclusion.text


def test_conclusion_links_finding_investigation_path(filters: ActiveFilters) -> None:
    projection = _project(_overview(findings=[_finding("negative")]), filters)
    path = projection.conclusion.findings[0]["investigation_path"]
    assert path.startswith("/investigations/")
    assert projection.conclusion.tone in {"attention", "risk"}


def test_conclusion_neutral_when_no_negative_findings(filters: ActiveFilters) -> None:
    projection = _project(_overview(findings=[_finding("positive")]), filters)
    assert projection.conclusion.tone == "neutral"


def test_source_notice_is_carried(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters, source_notice="演示数据")
    assert projection.source_notice == "演示数据"


def test_state_is_propagated(filters: ActiveFilters) -> None:
    projection = _project(_overview(), filters, now=datetime(2026, 9, 30, tzinfo=UTC))
    assert projection.state == "ready"
