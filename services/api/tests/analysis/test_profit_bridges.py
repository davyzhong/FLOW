from decimal import Decimal

from flow_api.analysis.bridges import RevenueMixCell, calculate_revenue_vpm
from flow_api.analysis.playbooks import (
    ProfitBridgeInput,
    calculate_gross_profit_bridge,
    calculate_operating_profit_bridge,
)


def _revenue_result():
    return calculate_revenue_vpm(
        (
            RevenueMixCell(
                cell_code="A",
                comparison_orders=Decimal("10"),
                comparison_revenue=Decimal("100"),
                analysis_orders=Decimal("12"),
                analysis_revenue=Decimal("132"),
                source_record_count=2,
            ),
            RevenueMixCell(
                cell_code="B",
                comparison_orders=Decimal("10"),
                comparison_revenue=Decimal("200"),
                analysis_orders=Decimal("8"),
                analysis_revenue=Decimal("144"),
                source_record_count=2,
            ),
        ),
        tolerance=Decimal("0.01"),
    )


def _input() -> ProfitBridgeInput:
    return ProfitBridgeInput(
        revenue_result=_revenue_result(),
        comparison_warehousing_cost=Decimal("50"),
        analysis_warehousing_cost=Decimal("55"),
        comparison_transportation_cost=Decimal("60"),
        analysis_transportation_cost=Decimal("70"),
        comparison_other_direct_cost=Decimal("10"),
        analysis_other_direct_cost=Decimal("11"),
        comparison_gross_profit=Decimal("180"),
        analysis_gross_profit=Decimal("140"),
        comparison_operating_expense=Decimal("30"),
        analysis_operating_expense=Decimal("35"),
        comparison_operating_profit=Decimal("150"),
        analysis_operating_profit=Decimal("105"),
        source_record_count=12,
    )


def test_gross_profit_bridge_reuses_revenue_drivers_and_cost_signs() -> None:
    result = calculate_gross_profit_bridge(_input(), tolerance=Decimal("0.01"))

    assert result.status == "complete"
    assert result.impact_amount == Decimal("-40.0000")
    assert [(driver.driver_code, driver.contribution_amount) for driver in result.drivers] == [
        ("revenue_volume", Decimal("0.0000")),
        ("revenue_mix", Decimal("-20.0000")),
        ("revenue_price", Decimal("-4.0000")),
        ("warehousing_cost", Decimal("-5.0000")),
        ("transportation_cost", Decimal("-10.0000")),
        ("other_direct_cost", Decimal("-1.0000")),
    ]
    assert result.reconciliation_difference == Decimal("0.0000")


def test_operating_profit_bridge_extends_gross_profit_with_opex() -> None:
    gross = calculate_gross_profit_bridge(_input(), tolerance=Decimal("0.01"))
    result = calculate_operating_profit_bridge(
        _input(), gross_result=gross, tolerance=Decimal("0.01")
    )

    assert result.status == "complete"
    assert result.impact_amount == Decimal("-45.0000")
    assert result.drivers[-1].driver_code == "operating_expense"
    assert result.drivers[-1].contribution_amount == Decimal("-5.0000")
    assert result.reconciliation_difference == Decimal("0.0000")


def test_profit_bridges_degrade_when_revenue_vpm_is_degraded() -> None:
    degraded_revenue = calculate_revenue_vpm(
        (
            RevenueMixCell(
                cell_code="new",
                comparison_orders=Decimal("0"),
                comparison_revenue=Decimal("0"),
                analysis_orders=Decimal("1"),
                analysis_revenue=Decimal("10"),
                source_record_count=1,
            ),
        ),
        tolerance=Decimal("0.01"),
    )
    payload = _input().model_copy(update={"revenue_result": degraded_revenue})

    gross = calculate_gross_profit_bridge(payload, tolerance=Decimal("0.01"))
    assert gross.status == "degraded"
    assert gross.degradation_code == "upstream_result_degraded"
    assert gross.drivers == ()
