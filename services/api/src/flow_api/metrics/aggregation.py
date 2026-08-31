from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from flow_api.metrics.decimal_math import (
    CalculatedDecimal,
    MetricCalculationError,
    calculate_ratio,
    decimal_sum,
)
from flow_api.metrics.grain import MetricGrain


@dataclass(frozen=True, slots=True)
class PeriodValue:
    period_id: UUID
    month_key: int
    grain: MetricGrain
    value: Decimal


def aggregate_flow(
    values: Iterable[PeriodValue], months: frozenset[int]
) -> dict[MetricGrain, Decimal]:
    grouped: defaultdict[MetricGrain, list[Decimal]] = defaultdict(list)
    for value in values:
        if value.month_key in months:
            grouped[value.grain].append(value.value)
    return {
        grain: decimal_sum(grouped[grain])
        for grain in sorted(grouped, key=lambda item: item.sort_key)
    }


def aggregate_closing_balance(
    values: Iterable[PeriodValue], months: frozenset[int]
) -> dict[MetricGrain, Decimal]:
    grouped: defaultdict[MetricGrain, list[PeriodValue]] = defaultdict(list)
    for value in values:
        if value.month_key in months:
            grouped[value.grain].append(value)
    result: dict[MetricGrain, Decimal] = {}
    for grain in sorted(grouped, key=lambda item: item.sort_key):
        closing_month = max(value.month_key for value in grouped[grain])
        result[grain] = decimal_sum(
            value.value for value in grouped[grain] if value.month_key == closing_month
        )
    return result


def ratio_by_grain(
    metric_code: str,
    numerators: Mapping[MetricGrain, Decimal],
    denominators: Mapping[MetricGrain, Decimal],
    *,
    multiplier: Decimal = Decimal("1"),
    output_scale: int = 6,
) -> dict[MetricGrain, CalculatedDecimal]:
    if set(numerators) != set(denominators):
        missing = sorted(
            set(numerators).symmetric_difference(denominators),
            key=lambda grain: grain.sort_key,
        )
        raise MetricCalculationError(
            metric_code,
            "missing_dependency",
            f"{metric_code} has unmatched grains: {[grain.dimensions for grain in missing]}",
        )
    return {
        grain: calculate_ratio(
            metric_code,
            numerators[grain],
            denominators[grain],
            multiplier=multiplier,
            output_scale=output_scale,
        )
        for grain in sorted(numerators, key=lambda item: item.sort_key)
    }
