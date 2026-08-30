from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CanonicalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class BatchRecord(CanonicalRecord):
    batch_code: str
    contract_version: str
    analysis_start_month: str
    analysis_end_month: str
    comparison_start_month: str
    comparison_end_month: str
    currency: str
    actual_scenario_code: str
    budget_scenario_code: str
    budget_version_label: str
    generated_at: datetime


class PeriodRecord(CanonicalRecord):
    month_key: str
    year: int
    quarter: int = Field(ge=1, le=4)
    month: int = Field(ge=1, le=12)
    window: str


class OrganizationRecord(CanonicalRecord):
    code: str
    name: str
    level: str
    parent_code: str | None = None


class CustomerSegmentRecord(CanonicalRecord):
    code: str
    name: str


class CustomerRecord(CanonicalRecord):
    code: str
    name: str
    industry: str | None = None
    tier: str | None = None
    credit_term_days: int | None = Field(default=None, ge=0)
    segment_code: str


class LogisticsProductRecord(CanonicalRecord):
    code: str
    name: str
    level: str
    parent_code: str | None = None


class RegionRecord(CanonicalRecord):
    code: str
    name: str
    province: str | None = None
    city: str | None = None
    parent_code: str | None = None


class ManagementAccountRecord(CanonicalRecord):
    code: str
    name: str
    category: str
    financial_account_code: str | None = None
    parent_code: str | None = None


class ScenarioVersionRecord(CanonicalRecord):
    code: str
    name: str
    scenario_type: str
    version_label: str | None = None


class OperatingActualRecord(CanonicalRecord):
    record_id: str
    month_key: str
    organization_code: str
    customer_code: str
    logistics_product_code: str
    region_code: str
    order_count: Decimal
    shipment_count: Decimal
    revenue: Decimal
    warehousing_cost: Decimal
    transportation_cost: Decimal
    other_direct_cost: Decimal


class FinancialActualRecord(CanonicalRecord):
    record_id: str
    month_key: str
    organization_code: str
    management_account_code: str
    amount: Decimal


class MonthlyBudgetRecord(CanonicalRecord):
    record_id: str
    month_key: str
    organization_code: str
    customer_segment_code: str | None = None
    logistics_product_code: str | None = None
    management_account_code: str | None = None
    scenario_code: str
    metric_code: str
    amount: Decimal


class ArCollectionRecord(CanonicalRecord):
    record_id: str
    month_key: str
    customer_code: str
    invoice_number: str | None = None
    aging_bucket: str | None = None
    receivable_balance: Decimal
    due_amount: Decimal
    overdue_amount: Decimal
    collected_amount: Decimal


class CanonicalPackage(CanonicalRecord):
    batch: BatchRecord
    periods: tuple[PeriodRecord, ...]
    organizations: tuple[OrganizationRecord, ...]
    customer_segments: tuple[CustomerSegmentRecord, ...]
    customers: tuple[CustomerRecord, ...]
    logistics_products: tuple[LogisticsProductRecord, ...]
    regions: tuple[RegionRecord, ...]
    management_accounts: tuple[ManagementAccountRecord, ...]
    scenario_versions: tuple[ScenarioVersionRecord, ...]
    operating_actuals: tuple[OperatingActualRecord, ...]
    financial_actuals: tuple[FinancialActualRecord, ...]
    monthly_budgets: tuple[MonthlyBudgetRecord, ...]
    ar_collections: tuple[ArCollectionRecord, ...]
