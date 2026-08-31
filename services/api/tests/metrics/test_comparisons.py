from __future__ import annotations

import importlib
from decimal import Decimal

import pytest


def _comparisons_module():
    try:
        return importlib.import_module("flow_api.metrics.comparisons")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.comparisons does not exist")


def test_amount_and_ratio_point_variances_use_actual_minus_comparison() -> None:
    module = _comparisons_module()

    assert module.variance(Decimal("90"), Decimal("100")) == Decimal("-10")
    ratio_points = module.ratio_point_variance(
        "gross_margin", Decimal("0.328583"), Decimal("0.345000")
    )

    assert ratio_points.exact_value == Decimal("-0.016417")
    assert ratio_points.persisted_value == Decimal("-0.0164")


def test_variance_percent_uses_comparison_as_denominator() -> None:
    module = _comparisons_module()

    result = module.variance_pct("revenue", Decimal("90"), Decimal("100"))

    assert result.exact_value == Decimal("-0.100000")
    assert result.persisted_value == Decimal("-0.1000")


def test_zero_comparison_is_not_silently_replaced() -> None:
    module = _comparisons_module()

    with pytest.raises(module.MetricCalculationError) as error:
        module.variance_pct("revenue", Decimal("10"), Decimal("0"))

    assert error.value.code == "zero_denominator"
