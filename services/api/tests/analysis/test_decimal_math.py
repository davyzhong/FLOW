from decimal import Decimal

import pytest

from flow_api.analysis.decimal_math import (
    AnalysisCalculationError,
    contribution_ratio,
    ensure_decimal,
    reconcile,
)


def test_reconcile_accepts_a_cent_and_rejects_more() -> None:
    assert reconcile(Decimal("10.00"), Decimal("10.01"), Decimal("0.01")) == Decimal(
        "-0.01"
    )
    with pytest.raises(AnalysisCalculationError, match="does not reconcile"):
        reconcile(Decimal("10.00"), Decimal("10.02"), Decimal("0.01"))


def test_contribution_ratio_is_absent_for_zero_total() -> None:
    assert contribution_ratio(Decimal("1"), Decimal("0")) is None
    assert contribution_ratio(Decimal("5"), Decimal("20")) == Decimal("0.250000")


def test_public_decimal_guard_rejects_float() -> None:
    with pytest.raises(TypeError, match="float values are forbidden"):
        ensure_decimal(1.5)
