from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.metrics.aggregation import (
    PeriodValue,
    aggregate_closing_balance,
    aggregate_flow,
)
from flow_api.metrics.catalog import metric_catalog_hash, topological_metric_order
from flow_api.metrics.comparisons import ratio_point_variance, variance, variance_pct
from flow_api.metrics.decimal_math import calculate_amount, calculate_ratio
from flow_api.metrics.formulas import evaluate_derived_metric
from flow_api.metrics.grain import MetricGrain, project_metric_grains
from flow_api.metrics.models import DimensionName, MetricCatalog, MetricSpec
from flow_api.metrics.repositories import MetricSourceRepository
from flow_api.metrics.results import CalculatedMetricValue, MetricCalculationResult
from flow_api.metrics.source_rows import PublishedMetricSource
from flow_api.metrics.windows import ComparisonType, MetricWindow, metric_windows

_ACTUAL_COMPARISONS = {
    "actual_month",
    "actual_ytd",
    "prior_year_month",
    "prior_year_ytd",
    "trailing_12",
}
_BUDGET_COMPARISONS = {"budget_month", "budget_ytd"}
_FINANCIAL_ACCOUNTS = {
    "operating_profit": "OPERATING_PROFIT",
    "operating_cash_flow": "OPERATING_CASH_FLOW",
}
_BUDGET_CODES = {
    "REVENUE": "revenue",
    "DIRECT_COST": "direct_cost",
    "OPERATING_PROFIT": "operating_profit",
    "OPERATING_CASH_FLOW": "operating_cash_flow",
}


def _dimensions(
    *,
    organization: UUID | None = None,
    customer: UUID | None = None,
    customer_segment: UUID | None = None,
    logistics_product: UUID | None = None,
    region: UUID | None = None,
) -> dict[DimensionName, UUID | None]:
    return {
        "organization": organization,
        "customer": customer,
        "customer_segment": customer_segment,
        "logistics_product": logistics_product,
        "region": region,
    }


def _period_value(
    period_id: UUID, month_key: int, grain: MetricGrain, value: Decimal
) -> PeriodValue:
    return PeriodValue(period_id=period_id, month_key=month_key, grain=grain, value=value)


def _ending_month(window: MetricWindow) -> int:
    return max(window.included_months)


def _shift_month(month_key: int, offset: int) -> int:
    year, month = divmod(month_key, 100)
    absolute = year * 12 + month - 1 + offset
    shifted_year, shifted_month = divmod(absolute, 12)
    return shifted_year * 100 + shifted_month + 1


def _trailing_months(ending_month: int) -> frozenset[int]:
    return frozenset(_shift_month(ending_month, offset) for offset in range(-11, 1))


def _result_sort_key(value: CalculatedMetricValue) -> tuple[object, ...]:
    return (
        value.metric_code,
        value.comparison_type,
        value.period_id.hex,
        value.grain.sort_key,
    )


class MetricCalculator:
    def __init__(
        self, session: Session, repository: MetricSourceRepository | None = None
    ) -> None:
        self._session = session
        self._repository = repository or MetricSourceRepository()

    def calculate(
        self,
        source: PublishedMetricSource,
        catalog: MetricCatalog,
        as_of_month: int,
    ) -> MetricCalculationResult:
        specs = {metric.metric_code: metric for metric in catalog.metrics}
        operating_rows = self._repository.operating_rows(self._session, source)
        financial_rows = self._repository.financial_rows(self._session, source)
        budget_rows = self._repository.budget_rows(self._session, source)
        ar_rows = self._repository.ar_rows(self._session, source)
        period_ids: dict[int, UUID] = {}
        for rows in (operating_rows, financial_rows, budget_rows, ar_rows):
            for row in rows:
                period_ids.setdefault(row.month_key, row.period_id)
        if as_of_month not in period_ids:
            raise ValueError(f"as-of month is unavailable: {as_of_month}")

        actual_values: defaultdict[str, list[PeriodValue]] = defaultdict(list)
        actual_counts: defaultdict[str, list[PeriodValue]] = defaultdict(list)
        for row in operating_rows:
            dimensions = _dimensions(
                organization=row.organization_id,
                customer=row.customer_id,
                customer_segment=row.customer_segment_id,
                logistics_product=row.logistics_product_id,
                region=row.region_id,
            )
            source_values = {
                "orders": row.order_count,
                "fulfilled_units": row.shipment_count,
                "revenue": row.revenue,
                "direct_cost": (
                    row.warehousing_cost
                    + row.transportation_cost
                    + row.other_direct_cost
                ),
            }
            for metric_code, raw_value in source_values.items():
                for grain in project_metric_grains(specs[metric_code], dimensions):
                    actual_values[metric_code].append(
                        _period_value(row.period_id, row.month_key, grain, raw_value)
                    )
                    actual_counts[metric_code].append(
                        _period_value(row.period_id, row.month_key, grain, Decimal("1"))
                    )

        for row in financial_rows:
            dimensions = _dimensions(organization=row.organization_id)
            for metric_code, account_code in _FINANCIAL_ACCOUNTS.items():
                if row.management_account_code != account_code:
                    continue
                for grain in project_metric_grains(specs[metric_code], dimensions):
                    actual_values[metric_code].append(
                        _period_value(row.period_id, row.month_key, grain, row.amount)
                    )
                    actual_counts[metric_code].append(
                        _period_value(row.period_id, row.month_key, grain, Decimal("1"))
                    )

        for row in ar_rows:
            dimensions = _dimensions(
                customer=row.customer_id,
                customer_segment=row.customer_segment_id,
            )
            for grain in project_metric_grains(specs["ar_balance"], dimensions):
                actual_values["ar_balance"].append(
                    _period_value(
                        row.period_id, row.month_key, grain, row.receivable_balance
                    )
                )
                actual_counts["ar_balance"].append(
                    _period_value(row.period_id, row.month_key, grain, Decimal("1"))
                )
            for grain in project_metric_grains(specs["collection_rate"], dimensions):
                actual_values["collection_collected"].append(
                    _period_value(row.period_id, row.month_key, grain, row.collected_amount)
                )
                actual_values["collection_due"].append(
                    _period_value(row.period_id, row.month_key, grain, row.due_amount)
                )
                actual_counts["collection_rate"].append(
                    _period_value(row.period_id, row.month_key, grain, Decimal("1"))
                )

        budget_values: defaultdict[str, list[PeriodValue]] = defaultdict(list)
        budget_counts: defaultdict[str, list[PeriodValue]] = defaultdict(list)
        for row in budget_rows:
            budget_metric_code = _BUDGET_CODES.get(row.metric_code)
            if budget_metric_code is None:
                continue
            dimensions = _dimensions(
                organization=row.organization_id,
                customer_segment=row.customer_segment_id,
                logistics_product=row.logistics_product_id,
            )
            for grain in project_metric_grains(
                specs[budget_metric_code], dimensions, budget=True
            ):
                budget_values[budget_metric_code].append(
                    _period_value(row.period_id, row.month_key, grain, row.amount)
                )
                budget_counts[budget_metric_code].append(
                    _period_value(row.period_id, row.month_key, grain, Decimal("1"))
                )

        windows = metric_windows(tuple(sorted(period_ids)), as_of_month)
        results: list[CalculatedMetricValue] = []
        window_results: dict[
            str, dict[tuple[str, MetricGrain], CalculatedMetricValue]
        ] = {}
        for window in windows:
            if window.comparison_type in _ACTUAL_COMPARISONS:
                values = self._calculate_window(
                    catalog,
                    specs,
                    window,
                    period_ids[as_of_month],
                    actual_values,
                    actual_counts,
                    budget=False,
                )
            elif window.comparison_type in _BUDGET_COMPARISONS:
                values = self._calculate_window(
                    catalog,
                    specs,
                    window,
                    period_ids[as_of_month],
                    budget_values,
                    budget_counts,
                    budget=True,
                )
            else:  # pragma: no cover - exhaustive Literal safeguard
                continue
            results.extend(values)
            window_results[window.comparison_type] = {
                (value.metric_code, value.grain): value for value in values
            }

        results.extend(
            self._comparison_results(
                window_results,
                "actual_month",
                "budget_month",
                "budget_variance_month",
                "budget_variance_month_pct",
            )
        )
        results.extend(
            self._comparison_results(
                window_results,
                "actual_ytd",
                "budget_ytd",
                "budget_variance_ytd",
                "budget_variance_ytd_pct",
            )
        )
        results.extend(
            self._comparison_results(
                window_results,
                "actual_month",
                "prior_year_month",
                "yoy_variance_month",
                "yoy_variance_month_pct",
            )
        )
        results.extend(
            self._comparison_results(
                window_results,
                "actual_ytd",
                "prior_year_ytd",
                "yoy_variance_ytd",
                "yoy_variance_ytd_pct",
            )
        )
        ordered = tuple(sorted(results, key=_result_sort_key))
        definition_hash = metric_catalog_hash(catalog)
        fingerprint = self._fingerprint(definition_hash, ordered)
        return MetricCalculationResult(
            source=source,
            as_of_period_id=period_ids[as_of_month],
            definition_set_hash=definition_hash,
            values=ordered,
            fingerprint=fingerprint,
        )

    def _calculate_window(
        self,
        catalog: MetricCatalog,
        specs: Mapping[str, MetricSpec],
        window: MetricWindow,
        as_of_period_id: UUID,
        raw_values: Mapping[str, list[PeriodValue]],
        raw_counts: Mapping[str, list[PeriodValue]],
        *,
        budget: bool,
    ) -> tuple[CalculatedMetricValue, ...]:
        values: dict[tuple[str, MetricGrain], CalculatedMetricValue] = {}
        direct_codes = (
            ("revenue", "direct_cost", "operating_profit", "operating_cash_flow")
            if budget
            else (
                "orders",
                "fulfilled_units",
                "revenue",
                "direct_cost",
                "operating_profit",
                "ar_balance",
                "operating_cash_flow",
            )
        )
        for metric_code in direct_codes:
            spec = specs[metric_code]
            aggregator = (
                aggregate_closing_balance
                if spec.aggregation == "closing_balance"
                else aggregate_flow
            )
            aggregated = aggregator(raw_values.get(metric_code, ()), window.included_months)
            counts = aggregator(raw_counts.get(metric_code, ()), window.included_months)
            for grain, raw_value in aggregated.items():
                calculated = calculate_amount(
                    metric_code, raw_value, output_scale=spec.output_scale
                )
                values[(metric_code, grain)] = CalculatedMetricValue(
                    metric_code=metric_code,
                    metric_version=spec.version,
                    comparison_type=window.comparison_type,
                    period_id=as_of_period_id,
                    grain=grain,
                    exact_value=calculated.exact_value,
                    persisted_value=calculated.persisted_value,
                    dependency_values=(),
                    source_fact_count=int(counts.get(grain, Decimal("0"))),
                )

        if not budget:
            collected = aggregate_flow(
                raw_values.get("collection_collected", ()), window.included_months
            )
            due = aggregate_flow(raw_values.get("collection_due", ()), window.included_months)
            counts = aggregate_flow(
                raw_counts.get("collection_rate", ()), window.included_months
            )
            spec = specs["collection_rate"]
            for grain in sorted(set(collected) & set(due), key=lambda item: item.sort_key):
                calculated = calculate_ratio(
                    "collection_rate",
                    collected[grain],
                    due[grain],
                    output_scale=spec.output_scale,
                )
                values[("collection_rate", grain)] = CalculatedMetricValue(
                    metric_code="collection_rate",
                    metric_version=spec.version,
                    comparison_type=window.comparison_type,
                    period_id=as_of_period_id,
                    grain=grain,
                    exact_value=calculated.exact_value,
                    persisted_value=calculated.persisted_value,
                    dependency_values=(
                        ("collected_amount", collected[grain]),
                        ("due_amount", due[grain]),
                    ),
                    source_fact_count=int(counts.get(grain, Decimal("0"))),
                )

        for metric_code in topological_metric_order(catalog):
            spec = specs[metric_code]
            if not spec.dependencies or metric_code == "dso":
                continue
            allowed = spec.budget_dimension_sets if budget else spec.allowed_dimension_sets
            if budget and not allowed:
                continue
            candidate_grains = {
                grain
                for code, grain in values
                if code == spec.dependencies[0] and grain.dimensions in allowed
            }
            for grain in sorted(candidate_grains, key=lambda item: item.sort_key):
                dependencies = {
                    dependency: values[(dependency, grain)].exact_value
                    for dependency in spec.dependencies
                    if (dependency, grain) in values
                }
                if len(dependencies) != len(spec.dependencies):
                    continue
                calculated = evaluate_derived_metric(spec, dependencies)
                dependency_values = tuple(
                    (dependency, dependencies[dependency])
                    for dependency in spec.dependencies
                )
                source_count = sum(
                    values[(dependency, grain)].source_fact_count
                    for dependency in spec.dependencies
                )
                values[(metric_code, grain)] = CalculatedMetricValue(
                    metric_code=metric_code,
                    metric_version=spec.version,
                    comparison_type=window.comparison_type,
                    period_id=as_of_period_id,
                    grain=grain,
                    exact_value=calculated.exact_value,
                    persisted_value=calculated.persisted_value,
                    dependency_values=dependency_values,
                    source_fact_count=source_count,
                )

        if not budget:
            spec = specs["dso"]
            ar_values = {
                grain: value
                for (code, grain), value in values.items()
                if code == "ar_balance"
            }
            revenue = aggregate_flow(
                raw_values.get("revenue", ()), _trailing_months(_ending_month(window))
            )
            revenue_counts = aggregate_flow(
                raw_counts.get("revenue", ()), _trailing_months(_ending_month(window))
            )
            for grain in sorted(set(ar_values) & set(revenue), key=lambda item: item.sort_key):
                ar_value = ar_values[grain]
                calculated = evaluate_derived_metric(
                    spec,
                    {"ar_balance": ar_value.exact_value, "revenue": revenue[grain]},
                )
                values[("dso", grain)] = CalculatedMetricValue(
                    metric_code="dso",
                    metric_version=spec.version,
                    comparison_type=window.comparison_type,
                    period_id=as_of_period_id,
                    grain=grain,
                    exact_value=calculated.exact_value,
                    persisted_value=calculated.persisted_value,
                    dependency_values=(
                        ("ar_balance", ar_value.exact_value),
                        ("revenue", revenue[grain]),
                    ),
                    source_fact_count=(
                        ar_value.source_fact_count
                        + int(revenue_counts.get(grain, Decimal("0")))
                    ),
                )
        return tuple(values.values())

    def _comparison_results(
        self,
        results: Mapping[str, Mapping[tuple[str, MetricGrain], CalculatedMetricValue]],
        actual_type: str,
        comparison_type: str,
        variance_type: ComparisonType,
        percent_type: ComparisonType,
    ) -> tuple[CalculatedMetricValue, ...]:
        actuals = results.get(actual_type, {})
        comparisons = results.get(comparison_type, {})
        common = sorted(
            set(actuals) & set(comparisons),
            key=lambda item: (item[0], item[1].sort_key),
        )
        output: list[CalculatedMetricValue] = []
        for key in common:
            actual = actuals[key]
            comparison = comparisons[key]
            if actual.metric_code in {
                "gross_margin",
                "fulfillment_cost_rate",
                "collection_rate",
                "cash_conversion",
            }:
                calculated_variance = ratio_point_variance(
                    actual.metric_code, actual.exact_value, comparison.exact_value
                )
            else:
                exponent = actual.exact_value.as_tuple().exponent
                if not isinstance(exponent, int):  # pragma: no cover - finite values only
                    raise ValueError("metric comparisons require finite decimals")
                calculated_variance = calculate_amount(
                    actual.metric_code,
                    variance(actual.exact_value, comparison.exact_value),
                    output_scale=-exponent,
                )
            dependencies = (
                (actual_type, actual.exact_value),
                (comparison_type, comparison.exact_value),
            )
            output.append(
                CalculatedMetricValue(
                    metric_code=actual.metric_code,
                    metric_version=actual.metric_version,
                    comparison_type=variance_type,
                    period_id=actual.period_id,
                    grain=actual.grain,
                    exact_value=calculated_variance.exact_value,
                    persisted_value=calculated_variance.persisted_value,
                    dependency_values=dependencies,
                    source_fact_count=actual.source_fact_count
                    + comparison.source_fact_count,
                )
            )
            calculated_pct = variance_pct(
                actual.metric_code, actual.exact_value, comparison.exact_value
            )
            output.append(
                CalculatedMetricValue(
                    metric_code=actual.metric_code,
                    metric_version=actual.metric_version,
                    comparison_type=percent_type,
                    period_id=actual.period_id,
                    grain=actual.grain,
                    exact_value=calculated_pct.exact_value,
                    persisted_value=calculated_pct.persisted_value,
                    dependency_values=dependencies,
                    source_fact_count=actual.source_fact_count
                    + comparison.source_fact_count,
                )
            )
        return tuple(output)

    @staticmethod
    def _fingerprint(
        definition_hash: str, values: Iterable[CalculatedMetricValue]
    ) -> str:
        payload = {
            "definition_set_hash": definition_hash,
            "values": [
                {
                    "comparison_type": value.comparison_type,
                    "dependencies": [
                        [code, str(dependency)]
                        for code, dependency in value.dependency_values
                    ],
                    "exact_value": str(value.exact_value),
                    "grain": [
                        str(identifier) if identifier is not None else None
                        for identifier in (
                            value.grain.organization_id,
                            value.grain.customer_id,
                            value.grain.customer_segment_id,
                            value.grain.logistics_product_id,
                            value.grain.region_id,
                        )
                    ],
                    "metric_code": value.metric_code,
                    "metric_version": value.metric_version,
                    "period_id": str(value.period_id),
                    "source_fact_count": value.source_fact_count,
                }
                for value in values
            ],
        }
        serialized = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
