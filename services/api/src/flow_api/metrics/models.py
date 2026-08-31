from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

MetricAggregation = Literal["sum", "closing_balance", "ratio"]
MetricTimeBehavior = Literal["flow", "balance"]
MetricUnit = Literal["order", "unit", "CNY", "CNY/order", "ratio", "day"]
DimensionName = Literal[
    "organization",
    "customer",
    "customer_segment",
    "logistics_product",
    "region",
]


class MetricSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_code: str
    version: int
    name: str
    business_definition: str
    formula: str
    dependencies: tuple[str, ...]
    aggregation: MetricAggregation
    time_behavior: MetricTimeBehavior
    unit: MetricUnit
    output_scale: int
    allowed_dimension_sets: tuple[tuple[DimensionName, ...], ...]
    budget_dimension_sets: tuple[tuple[DimensionName, ...], ...] = ()

    @model_validator(mode="after")
    def validate_definition(self) -> MetricSpec:
        if not self.metric_code or not self.metric_code.isidentifier():
            raise ValueError("metric_code must be a non-empty identifier")
        if self.version < 1:
            raise ValueError("metric version must be positive")
        if self.output_scale not in {4, 6}:
            raise ValueError("metric output_scale must be 4 or 6")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError(f"{self.metric_code} has duplicate dependencies")
        for dimensions in (*self.allowed_dimension_sets, *self.budget_dimension_sets):
            if len(dimensions) != len(set(dimensions)):
                raise ValueError(f"{self.metric_code} has a duplicate dimension")
            if "customer" in dimensions and "customer_segment" in dimensions:
                raise ValueError("customer and customer_segment cannot share a metric grain")
        if not set(self.budget_dimension_sets).issubset(set(self.allowed_dimension_sets)):
            raise ValueError("budget dimensions must also be allowed actual dimensions")
        return self


class MetricCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    definition_set_id: str
    engine_version: str
    metrics: tuple[MetricSpec, ...]

    @model_validator(mode="after")
    def validate_graph(self) -> MetricCatalog:
        identities = [(metric.metric_code, metric.version) for metric in self.metrics]
        if len(identities) != len(set(identities)):
            raise ValueError("metric identities must be unique")
        codes = {metric.metric_code for metric in self.metrics}
        if len(codes) != len(self.metrics):
            raise ValueError("one metric code cannot have multiple active versions")
        for metric in self.metrics:
            unknown = set(metric.dependencies) - codes
            if unknown:
                raise ValueError(
                    f"{metric.metric_code} has unknown dependencies: {sorted(unknown)}"
                )
            if metric.metric_code in metric.dependencies:
                raise ValueError(f"{metric.metric_code} cannot depend on itself")
        completed: set[str] = set()
        remaining = set(codes)
        while remaining:
            ready = {
                metric.metric_code
                for metric in self.metrics
                if metric.metric_code in remaining and set(metric.dependencies) <= completed
            }
            if not ready:
                raise ValueError("metric dependency graph contains a cycle")
            completed.update(ready)
            remaining.difference_update(ready)
        return self
