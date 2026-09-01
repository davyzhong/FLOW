from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _reject_float(value: object) -> object:
    if isinstance(value, float):
        raise ValueError("float values are forbidden; use Decimal or decimal strings")
    return value


StrictDecimal = Annotated[Decimal, BeforeValidator(_reject_float)]
DashboardState = Literal["ready", "empty", "error", "degraded", "stale"]
ValueStatus = Literal["available", "unavailable", "degraded"]
SemanticDirection = Literal["positive", "negative", "warning", "neutral"]
PeriodView = Literal["month", "ytd"]
DimensionName = Literal[
    "organization", "customer_segment", "logistics_product", "region"
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DashboardValue(FrozenModel):
    status: ValueStatus
    exact_value: StrictDecimal | None = None
    display_value: str
    semantic_direction: SemanticDirection
    unavailable_code: str | None = None
    unavailable_message: str | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> DashboardValue:
        if self.status == "available":
            if self.exact_value is None or not self.display_value:
                raise ValueError("available value requires exact_value and display_value")
            if self.unavailable_code is not None or self.unavailable_message is not None:
                raise ValueError("available value cannot expose unavailable details")
        else:
            if self.exact_value is not None:
                raise ValueError("unavailable value cannot expose exact_value")
            if not self.unavailable_code or not self.unavailable_message:
                raise ValueError("unavailable value requires code and message")
        return self


class DashboardContext(FrozenModel):
    batch_id: UUID
    import_version_id: UUID
    metric_snapshot_id: UUID
    analysis_run_id: UUID
    as_of_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    metric_definition_set_id: str
    metric_definition_set_hash: str = Field(min_length=64, max_length=64)
    metric_engine_version: str
    analysis_policy_id: str
    analysis_policy_hash: str = Field(min_length=64, max_length=64)
    analysis_engine_version: str
    generated_at: datetime


class DimensionOption(FrozenModel):
    id: UUID
    code: str
    name: str


class FilterDimension(FrozenModel):
    dimension: DimensionName
    label: str
    options: tuple[DimensionOption, ...]


class FilterOptions(FrozenModel):
    dimensions: tuple[FilterDimension, ...]
    supported_combinations: tuple[tuple[DimensionName, ...], ...]


class ActiveFilters(FrozenModel):
    period_view: PeriodView
    organization_id: UUID | None = None
    customer_segment_id: UUID | None = None
    logistics_product_id: UUID | None = None
    region_id: UUID | None = None
    is_total_scope: bool

    @model_validator(mode="after")
    def validate_total_scope(self) -> ActiveFilters:
        has_dimension = any(
            value is not None
            for value in (
                self.organization_id,
                self.customer_segment_id,
                self.logistics_product_id,
                self.region_id,
            )
        )
        if self.is_total_scope == has_dimension:
            raise ValueError("is_total_scope must match dimension selections")
        return self


class DataStatus(FrozenModel):
    batch_status: Literal["draft", "validating", "blocked", "ready", "published"]
    import_status: Literal["draft", "validating", "blocked", "ready", "published"]
    quality_status: Literal["passed", "warning", "blocked"]
    blocking_issue_count: int = Field(ge=0)
    warning_issue_count: int = Field(ge=0)
    acknowledged_warning_count: int = Field(ge=0)
    reconciliation_status: Literal["passed", "failed", "not_available"]
    metric_snapshot_status: Literal["published"]
    analysis_run_status: Literal["published"]
    freshness_status: Literal["fresh", "stale"]


class MetricCard(FrozenModel):
    metric_code: Literal[
        "orders",
        "revenue",
        "revenue_per_order",
        "gross_margin",
        "fulfillment_cost_rate",
        "operating_profit",
        "ar_balance",
        "operating_cash_flow",
    ]
    title: str
    category: str
    unit: Literal["order", "CNY", "CNY/order", "ratio", "day"]
    primary: DashboardValue
    budget: DashboardValue
    yoy: DashboardValue
    ytd_budget: DashboardValue
    companion: DashboardValue | None


class TrendPoint(FrozenModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    metric_snapshot_id: UUID
    revenue: DashboardValue
    operating_profit: DashboardValue
    gross_margin: DashboardValue
    operating_cash_flow: DashboardValue


class TrendPanel(FrozenModel):
    status: Literal["complete", "partial_series", "degraded"]
    coverage_count: int = Field(ge=0, le=12)
    expected_count: Literal[12]
    missing_months: tuple[str, ...]
    points: tuple[TrendPoint, ...]
    degradation_message: str | None = None

    @model_validator(mode="after")
    def validate_coverage(self) -> TrendPanel:
        if self.coverage_count != len(self.points):
            raise ValueError("trend coverage_count must match points")
        if self.status == "complete" and (
            self.coverage_count != self.expected_count or self.missing_months
        ):
            raise ValueError("complete trend requires all expected points")
        return self


class BridgeDriver(FrozenModel):
    driver_code: str
    label: str
    contribution: DashboardValue


class ProfitBridge(FrozenModel):
    status: Literal["complete", "degraded", "not_applicable"]
    comparison_basis: Literal["prior_year", "budget"]
    impact: DashboardValue
    reconciliation_status: Literal["passed", "failed", "not_applicable"]
    reconciliation_difference: StrictDecimal
    drivers: tuple[BridgeDriver, ...]
    degradation_message: str | None = None


class FindingItem(FrozenModel):
    finding_id: UUID
    finding_type: str
    title: str
    impact: DashboardValue
    total_score: StrictDecimal = Field(ge=0, le=100)
    comparison_basis: Literal["prior_year", "budget"]
    evidence_verified: int = Field(ge=0)
    evidence_total: int = Field(ge=0)
    scope: Literal["global"]
    investigation_path: str = Field(pattern=r"^/investigations/")

    @model_validator(mode="after")
    def validate_evidence_counts(self) -> FindingItem:
        if self.evidence_verified > self.evidence_total:
            raise ValueError("verified evidence cannot exceed total evidence")
        return self


class ProductRow(FrozenModel):
    logistics_product_id: UUID
    code: str
    name: str
    revenue: DashboardValue
    orders: DashboardValue
    gross_margin: DashboardValue
    fulfillment_cost_rate: DashboardValue
    revenue_comparison: DashboardValue
    orders_comparison: DashboardValue
    gross_margin_comparison: DashboardValue


class ProductPerformance(FrozenModel):
    status: Literal["complete", "degraded"]
    comparison_label: Literal["预算", "同比", "不可用"]
    rows: tuple[ProductRow, ...]
    degradation_message: str | None = None


class MatrixCell(FrozenModel):
    customer_segment_id: UUID
    logistics_product_id: UUID
    actual_margin: DashboardValue
    comparison: DashboardValue


class MarginMatrix(FrozenModel):
    status: Literal["complete", "degraded"]
    comparison_label: Literal["预算", "同比", "不可用"]
    rows: tuple[DimensionOption, ...]
    columns: tuple[DimensionOption, ...]
    cells: tuple[MatrixCell, ...]
    degradation_message: str | None = None


class Highlight(FrozenModel):
    finding_id: UUID
    title: str
    impact_display: str


class DashboardDegradation(FrozenModel):
    panel: Literal[
        "metric_cards", "trends", "profit_bridge", "findings", "product_table", "margin_matrix"
    ]
    code: str
    message: str


class DashboardOverview(FrozenModel):
    state: DashboardState
    context: DashboardContext
    filter_options: FilterOptions
    active_filters: ActiveFilters
    data_status: DataStatus
    metric_cards: tuple[MetricCard, ...]
    trends: TrendPanel
    profit_bridge: ProfitBridge
    findings: tuple[FindingItem, ...]
    product_table: ProductPerformance
    margin_matrix: MarginMatrix
    highlights: tuple[Highlight, ...]
    degradations: tuple[DashboardDegradation, ...]

    @model_validator(mode="after")
    def validate_metric_cards(self) -> DashboardOverview:
        expected = (
            "orders",
            "revenue",
            "revenue_per_order",
            "gross_margin",
            "fulfillment_cost_rate",
            "operating_profit",
            "ar_balance",
            "operating_cash_flow",
        )
        actual = tuple(card.metric_code for card in self.metric_cards)
        if actual != expected:
            raise ValueError("dashboard requires exactly eight metric cards in stable order")
        return self


__all__ = [
    "ActiveFilters",
    "BridgeDriver",
    "DashboardContext",
    "DashboardDegradation",
    "DashboardOverview",
    "DashboardState",
    "DashboardValue",
    "DataStatus",
    "DimensionName",
    "DimensionOption",
    "FilterDimension",
    "FilterOptions",
    "FindingItem",
    "FrozenModel",
    "Highlight",
    "MarginMatrix",
    "MatrixCell",
    "MetricCard",
    "PeriodView",
    "ProductPerformance",
    "ProductRow",
    "ProfitBridge",
    "StrictDecimal",
    "TrendPanel",
    "TrendPoint",
]
