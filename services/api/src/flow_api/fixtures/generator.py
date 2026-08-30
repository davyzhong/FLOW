from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from pydantic import BaseModel

from flow_api.data_contract.records import (
    ArCollectionRecord,
    BatchRecord,
    CanonicalPackage,
    CustomerRecord,
    CustomerSegmentRecord,
    FinancialActualRecord,
    LogisticsProductRecord,
    ManagementAccountRecord,
    MonthlyBudgetRecord,
    OperatingActualRecord,
    OrganizationRecord,
    PeriodRecord,
    RegionRecord,
    ScenarioVersionRecord,
)

FLOW_FIXTURE_NAMESPACE = UUID("fd9e0e69-0c9c-5c6e-bdf5-38f386c77b10")
AMOUNT_QUANTUM = Decimal("0.0001")


def _decimal(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(AMOUNT_QUANTUM, rounding=ROUND_HALF_UP)


def _record_id(prefix: str, *parts: str) -> str:
    return str(uuid5(FLOW_FIXTURE_NAMESPACE, ":".join((prefix, *parts))))


def _month_range(start_year: int, start_month: int, length: int) -> list[str]:
    months: list[str] = []
    year = start_year
    month = start_month
    for _ in range(length):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def _build_periods() -> tuple[PeriodRecord, ...]:
    comparison = _month_range(2024, 9, 12)
    analysis = _month_range(2025, 9, 12)
    rows = []
    for month_key in comparison + analysis:
        year, month = (int(value) for value in month_key.split("-"))
        rows.append(
            PeriodRecord(
                month_key=month_key,
                year=year,
                quarter=(month - 1) // 3 + 1,
                month=month,
                window="comparison" if month_key in comparison else "analysis",
            )
        )
    return tuple(rows)


def _build_dimensions() -> tuple[
    tuple[OrganizationRecord, ...],
    tuple[CustomerSegmentRecord, ...],
    tuple[CustomerRecord, ...],
    tuple[LogisticsProductRecord, ...],
    tuple[RegionRecord, ...],
    tuple[ManagementAccountRecord, ...],
    tuple[ScenarioVersionRecord, ...],
]:
    organizations = (
        OrganizationRecord(code="FLOW_GROUP", name="FLOW 供应链集团", level="group"),
        OrganizationRecord(
            code="ORG_NORTH", name="北方经营中心", level="business_unit", parent_code="FLOW_GROUP"
        ),
        OrganizationRecord(
            code="ORG_SOUTH", name="南方经营中心", level="business_unit", parent_code="FLOW_GROUP"
        ),
    )
    segments = (
        CustomerSegmentRecord(code="KEY_ACCOUNT", name="集团大客户"),
        CustomerSegmentRecord(code="DOMESTIC", name="国内营销客户"),
    )
    customers = tuple(
        CustomerRecord(
            code=f"CUST_KEY_{index:02d}",
            name=f"集团客户{index:02d}",
            industry=("平台电商", "消费电子", "汽车零部件", "医药健康")[(index - 1) % 4],
            tier="A" if index <= 4 else "B",
            credit_term_days=60 if index <= 4 else 45,
            segment_code="KEY_ACCOUNT",
        )
        for index in range(1, 9)
    ) + tuple(
        CustomerRecord(
            code=f"CUST_DOM_{index:02d}",
            name=f"国内客户{index:02d}",
            industry=("食品", "家居", "美妆", "服饰")[(index - 1) % 4],
            tier="B" if index <= 4 else "C",
            credit_term_days=30,
            segment_code="DOMESTIC",
        )
        for index in range(1, 9)
    )
    products = (
        LogisticsProductRecord(code="B2C", name="国内 B2C 配送", level="service"),
        LogisticsProductRecord(code="B2B", name="国内 B2B 配送", level="service"),
        LogisticsProductRecord(code="WAREHOUSE", name="仓配一体", level="service"),
        LogisticsProductRecord(code="CROSS_BORDER", name="跨境供应链", level="service"),
        LogisticsProductRecord(code="COLD_CHAIN", name="冷链物流", level="service"),
        LogisticsProductRecord(code="REVERSE", name="逆向物流", level="service"),
        LogisticsProductRecord(code="M2C", name="产地直发 M2C", level="service"),
        LogisticsProductRecord(code="SAME_DAY", name="同城即时配", level="service"),
    )
    regions = (
        RegionRecord(code="REGION_NORTH", name="华北", province="北京市", city="北京市"),
        RegionRecord(code="REGION_EAST", name="华东", province="上海市", city="上海市"),
        RegionRecord(code="REGION_SOUTH", name="华南", province="广东省", city="广州市"),
        RegionRecord(code="REGION_WEST", name="西部", province="四川省", city="成都市"),
    )
    accounts = (
        ManagementAccountRecord(code="REVENUE", name="营业收入", category="revenue"),
        ManagementAccountRecord(
            code="WAREHOUSING_COST", name="仓储直接成本", category="direct_cost"
        ),
        ManagementAccountRecord(
            code="TRANSPORTATION_COST", name="运输直接成本", category="direct_cost"
        ),
        ManagementAccountRecord(
            code="OTHER_DIRECT_COST", name="其他直接成本", category="direct_cost"
        ),
        ManagementAccountRecord(code="GROSS_PROFIT", name="毛利", category="operating_profit"),
        ManagementAccountRecord(
            code="OPERATING_EXPENSE", name="期间费用", category="operating_expense"
        ),
        ManagementAccountRecord(
            code="OPERATING_PROFIT", name="经营利润", category="operating_profit"
        ),
        ManagementAccountRecord(
            code="OPERATING_CASH_FLOW", name="经营现金流", category="cash_flow"
        ),
        ManagementAccountRecord(code="AR_BALANCE", name="应收账款余额", category="working_capital"),
    )
    scenarios = (
        ScenarioVersionRecord(code="ACTUAL", name="实际", scenario_type="actual"),
        ScenarioVersionRecord(
            code="BUDGET_FY26_V1",
            name="FY26 月度预算",
            scenario_type="budget",
            version_label="FY26 V1",
        ),
    )
    return organizations, segments, customers, products, regions, accounts, scenarios


def _customer_assignment(customer: CustomerRecord) -> tuple[str, str]:
    index = int(customer.code.rsplit("_", maxsplit=1)[1])
    organization = "ORG_NORTH" if index % 2 else "ORG_SOUTH"
    region_codes = ("REGION_NORTH", "REGION_EAST", "REGION_SOUTH", "REGION_WEST")
    return organization, region_codes[(index - 1) % len(region_codes)]


def _build_operating_actuals(
    periods: tuple[PeriodRecord, ...],
    customers: tuple[CustomerRecord, ...],
    products: tuple[LogisticsProductRecord, ...],
) -> tuple[OperatingActualRecord, ...]:
    product_weights = tuple(
        Decimal(value) for value in ("0.20", "0.16", "0.15", "0.12", "0.10", "0.08", "0.11", "0.08")
    )
    price_per_order = tuple(
        Decimal(value) for value in ("98", "125", "148", "210", "185", "92", "112", "82")
    )
    pieces_per_order = tuple(
        Decimal(value) for value in ("2.4", "5.8", "4.2", "3.1", "2.0", "1.6", "3.8", "1.3")
    )
    seasonality = tuple(
        Decimal(value)
        for value in (
            "0.92",
            "0.98",
            "1.08",
            "1.22",
            "0.88",
            "0.91",
            "0.96",
            "1.00",
            "1.03",
            "1.06",
            "1.10",
            "1.16",
        )
    )
    rows: list[OperatingActualRecord] = []
    for period_index, period in enumerate(periods):
        analysis_period = period.window == "analysis"
        matched_month_index = period_index % 12
        final_quarter = analysis_period and matched_month_index >= 9
        for customer_index, customer in enumerate(customers, start=1):
            organization_code, region_code = _customer_assignment(customer)
            base_orders = (
                Decimal("1120") if customer.segment_code == "KEY_ACCOUNT" else Decimal("760")
            )
            customer_factor = Decimal("0.86") + Decimal(customer_index % 8) * Decimal("0.035")
            if analysis_period:
                growth = (
                    Decimal("0.94") if customer.segment_code == "KEY_ACCOUNT" else Decimal("1.24")
                )
            else:
                growth = Decimal("1.00")
            for product_index, product in enumerate(products):
                order_count = _decimal(
                    base_orders
                    * customer_factor
                    * seasonality[matched_month_index]
                    * growth
                    * product_weights[product_index]
                )
                shipment_count = _decimal(order_count * pieces_per_order[product_index])
                price_growth = Decimal("1.035") if analysis_period else Decimal("1.00")
                revenue = _decimal(order_count * price_per_order[product_index] * price_growth)
                warehouse_rate = Decimal("0.115") + Decimal(product_index % 3) * Decimal("0.009")
                transport_rate = Decimal("0.455") + Decimal(product_index % 4) * Decimal("0.012")
                if final_quarter:
                    transport_rate += Decimal("0.085")
                warehousing_cost = _decimal(revenue * warehouse_rate)
                transportation_cost = _decimal(revenue * transport_rate)
                other_direct_cost = _decimal(revenue * Decimal("0.042"))
                rows.append(
                    OperatingActualRecord(
                        record_id=_record_id(
                            "operating",
                            period.month_key,
                            organization_code,
                            customer.code,
                            product.code,
                            region_code,
                        ),
                        month_key=period.month_key,
                        organization_code=organization_code,
                        customer_code=customer.code,
                        logistics_product_code=product.code,
                        region_code=region_code,
                        order_count=order_count,
                        shipment_count=shipment_count,
                        revenue=revenue,
                        warehousing_cost=warehousing_cost,
                        transportation_cost=transportation_cost,
                        other_direct_cost=other_direct_cost,
                    )
                )
    return tuple(rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _decimal(sum(values, start=Decimal("0")))


def _build_ar_collections(
    periods: tuple[PeriodRecord, ...],
    customers: tuple[CustomerRecord, ...],
    operating_actuals: tuple[OperatingActualRecord, ...],
) -> tuple[ArCollectionRecord, ...]:
    buckets = ("current", "1-30", "31-60", "61-90", "90+")
    standard_weights = tuple(Decimal(value) for value in ("0.42", "0.27", "0.17", "0.09", "0.05"))
    risk_weights = tuple(Decimal(value) for value in ("0.25", "0.22", "0.20", "0.18", "0.15"))
    rows: list[ArCollectionRecord] = []
    for period_index, period in enumerate(periods):
        final_quarter = period.window == "analysis" and period_index % 12 >= 9
        for customer in customers:
            revenue = _sum_decimal(
                row.revenue
                for row in operating_actuals
                if row.month_key == period.month_key and row.customer_code == customer.code
            )
            term_factor = Decimal(customer.credit_term_days or 30) / Decimal("30")
            at_risk = final_quarter and customer.code in {"CUST_KEY_01", "CUST_KEY_02"}
            balance_factor = term_factor * (Decimal("1.28") if at_risk else Decimal("1.00"))
            balance_total = _decimal(revenue * balance_factor)
            collected_total = _decimal(revenue * (Decimal("0.68") if at_risk else Decimal("0.93")))
            weights = risk_weights if at_risk else standard_weights
            for bucket, weight in zip(buckets, weights, strict=True):
                balance = _decimal(balance_total * weight)
                due = _decimal(balance if bucket != "current" else Decimal("0"))
                overdue = _decimal(balance if bucket in {"31-60", "61-90", "90+"} else Decimal("0"))
                rows.append(
                    ArCollectionRecord(
                        record_id=_record_id("ar", period.month_key, customer.code, bucket),
                        month_key=period.month_key,
                        customer_code=customer.code,
                        aging_bucket=bucket,
                        receivable_balance=balance,
                        due_amount=due,
                        overdue_amount=overdue,
                        collected_amount=_decimal(collected_total * weight),
                    )
                )
    return tuple(rows)


def _build_financial_actuals(
    periods: tuple[PeriodRecord, ...],
    operating_actuals: tuple[OperatingActualRecord, ...],
    ar_collections: tuple[ArCollectionRecord, ...],
) -> tuple[FinancialActualRecord, ...]:
    rows: list[FinancialActualRecord] = []
    organizations = ("ORG_NORTH", "ORG_SOUTH")
    for period_index, period in enumerate(periods):
        final_quarter = period.window == "analysis" and period_index % 12 >= 9
        for organization_code in organizations:
            operating_rows = tuple(
                row
                for row in operating_actuals
                if row.month_key == period.month_key and row.organization_code == organization_code
            )
            customer_codes = {row.customer_code for row in operating_rows}
            revenue = _sum_decimal(row.revenue for row in operating_rows)
            warehousing = _sum_decimal(row.warehousing_cost for row in operating_rows)
            transportation = _sum_decimal(row.transportation_cost for row in operating_rows)
            other_direct = _sum_decimal(row.other_direct_cost for row in operating_rows)
            gross_profit = _decimal(revenue - warehousing - transportation - other_direct)
            operating_expense = _decimal(
                revenue * (Decimal("0.100") if final_quarter else Decimal("0.080"))
            )
            operating_profit = _decimal(gross_profit - operating_expense)
            cash_factor = (
                Decimal("0.55")
                if final_quarter
                else Decimal("0.78")
                if period.window == "analysis"
                else Decimal("0.90")
            )
            operating_cash_flow = _decimal(operating_profit * cash_factor)
            ar_balance = _sum_decimal(
                row.receivable_balance
                for row in ar_collections
                if row.month_key == period.month_key and row.customer_code in customer_codes
            )
            values = {
                "REVENUE": revenue,
                "WAREHOUSING_COST": warehousing,
                "TRANSPORTATION_COST": transportation,
                "OTHER_DIRECT_COST": other_direct,
                "GROSS_PROFIT": gross_profit,
                "OPERATING_EXPENSE": operating_expense,
                "OPERATING_PROFIT": operating_profit,
                "OPERATING_CASH_FLOW": operating_cash_flow,
                "AR_BALANCE": ar_balance,
            }
            for account_code, amount in values.items():
                rows.append(
                    FinancialActualRecord(
                        record_id=_record_id(
                            "financial", period.month_key, organization_code, account_code
                        ),
                        month_key=period.month_key,
                        organization_code=organization_code,
                        management_account_code=account_code,
                        amount=amount,
                    )
                )
    return tuple(rows)


def _build_budgets(
    periods: tuple[PeriodRecord, ...],
    financial_actuals: tuple[FinancialActualRecord, ...],
) -> tuple[MonthlyBudgetRecord, ...]:
    rows: list[MonthlyBudgetRecord] = []
    analysis_periods = tuple(period for period in periods if period.window == "analysis")
    account_for_metric = {
        "REVENUE": "REVENUE",
        "DIRECT_COST": None,
        "OPERATING_EXPENSE": "OPERATING_EXPENSE",
        "OPERATING_PROFIT": "OPERATING_PROFIT",
        "OPERATING_CASH_FLOW": "OPERATING_CASH_FLOW",
    }
    for period in analysis_periods:
        comparison_month = f"{period.year - 1:04d}-{period.month:02d}"
        for organization_code in ("ORG_NORTH", "ORG_SOUTH"):
            prior_revenue = next(
                row.amount
                for row in financial_actuals
                if row.month_key == comparison_month
                and row.organization_code == organization_code
                and row.management_account_code == "REVENUE"
            )
            budget_revenue = _decimal(prior_revenue * Decimal("1.12"))
            direct_cost = _decimal(budget_revenue * Decimal("0.655"))
            operating_expense = _decimal(budget_revenue * Decimal("0.080"))
            operating_profit = _decimal(budget_revenue - direct_cost - operating_expense)
            values = {
                "REVENUE": budget_revenue,
                "DIRECT_COST": direct_cost,
                "OPERATING_EXPENSE": operating_expense,
                "OPERATING_PROFIT": operating_profit,
                "OPERATING_CASH_FLOW": _decimal(operating_profit * Decimal("0.85")),
            }
            for metric_code, amount in values.items():
                rows.append(
                    MonthlyBudgetRecord(
                        record_id=_record_id(
                            "budget", period.month_key, organization_code, metric_code
                        ),
                        month_key=period.month_key,
                        organization_code=organization_code,
                        management_account_code=account_for_metric[metric_code],
                        scenario_code="BUDGET_FY26_V1",
                        metric_code=metric_code,
                        amount=amount,
                    )
                )
    return tuple(rows)


def build_reference_package() -> CanonicalPackage:
    periods = _build_periods()
    (
        organizations,
        segments,
        customers,
        products,
        regions,
        accounts,
        scenarios,
    ) = _build_dimensions()
    operating_actuals = _build_operating_actuals(periods, customers, products)
    ar_collections = _build_ar_collections(periods, customers, operating_actuals)
    financial_actuals = _build_financial_actuals(periods, operating_actuals, ar_collections)
    monthly_budgets = _build_budgets(periods, financial_actuals)
    return CanonicalPackage(
        batch=BatchRecord(
            batch_code="FLOW_REFERENCE_2026_08",
            contract_version="flow.excel.v1",
            analysis_start_month="2025-09",
            analysis_end_month="2026-08",
            comparison_start_month="2024-09",
            comparison_end_month="2025-08",
            currency="CNY",
            actual_scenario_code="ACTUAL",
            budget_scenario_code="BUDGET_FY26_V1",
            budget_version_label="FY26 V1",
            generated_at=datetime(2026, 8, 30, 0, 0, tzinfo=UTC),
        ),
        periods=periods,
        organizations=organizations,
        customer_segments=segments,
        customers=customers,
        logistics_products=products,
        regions=regions,
        management_accounts=accounts,
        scenario_versions=scenarios,
        operating_actuals=operating_actuals,
        financial_actuals=financial_actuals,
        monthly_budgets=monthly_budgets,
        ar_collections=ar_collections,
    )


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, ".4f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(nested) for nested in value]
    return value


def _write_jsonl(path: Path, records: Iterable[BaseModel]) -> tuple[int, str]:
    lines = [
        json.dumps(
            _json_value(record.model_dump()),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for record in records
    ]
    content = ("\n".join(lines) + "\n").encode()
    path.write_bytes(content)
    return len(lines), hashlib.sha256(content).hexdigest()


def write_canonical_package(package: CanonicalPackage, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    collections: tuple[tuple[str, tuple[BaseModel, ...]], ...] = (
        ("batch.jsonl", (package.batch,)),
        ("periods.jsonl", package.periods),
        ("organizations.jsonl", package.organizations),
        ("customer_segments.jsonl", package.customer_segments),
        ("customers.jsonl", package.customers),
        ("logistics_products.jsonl", package.logistics_products),
        ("regions.jsonl", package.regions),
        ("management_accounts.jsonl", package.management_accounts),
        ("scenario_versions.jsonl", package.scenario_versions),
        ("operating_actuals.jsonl", package.operating_actuals),
        ("financial_actuals.jsonl", package.financial_actuals),
        ("monthly_budgets.jsonl", package.monthly_budgets),
        ("ar_collections.jsonl", package.ar_collections),
    )
    manifest_files: dict[str, dict[str, int | str]] = {}
    for filename, records in collections:
        count, digest = _write_jsonl(destination / filename, records)
        manifest_files[filename] = {"row_count": count, "sha256": digest}
    manifest = {
        "contract_version": package.batch.contract_version,
        "batch_code": package.batch.batch_code,
        "files": manifest_files,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
