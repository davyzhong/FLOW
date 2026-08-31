from __future__ import annotations

from decimal import Decimal

from flow_api.metrics.decimal_math import (
    CalculatedDecimal,
    MetricCalculationError,
    calculate_amount,
    calculate_ratio,
)


def _require_decimal(metric_code: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise MetricCalculationError(
            metric_code,
            "float_rejected",
            f"{metric_code} comparisons accept Decimal values only",
        )
    return value


def variance(actual: Decimal, comparison: Decimal) -> Decimal:
    return _require_decimal("variance", actual) - _require_decimal("variance", comparison)


def variance_pct(
    metric_code: str, actual: Decimal, comparison: Decimal
) -> CalculatedDecimal:
    return calculate_ratio(
        metric_code,
        variance(actual, comparison),
        comparison,
        output_scale=6,
    )


def ratio_point_variance(
    metric_code: str, actual: Decimal, comparison: Decimal
) -> CalculatedDecimal:
    return calculate_amount(
        metric_code,
        variance(actual, comparison),
        output_scale=6,
    )
