from decimal import Decimal

from flow_api.analysis.playbooks import ArCashInput, calculate_ar_cash_impact


def _input(*, aging_complete: bool = True) -> ArCashInput:
    return ArCashInput(
        comparison_bucket_balances={
            "current": Decimal("100"),
            "1-30": Decimal("50"),
            "31-60": Decimal("20"),
        },
        analysis_bucket_balances={
            "current": Decimal("110"),
            "1-30": Decimal("60"),
            "31-60": Decimal("40"),
        },
        comparison_closing_ar=Decimal("170"),
        analysis_closing_ar=Decimal("210"),
        comparison_dso=Decimal("45"),
        analysis_dso=Decimal("52"),
        due_amount=Decimal("100"),
        collected_amount=Decimal("80"),
        overdue_by_customer={"CUST_A": Decimal("25"), "CUST_B": Decimal("15")},
        aging_complete=aging_complete,
        source_record_count=12,
    )


def test_ar_cash_impact_reconciles_aging_buckets_without_double_counting_customers() -> None:
    result = calculate_ar_cash_impact(_input(), tolerance=Decimal("0.01"))

    assert result.status == "complete"
    assert result.impact_amount == Decimal("-40.0000")
    assert [(driver.driver_code, driver.contribution_amount) for driver in result.drivers] == [
        ("aging_1_30", Decimal("-10.0000")),
        ("aging_31_60", Decimal("-20.0000")),
        ("aging_current", Decimal("-10.0000")),
    ]
    assert result.calculation_trace["dso_change"] == "7"
    assert result.calculation_trace["collection_rate"] == "0.800000"
    assert result.calculation_trace["collection_shortfall"] == "20.0000"
    assert result.calculation_trace["top_overdue_customer"] == "CUST_A"
    assert all(not driver.driver_code.startswith("customer_") for driver in result.drivers)


def test_ar_cash_degrades_when_aging_detail_is_incomplete() -> None:
    result = calculate_ar_cash_impact(
        _input(aging_complete=False), tolerance=Decimal("0.01")
    )

    assert result.status == "degraded"
    assert result.degradation_code == "missing_required_field"
    assert result.impact_amount == Decimal("-40.0000")
    assert result.drivers == ()
