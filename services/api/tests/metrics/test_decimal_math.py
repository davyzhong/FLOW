from __future__ import annotations

import importlib
from decimal import Decimal

import pytest


def _math_module():
    try:
        return importlib.import_module("flow_api.metrics.decimal_math")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.decimal_math does not exist")


def test_decimal_sum_is_exact_and_rounds_half_up() -> None:
    module = _math_module()

    assert module.decimal_sum([Decimal("1.00004"), Decimal("-0.00001")]) == Decimal(
        "1.0000"
    )
    assert module.decimal_sum([Decimal("1.00005")]) == Decimal("1.0001")
    assert module.decimal_sum([], scale=6) == Decimal("0.000000")


def test_decimal_boundary_rejects_float() -> None:
    module = _math_module()

    with pytest.raises(module.MetricCalculationError) as error:
        module.decimal_sum([Decimal("1"), 0.5])

    assert error.value.code == "float_rejected"
    assert error.value.metric_code == "decimal_sum"


@pytest.mark.parametrize(
    ("numerator", "denominator", "exact", "persisted"),
    [
        ("1", "3", "0.333333", "0.3333"),
        ("2", "3", "0.666667", "0.6667"),
        ("-1", "8", "-0.125000", "-0.1250"),
    ],
)
def test_ratio_preserves_exact_value_and_separate_persistence_rounding(
    numerator: str, denominator: str, exact: str, persisted: str
) -> None:
    module = _math_module()

    result = module.calculate_ratio(
        "test_ratio", Decimal(numerator), Decimal(denominator), output_scale=6
    )

    assert result.exact_value == Decimal(exact)
    assert result.persisted_value == Decimal(persisted)
    assert result.output_scale == 6
    assert result.rounding == "ROUND_HALF_UP"


def test_ratio_zero_denominator_is_a_typed_blocker() -> None:
    module = _math_module()

    with pytest.raises(module.MetricCalculationError) as error:
        module.calculate_ratio("gross_margin", Decimal("1"), Decimal("0"))

    assert error.value.code == "zero_denominator"
    assert error.value.metric_code == "gross_margin"
