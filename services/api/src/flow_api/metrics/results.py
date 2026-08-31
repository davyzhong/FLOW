from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from flow_api.metrics.grain import MetricGrain
from flow_api.metrics.source_rows import PublishedMetricSource
from flow_api.metrics.windows import ComparisonType


@dataclass(frozen=True, slots=True)
class CalculatedMetricValue:
    metric_code: str
    metric_version: int
    comparison_type: ComparisonType
    period_id: UUID
    grain: MetricGrain
    exact_value: Decimal
    persisted_value: Decimal
    dependency_values: tuple[tuple[str, Decimal], ...]
    source_fact_count: int


@dataclass(frozen=True, slots=True)
class MetricCalculationResult:
    source: PublishedMetricSource
    as_of_period_id: UUID
    definition_set_hash: str
    values: tuple[CalculatedMetricValue, ...]
    fingerprint: str
