from decimal import Decimal

from flow_api.analysis.bridges import FulfillmentTotals, calculate_fulfillment_rve


def test_fulfillment_rve_exactly_reconciles_rate_volume_and_efficiency() -> None:
    result = calculate_fulfillment_rve(
        FulfillmentTotals(
            comparison_orders=Decimal("10"),
            comparison_shipments=Decimal("20"),
            comparison_cost=Decimal("100"),
            analysis_orders=Decimal("12"),
            analysis_shipments=Decimal("30"),
            analysis_cost=Decimal("180"),
            source_record_count=4,
        ),
        tolerance=Decimal("0.01"),
    )

    assert result.status == "complete"
    assert result.impact_amount == Decimal("80.0000")
    assert [(driver.driver_code, driver.contribution_amount) for driver in result.drivers] == [
        ("volume", Decimal("20.0000")),
        ("efficiency", Decimal("30.0000")),
        ("rate", Decimal("30.0000")),
    ]
    assert result.reconciliation_difference == Decimal("0.0000")


def test_fulfillment_rve_degrades_on_zero_denominator() -> None:
    result = calculate_fulfillment_rve(
        FulfillmentTotals(
            comparison_orders=Decimal("0"),
            comparison_shipments=Decimal("0"),
            comparison_cost=Decimal("0"),
            analysis_orders=Decimal("12"),
            analysis_shipments=Decimal("30"),
            analysis_cost=Decimal("180"),
            source_record_count=2,
        ),
        tolerance=Decimal("0.01"),
    )

    assert result.status == "degraded"
    assert result.degradation_code == "zero_denominator"
    assert result.drivers == ()
