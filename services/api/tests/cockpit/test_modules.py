from decimal import Decimal
from uuid import uuid4

from flow_api.cockpit.modules import ModuleFactContext, build_risk_module


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
