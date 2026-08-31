from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from flow_api.metrics.decimal_math import (
    CalculatedDecimal,
    MetricCalculationError,
    calculate_amount,
    calculate_ratio,
)
from flow_api.metrics.models import MetricSpec


def _dependency_values(
    metric: MetricSpec, values: Mapping[str, Decimal]
) -> tuple[Decimal, ...]:
    missing = [dependency for dependency in metric.dependencies if dependency not in values]
    if missing:
        raise MetricCalculationError(
            metric.metric_code,
            "missing_dependency",
            f"{metric.metric_code} is missing dependencies: {missing}",
        )
    return tuple(values[dependency] for dependency in metric.dependencies)


def evaluate_derived_metric(
    metric: MetricSpec, dependency_values: Mapping[str, Decimal]
) -> CalculatedDecimal:
    values = _dependency_values(metric, dependency_values)
    if metric.formula == "subtract" and len(values) == 2:
        return calculate_amount(
            metric.metric_code,
            values[0] - values[1],
            output_scale=metric.output_scale,
        )
    if metric.formula == "ratio" and len(values) == 2:
        return calculate_ratio(
            metric.metric_code,
            values[0],
            values[1],
            output_scale=metric.output_scale,
        )
    if metric.formula == "closing_ar_over_trailing_12_revenue_times_365" and len(values) == 2:
        return calculate_ratio(
            metric.metric_code,
            values[0],
            values[1],
            multiplier=Decimal("365"),
            output_scale=metric.output_scale,
        )
    raise MetricCalculationError(
        metric.metric_code,
        "unsupported_formula",
        f"unsupported derived formula for {metric.metric_code}: {metric.formula}",
    )
