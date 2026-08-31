from __future__ import annotations

import importlib
from decimal import Decimal
from uuid import UUID

import pytest


def _aggregation_module():
    try:
        return importlib.import_module("flow_api.metrics.aggregation")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.aggregation does not exist")


def test_flow_aggregation_preserves_total_and_slice_invariants() -> None:
    module = _aggregation_module()
    period_id = UUID("10000000-0000-0000-0000-000000000001")
    organization_a = UUID("20000000-0000-0000-0000-000000000001")
    organization_b = UUID("20000000-0000-0000-0000-000000000002")
    total = module.MetricGrain()
    grain_a = module.MetricGrain(organization_id=organization_a)
    grain_b = module.MetricGrain(organization_id=organization_b)
    values = (
        module.PeriodValue(period_id, 202608, total, Decimal("4.0000")),
        module.PeriodValue(period_id, 202608, grain_a, Decimal("4.0000")),
        module.PeriodValue(period_id, 202608, total, Decimal("20.0000")),
        module.PeriodValue(period_id, 202608, grain_b, Decimal("20.0000")),
        module.PeriodValue(period_id, 202607, total, Decimal("99.0000")),
    )

    result = module.aggregate_flow(values, frozenset({202608}))

    assert result[total] == Decimal("24.0000")
    assert result[total] == result[grain_a] + result[grain_b]


def test_balance_aggregation_uses_last_available_period_per_grain() -> None:
    module = _aggregation_module()
    total = module.MetricGrain()
    customer = module.MetricGrain(
        customer_id=UUID("30000000-0000-0000-0000-000000000001")
    )
    values = tuple(
        module.PeriodValue(
            UUID(f"40000000-0000-0000-0000-{month:012d}"),
            202600 + month,
            grain,
            Decimal(month * multiplier),
        )
        for month in range(1, 9)
        for grain, multiplier in ((total, 100), (customer, 40))
    )

    result = module.aggregate_closing_balance(
        values, frozenset(202600 + month for month in range(1, 9))
    )

    assert result[total] == Decimal("800.0000")
    assert result[customer] == Decimal("320.0000")
    assert result[total] != sum(
        (value.value for value in values if value.grain == total), Decimal("0")
    )


def test_ratio_is_recalculated_from_same_grain_totals() -> None:
    module = _aggregation_module()
    total = module.MetricGrain()
    segment_a = module.MetricGrain(
        customer_segment_id=UUID("50000000-0000-0000-0000-000000000001")
    )
    segment_b = module.MetricGrain(
        customer_segment_id=UUID("50000000-0000-0000-0000-000000000002")
    )
    gross_profit = {
        total: Decimal("50"),
        segment_a: Decimal("10"),
        segment_b: Decimal("40"),
    }
    revenue = {
        total: Decimal("200"),
        segment_a: Decimal("20"),
        segment_b: Decimal("180"),
    }

    result = module.ratio_by_grain("gross_margin", gross_profit, revenue)

    assert result[total].exact_value == Decimal("0.250000")
    assert result[total].exact_value != (
        result[segment_a].exact_value + result[segment_b].exact_value
    ) / Decimal("2")
