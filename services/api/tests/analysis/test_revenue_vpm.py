from decimal import Decimal

import pytest
from pydantic import ValidationError

from flow_api.analysis.bridges import RevenueMixCell, calculate_revenue_vpm


def _cell(
    code: str,
    *,
    q0: str,
    r0: str,
    q1: str,
    r1: str,
) -> RevenueMixCell:
    return RevenueMixCell(
        cell_code=code,
        comparison_orders=Decimal(q0),
        comparison_revenue=Decimal(r0),
        analysis_orders=Decimal(q1),
        analysis_revenue=Decimal(r1),
        source_record_count=2,
    )


def test_revenue_vpm_exactly_reconciles_volume_mix_and_price() -> None:
    result = calculate_revenue_vpm(
        (
            _cell("A", q0="10", r0="100", q1="12", r1="132"),
            _cell("B", q0="10", r0="200", q1="8", r1="144"),
        ),
        tolerance=Decimal("0.01"),
    )

    assert result.status == "complete"
    assert result.impact_amount == Decimal("-24.0000")
    assert [(driver.driver_code, driver.contribution_amount) for driver in result.drivers] == [
        ("volume", Decimal("0.0000")),
        ("mix", Decimal("-20.0000")),
        ("price", Decimal("-4.0000")),
    ]
    assert result.reconciliation_difference == Decimal("0.0000")
    assert result.source_record_count == 4


def test_revenue_vpm_degrades_for_new_or_lost_mix_cell() -> None:
    result = calculate_revenue_vpm(
        (
            _cell("existing", q0="10", r0="100", q1="10", r1="100"),
            _cell("new", q0="0", r0="0", q1="2", r1="20"),
        ),
        tolerance=Decimal("0.01"),
    )

    assert result.status == "degraded"
    assert result.degradation_code == "unmatched_mix_cell"
    assert result.drivers == ()
    assert result.impact_amount == Decimal("20.0000")


def test_revenue_vpm_detects_duplicate_cell_and_source_total_mismatch() -> None:
    cell = _cell("A", q0="10", r0="100", q1="12", r1="132")
    duplicate = calculate_revenue_vpm((cell, cell), tolerance=Decimal("0.01"))
    assert duplicate.status == "degraded"
    assert duplicate.degradation_code == "source_total_mismatch"

    mismatch = calculate_revenue_vpm(
        (cell,),
        tolerance=Decimal("0.01"),
        expected_comparison_revenue=Decimal("101"),
        expected_analysis_revenue=Decimal("132"),
    )
    assert mismatch.status == "degraded"
    assert mismatch.degradation_code == "source_total_mismatch"


def test_revenue_mix_cell_rejects_float() -> None:
    with pytest.raises(ValidationError, match="float values are forbidden"):
        RevenueMixCell(
            cell_code="A",
            comparison_orders=1.5,
            comparison_revenue=Decimal("1"),
            analysis_orders=Decimal("1"),
            analysis_revenue=Decimal("1"),
            source_record_count=1,
        )
