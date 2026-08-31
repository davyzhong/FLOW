from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PublishedMetricSource:
    batch_id: UUID
    import_version_id: UUID
    analysis_start_month: int
    analysis_end_month: int
    comparison_start_month: int
    comparison_end_month: int
    actual_scenario_code: str
    budget_scenario_code: str


@dataclass(frozen=True, slots=True)
class OperatingSourceRow:
    fact_id: UUID
    import_version_id: UUID
    period_id: UUID
    month_key: int
    organization_id: UUID
    customer_id: UUID
    customer_segment_id: UUID | None
    logistics_product_id: UUID
    region_id: UUID
    order_count: Decimal
    shipment_count: Decimal
    revenue: Decimal
    warehousing_cost: Decimal
    transportation_cost: Decimal
    other_direct_cost: Decimal


@dataclass(frozen=True, slots=True)
class FinancialSourceRow:
    fact_id: UUID
    import_version_id: UUID
    period_id: UUID
    month_key: int
    organization_id: UUID
    management_account_id: UUID
    management_account_code: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class BudgetSourceRow:
    fact_id: UUID
    import_version_id: UUID
    period_id: UUID
    month_key: int
    organization_id: UUID
    customer_segment_id: UUID | None
    logistics_product_id: UUID | None
    management_account_id: UUID | None
    scenario_version_id: UUID
    scenario_code: str
    metric_code: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ArSourceRow:
    fact_id: UUID
    import_version_id: UUID
    period_id: UUID
    month_key: int
    customer_id: UUID
    customer_segment_id: UUID | None
    invoice_number: str | None
    aging_bucket: str | None
    receivable_balance: Decimal
    due_amount: Decimal
    overdue_amount: Decimal
    collected_amount: Decimal
