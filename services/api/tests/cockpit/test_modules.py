from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from flow_api.cockpit.modules import (
    ModuleFactContext,
    build_cashflow_module,
    build_expenses_module,
    build_risk_module,
    load_fact_context,
)


def test_risk_module_publishes_separate_comparable_ratio_charts() -> None:
    current = {
        "bs.current_assets:end": Decimal("120"),
        "bs.inventory:end": Decimal("20"),
        "bs.cash:end": Decimal("30"),
        "bs.current_liab:end": Decimal("60"),
        "bs.total_liab:end": Decimal("90"),
        "bs.total_assets:end": Decimal("150"),
        "bs.equity:end": Decimal("60"),
        "cf.ocf:cur": Decimal("24"),
    }
    prior = {
        "bs.current_assets:end": Decimal("100"),
        "bs.inventory:end": Decimal("20"),
        "bs.cash:end": Decimal("20"),
        "bs.current_liab:end": Decimal("50"),
        "bs.total_liab:end": Decimal("70"),
        "bs.total_assets:end": Decimal("140"),
        "bs.equity:end": Decimal("70"),
        "cf.ocf:cur": Decimal("20"),
    }
    ctx = ModuleFactContext(
        current_report_id=uuid4(),
        prior_report_id=uuid4(),
        period_label="FY2023",
        prior_period_label="FY2022",
        snapshot_id="snapshot",
        current=current,
        prior=prior,
    )

    response = build_risk_module(ctx)
    kpis = {item["name"]: item for item in response["kpis"]}
    assert kpis["流动比率"]["value"] == "2.0000"
    assert kpis["流动比率"]["prior_value"] == "2.0000"
    assert kpis["资产负债率"]["value"] == "0.6000"
    assert kpis["权益乘数"]["value"] == "2.5000"

    charts = response["charts"]
    assert charts["liquidity_ratios"]["unit"] == "倍"
    assert charts["liquidity_ratios"]["series"]["流动比率"] == [
        Decimal("2.0000"), Decimal("2.0000")
    ]
    assert charts["solvency_ratios"]["unit"] == "ratio"
    assert charts["leverage_ratios"]["unit"] == "倍"


def test_load_fact_context_retains_raw_cashflow_statement_rows() -> None:
    prior_report = SimpleNamespace(id=uuid4(), period_label="FY2022", items=[])
    current_report = SimpleNamespace(
        id=uuid4(),
        period_label="FY2023",
        items=[
            SimpleNamespace(
                statement_type="合并现金流量表",
                item_name="年初现金及现金等价物",
                value_end=None,
                value_begin=None,
                value_current=Decimal("10197742"),
                value_prior=Decimal("11818639"),
            ),
            SimpleNamespace(
                statement_type="合并现金流量表",
                item_name="年末现金及现金等价物",
                value_end=None,
                value_begin=None,
                value_current=Decimal("8784404"),
                value_prior=Decimal("10197742"),
            ),
            SimpleNamespace(
                statement_type="合并现金流量表",
                item_name="经营活动所得现金净额",
                value_end=None,
                value_begin=None,
                value_current=Decimal("1859349"),
                value_prior=Decimal("2330178"),
            ),
        ],
    )
    normalized_rows = [
        SimpleNamespace(
            item_id="cf.ocf",
            value_end=None,
            value_begin=None,
            value_current=Decimal("1859349"),
            value_prior=Decimal("2330178"),
        )
    ]
    result = SimpleNamespace(all=lambda: normalized_rows)
    session = Mock()
    session.scalars.side_effect = [
        [prior_report, current_report], result, result, result
    ]
    session.scalar.side_effect = [uuid4(), SimpleNamespace(id=uuid4())]

    context = load_fact_context(session, "DAMAI.SYN")

    assert context.raw_current[
        ("合并现金流量表", "年初现金及现金等价物", "cur")
    ] == Decimal("10197.742")
    assert context.raw_current[
        ("合并现金流量表", "经营活动所得现金净额", "cur")
    ] == Decimal("1859.349")
    bridge = build_cashflow_module(context)["charts"]["cash_bridge"]["steps"]
    assert bridge["年初"] == Decimal("10197.742")
    assert bridge["经营"] == Decimal("1859.349")
    assert bridge["年末"] == Decimal("8784.404")


def test_expenses_module_compares_two_reported_periods() -> None:
    current = {
        "is.revenue:cur": Decimal("1000"),
        "is.selling_exp:cur": Decimal("-100"),
        "is.admin_exp:cur": Decimal("-200"),
        "is.rnd_exp:cur": Decimal("-50"),
        "is.fin_exp:cur": Decimal("-10"),
    }
    prior = {
        "is.revenue:cur": Decimal("800"),
        "is.selling_exp:cur": Decimal("-80"),
        "is.admin_exp:cur": Decimal("-160"),
        "is.rnd_exp:cur": Decimal("-40"),
        "is.fin_exp:cur": Decimal("-8"),
    }
    context = ModuleFactContext(
        current_report_id=uuid4(),
        prior_report_id=uuid4(),
        period_label="FY2023",
        prior_period_label="FY2022",
        snapshot_id="snapshot",
        current=current,
        prior=prior,
    )

    response = build_expenses_module(context)

    selling = next(kpi for kpi in response["kpis"] if kpi["name"] == "销售及市场推广开支")
    assert selling["prior_value"] == "80"
    assert response["charts"]["expense_comparison"]["series"]["销售"] == [
        Decimal("80"),
        Decimal("100"),
    ]
    assert response["charts"]["expense_rate_trend"]["series"]["销售费用率"] == [
        Decimal("0.1000"),
        Decimal("0.1000"),
    ]
