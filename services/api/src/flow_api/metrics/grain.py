from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from flow_api.metrics.models import DimensionName, MetricSpec

DIMENSION_FIELDS: tuple[tuple[DimensionName, str], ...] = (
    ("organization", "organization_id"),
    ("customer", "customer_id"),
    ("customer_segment", "customer_segment_id"),
    ("logistics_product", "logistics_product_id"),
    ("region", "region_id"),
)


class UnsupportedMetricGrainError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MetricGrain:
    organization_id: UUID | None = None
    customer_id: UUID | None = None
    customer_segment_id: UUID | None = None
    logistics_product_id: UUID | None = None
    region_id: UUID | None = None

    @property
    def dimensions(self) -> tuple[DimensionName, ...]:
        return tuple(
            dimension
            for dimension, field_name in DIMENSION_FIELDS
            if getattr(self, field_name) is not None
        )

    @property
    def sort_key(self) -> tuple[str, ...]:
        return tuple(
            str(getattr(self, field_name) or "") for _, field_name in DIMENSION_FIELDS
        )


def validate_grain(metric: MetricSpec, grain: MetricGrain, *, budget: bool = False) -> None:
    allowed = metric.budget_dimension_sets if budget else metric.allowed_dimension_sets
    if grain.dimensions not in allowed:
        raise UnsupportedMetricGrainError(
            f"{metric.metric_code} does not support grain {grain.dimensions}"
        )


def project_metric_grains(
    metric: MetricSpec,
    dimension_values: Mapping[DimensionName, UUID | None],
    *,
    budget: bool = False,
) -> tuple[MetricGrain, ...]:
    dimension_sets = metric.budget_dimension_sets if budget else metric.allowed_dimension_sets
    grains: set[MetricGrain] = set()
    for dimension_set in dimension_sets:
        if any(dimension_values.get(dimension) is None for dimension in dimension_set):
            continue
        values = {
            field_name: dimension_values.get(dimension) if dimension in dimension_set else None
            for dimension, field_name in DIMENSION_FIELDS
        }
        grain = MetricGrain(**values)
        validate_grain(metric, grain, budget=budget)
        grains.add(grain)
    return tuple(sorted(grains, key=lambda grain: grain.sort_key))
