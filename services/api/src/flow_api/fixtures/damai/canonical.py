"""大麦 canonical dict → flow.excel.v1 CanonicalPackage 转换（Task 4）。

守恒合同（tests/fixtures/test_damai_canonical.py 固定）：
- 收入、三路成本合计、毛利、预算、AR 四桶与回款逐项与 build_damai_package() 一致；
- 期间 = comparison 2024-09~2025-08 + analysis 2025-09~2026-08（24 个月连续）；
- 确定性：uuid5(record) 与固定比例拆分，无时钟/随机输入。

粒度决策：大麦 facts 为 business-family 聚合（24 月 × 3 族），转换保持该粒度，
客户/产品/区域使用聚合成员（DM-AGG / P-AGG / R-ALL），不伪造明细；
合计成本按固定比例拆为仓储 0.30 / 运输 0.60 / 其他 0.10（synthetic 演示口径）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

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
from flow_api.fixtures.damai.generator import build_damai_package

_DAMAI_NAMESPACE = UUID("da0a1a10-4c41-b9d1-3d4a-2f5e6b7c9d01")

_COMPARE_MONTHS = tuple(f"2024-{m:02d}" for m in range(9, 13)) + tuple(
    f"2025-{m:02d}" for m in range(1, 9)
)
_ANALYSIS_MONTHS = tuple(f"2025-{m:02d}" for m in range(9, 13)) + tuple(
    f"2026-{m:02d}" for m in range(1, 9)
)

_GROUP_CODE = "DAMAI_GROUP"
_FAMILY_TO_ORG: dict[str, tuple[str, str]] = {
    "international_cross_border": ("BU-INTL", "国际与跨境物流事业部"),
    "china_logistics": ("BU-CHINA", "中国物流事业部"),
    "tech_and_other": ("BU-TECH", "科技及其他事业部"),
}
_AGG_CUSTOMER = "DM-AGG"
_AGG_PRODUCT = "P-AGG"
_AGG_REGION = "R-ALL"

# 合计成本 → 三路直接成本的固定演示拆分（和恒等于合计）
_COST_SPLIT: tuple[tuple[str, Decimal], ...] = (
    ("WAREHOUSING_COST", Decimal("0.30")),
    ("TRANSPORTATION_COST", Decimal("0.60")),
    ("OTHER_DIRECT_COST", Decimal("0.10")),
)

_BUDGET_SCENARIO = "BUDGET_DAMAI_V1"


def _rid(prefix: str, *parts: str) -> str:
    return str(uuid5(_DAMAI_NAMESPACE, ":".join((prefix, *parts))))


def _d(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"))


def _periods() -> tuple[PeriodRecord, ...]:
    rows: list[PeriodRecord] = []
    for month_key in _COMPARE_MONTHS + _ANALYSIS_MONTHS:
        year, month = (int(v) for v in month_key.split("-"))
        rows.append(
            PeriodRecord(
                month_key=month_key,
                year=year,
                quarter=(month - 1) // 3 + 1,
                month=month,
                window="comparison" if month_key in _COMPARE_MONTHS else "analysis",
            )
        )
    return tuple(rows)


def _dimensions() -> tuple[
    tuple[OrganizationRecord, ...],
    tuple[CustomerSegmentRecord, ...],
    tuple[CustomerRecord, ...],
    tuple[LogisticsProductRecord, ...],
    tuple[RegionRecord, ...],
    tuple[ManagementAccountRecord, ...],
    tuple[ScenarioVersionRecord, ...],
]:
    organizations = (
        OrganizationRecord(code=_GROUP_CODE, name="大麦物流集团（synthetic）", level="group"),
        *(
            OrganizationRecord(
                code=code, name=name, level="business_unit", parent_code=_GROUP_CODE
            )
            for code, name in _FAMILY_TO_ORG.values()
        ),
    )
    segments = (CustomerSegmentRecord(code="DM_SYNTH", name="合成演示客户"),)
    customers = (
        CustomerRecord(
            code=_AGG_CUSTOMER,
            name="聚合客户（synthetic 演示口径）",
            industry="综合物流",
            tier="C",
            credit_term_days=30,
            segment_code="DM_SYNTH",
        ),
    )
    products = (
        LogisticsProductRecord(code=_AGG_PRODUCT, name="聚合产品（synthetic）", level="service"),
    )
    regions = (RegionRecord(code=_AGG_REGION, name="全国（synthetic）"),)
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
            code="OPERATING_CASH_FLOW", name="经营现金流", category="cash_flow"
        ),
        ManagementAccountRecord(
            code="AR_BALANCE", name="应收账款余额", category="working_capital"
        ),
    )
    scenarios = (
        ScenarioVersionRecord(code="ACTUAL", name="实际", scenario_type="actual"),
        ScenarioVersionRecord(
            code=_BUDGET_SCENARIO,
            name="大麦演示预算",
            scenario_type="budget",
            version_label="DEMO V1",
        ),
    )
    return organizations, segments, customers, products, regions, accounts, scenarios


def _operating_actuals(raw_rows: list[dict[str, Any]]) -> tuple[OperatingActualRecord, ...]:
    rows: list[OperatingActualRecord] = []
    for row in raw_rows:
        org_code = _FAMILY_TO_ORG[row["family_id"]][0]
        revenue = _d(row["revenue"])
        cost_total = _d(row["cost"])
        # 收入派生单量（确定性演示口径）：客单价 120、每单 2.0 件
        order_count = (revenue / Decimal("120")).quantize(Decimal("0.0001"))
        shipment_count = (order_count * Decimal("2.0")).quantize(Decimal("0.0001"))
        values: list[Decimal] = []
        last = len(_COST_SPLIT) - 1
        running = Decimal("0")
        for index, (_account, weight) in enumerate(_COST_SPLIT):
            if index < last:
                value = _d(cost_total * weight)
                running += value
            else:  # 尾差并入最后一路，保证三路之和恒等于合计
                value = cost_total - running
            values.append(value)
        warehousing, transportation, other = values
        rows.append(
            OperatingActualRecord(
                record_id=_rid("operating", row["month"], org_code, row["family_id"]),
                month_key=row["month"],
                organization_code=org_code,
                customer_code=_AGG_CUSTOMER,
                logistics_product_code=_AGG_PRODUCT,
                region_code=_AGG_REGION,
                order_count=order_count,
                shipment_count=shipment_count,
                revenue=revenue,
                warehousing_cost=warehousing,
                transportation_cost=transportation,
                other_direct_cost=other,
            )
        )
    return tuple(rows)


def _financial_actuals(
    raw: dict[str, Any],
    operating: tuple[OperatingActualRecord, ...],
) -> tuple[FinancialActualRecord, ...]:
    """财务账 = 经营账聚合（REVENUE/三成本/毛利）+ 全司口径分摊（OCF/AR）。

    分摊份额 = 各组织当月经营收入 / 全司当月经营收入，逐项守恒（尾差入末位组织）。
    """

    by_month_org: dict[tuple[str, str], dict[str, Decimal]] = {}
    for row in operating:
        agg = by_month_org.setdefault((row.month_key, row.organization_code), {})
        agg["REVENUE"] = agg.get("REVENUE", Decimal("0")) + row.revenue
        agg["WAREHOUSING_COST"] = (
            agg.get("WAREHOUSING_COST", Decimal("0")) + row.warehousing_cost
        )
        agg["TRANSPORTATION_COST"] = (
            agg.get("TRANSPORTATION_COST", Decimal("0")) + row.transportation_cost
        )
        agg["OTHER_DIRECT_COST"] = (
            agg.get("OTHER_DIRECT_COST", Decimal("0")) + row.other_direct_cost
        )
        agg["GROSS_PROFIT"] = agg.get("GROSS_PROFIT", Decimal("0")) + row.revenue - (
            row.warehousing_cost + row.transportation_cost + row.other_direct_cost
        )

    def _split(total: Decimal, month: str) -> dict[str, Decimal]:
        """按各组织当月收入份额分摊（尾差入末位组织，合计守恒）。"""

        org_codes = tuple(code for code, _ in _FAMILY_TO_ORG.values())
        month_total = sum(
            (by_month_org[(month, code)]["REVENUE"] for code in org_codes), Decimal("0")
        )
        shares: dict[str, Decimal] = {}
        running = Decimal("0")
        for index, code in enumerate(org_codes):
            if index < len(org_codes) - 1:
                share = _d(total * by_month_org[(month, code)]["REVENUE"] / month_total)
                running += share
            else:
                share = total - running
            shares[code] = share
        return shares

    ocf_by_month = {row["month"]: _d(row["ocf"]) for row in raw["monthly_facts"]["cash_flow"]}
    ar_by_month = {
        row["month"]: _d(row["ar_outstanding"]) for row in raw["monthly_facts"]["ar_aging"]
    }

    rows: list[FinancialActualRecord] = []
    for (month, org_code), agg in sorted(by_month_org.items()):
        for account_code in (
            "REVENUE",
            "WAREHOUSING_COST",
            "TRANSPORTATION_COST",
            "OTHER_DIRECT_COST",
            "GROSS_PROFIT",
        ):
            rows.append(
                FinancialActualRecord(
                    record_id=_rid("financial", month, org_code, account_code),
                    month_key=month,
                    organization_code=org_code,
                    management_account_code=account_code,
                    amount=agg[account_code],
                )
            )
        for account_code, totals in (
            ("OPERATING_CASH_FLOW", ocf_by_month),
            ("AR_BALANCE", ar_by_month),
        ):
            total = totals.get(month)
            if total is None:
                continue
            for org_code_share, amount in _split(total, month).items():
                rows.append(
                    FinancialActualRecord(
                        record_id=_rid("financial", month, org_code_share, account_code),
                        month_key=month,
                        organization_code=org_code_share,
                        management_account_code=account_code,
                        amount=amount,
                    )
                )
    return tuple(rows)


def _budgets(raw_rows: list[dict[str, Any]]) -> tuple[MonthlyBudgetRecord, ...]:
    rows: list[MonthlyBudgetRecord] = []
    for row in raw_rows:
        month = row["month"]
        rows.append(
            MonthlyBudgetRecord(
                record_id=_rid("budget", month, "REVENUE"),
                month_key=month,
                organization_code=_GROUP_CODE,
                customer_segment_code="DM_SYNTH",
                logistics_product_code=_AGG_PRODUCT,
                management_account_code="REVENUE",
                scenario_code=_BUDGET_SCENARIO,
                metric_code="REVENUE",
                amount=_d(row["revenue"]),
            )
        )
    return tuple(rows)


_AR_BUCKETS: tuple[tuple[str, str, bool], ...] = (
    ("current", "b_current", False),
    ("31-60", "b_31_60", True),
    ("61-90", "b_61_90", True),
    ("90+", "b_90_plus", True),
)


def _ar_collections(raw_rows: list[dict[str, Any]]) -> tuple[ArCollectionRecord, ...]:
    rows: list[ArCollectionRecord] = []
    for row in raw_rows:
        month = row["month"]
        for bucket_code, field, overdue in _AR_BUCKETS:
            balance = _d(row[field])
            due = balance if overdue else Decimal("0")
            stem = month.replace("-", "") + "-" + bucket_code.replace("-", "")
            rows.append(
                ArCollectionRecord(
                    record_id=_rid("ar", month, _AGG_CUSTOMER, bucket_code),
                    month_key=month,
                    customer_code=_AGG_CUSTOMER,
                    invoice_number=f"INV-SYN-{stem}",
                    aging_bucket=bucket_code,
                    receivable_balance=balance,
                    due_amount=due,
                    overdue_amount=_d(row["overdue"]) if "overdue" in row else due,
                    collected_amount=(
                        _d(row["collected"]) if bucket_code == "current" else Decimal("0")
                    ),
                )
            )
    return tuple(rows)


def build_damai_canonical_package() -> CanonicalPackage:
    """构建大麦 flow.excel.v1 canonical 包（确定性、守恒）。"""

    raw = build_damai_package()
    (
        organizations,
        segments,
        customers,
        products,
        regions,
        accounts,
        scenarios,
    ) = _dimensions()
    operating = _operating_actuals(raw["monthly_facts"]["operating_actual"])
    return CanonicalPackage(
        batch=BatchRecord(
            batch_code="DAMAI_DEMO_2026_08",
            contract_version="flow.excel.v1",
            analysis_start_month=_ANALYSIS_MONTHS[0],
            analysis_end_month=_ANALYSIS_MONTHS[-1],
            comparison_start_month=_COMPARE_MONTHS[0],
            comparison_end_month=_COMPARE_MONTHS[-1],
            currency="CNY",
            actual_scenario_code="ACTUAL",
            budget_scenario_code=_BUDGET_SCENARIO,
            budget_version_label="DEMO V1",
            generated_at=datetime(2026, 9, 24, 0, 0, tzinfo=UTC),
        ),
        periods=_periods(),
        organizations=organizations,
        customer_segments=segments,
        customers=customers,
        logistics_products=products,
        regions=regions,
        management_accounts=accounts,
        scenario_versions=scenarios,
        operating_actuals=operating,
        financial_actuals=_financial_actuals(raw, operating),
        monthly_budgets=_budgets(raw["monthly_facts"]["budget"]),
        ar_collections=_ar_collections(raw["monthly_facts"]["ar_aging"]),
    )


__all__ = ["build_damai_canonical_package"]
