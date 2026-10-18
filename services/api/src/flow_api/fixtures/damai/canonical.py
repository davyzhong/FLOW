"""大麦 canonical dict → flow.excel.v1 CanonicalPackage 转换（Task 4 / Task A2）。

守恒合同（tests/fixtures/test_damai_canonical.py 固定）：
- 收入、三路成本合计、毛利、预算、AR 五桶与回款逐项与 build_damai_package() 一致；
- 期间 = comparison（FY2022）2021-04~2022-03 + analysis（FY2023）2022-04~2023-03；
- 确定性：uuid5(record) 与固定比例拆分，无时钟/随机输入。

粒度（规格 §3.3，Task A2 起）：经营明细为 客户×产品 粒度（1,920 行），
组织 = 1 集团 + 4 事业部（产品归属单元）；禁止 DM-AGG/P-AGG/R-ALL 聚合成员。
合计成本按固定比例拆为仓储 0.30 / 运输 0.60 / 其他 0.10（synthetic 演示口径，
尾差并入末路）；预算 metric_code 合同：三成本统一 DIRECT_COST。
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
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
from flow_api.fixtures.damai.profile import (
    ANALYSIS_MONTHS as _ANALYSIS_MONTHS,
)
from flow_api.fixtures.damai.profile import (
    BUSINESS_UNITS,
    CUSTOMER_ASSIGNMENTS,
    CUSTOMER_SEGMENTS,
    CUSTOMERS,
    PRODUCTS,
    REGIONS,
)
from flow_api.fixtures.damai.profile import (
    PRIOR_MONTHS as _COMPARE_MONTHS,
)

_DAMAI_NAMESPACE = UUID("da0a1a10-4c41-b9d1-3d4a-2f5e6b7c9d01")
_WAN_TO_CNY = Decimal("10000")

# 时间线迁移（2026-10-13）：期间唯一来源是 profile 的 24 月合同（顶部导入别名）


_GROUP_CODE = "DAMAI_GROUP"
# 4 事业部组织编码（顺序与 BUSINESS_UNITS 一致）
_UNIT_TO_ORG: dict[str, tuple[str, str]] = {
    name: (f"BU-{index:02d}", name) for index, name in enumerate(BUSINESS_UNITS, 1)
}
_SEGMENT_TO_CODE: dict[str, str] = {
    name: f"SEG-{index:02d}" for index, name in enumerate(CUSTOMER_SEGMENTS, 1)
}
_REGION_TO_CODE: dict[str, str] = {
    name: f"R-{index:02d}" for index, name in enumerate(REGIONS, 1)
}

# 合计成本 → 三路直接成本的固定演示拆分（和恒等于合计）
_COST_SPLIT: tuple[tuple[str, Decimal], ...] = (
    ("WAREHOUSING_COST", Decimal("0.30")),
    ("TRANSPORTATION_COST", Decimal("0.60")),
    ("OTHER_DIRECT_COST", Decimal("0.10")),
)

# 预算管理科目 → 引擎 metric_code（规格 §3.3：三成本统一 DIRECT_COST）
_METRIC_CODE_MAP: dict[str, str] = {
    "REVENUE": "REVENUE",
    "WAREHOUSING_COST": "DIRECT_COST",
    "TRANSPORTATION_COST": "DIRECT_COST",
    "OTHER_DIRECT_COST": "DIRECT_COST",
    "OPERATING_EXPENSE": "OPERATING_EXPENSE",
    "OPERATING_PROFIT": "OPERATING_PROFIT",
    "OPERATING_CASH_FLOW": "OPERATING_CASH_FLOW",
}

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
            for code, name in _UNIT_TO_ORG.values()
        ),
    )
    segments = tuple(
        CustomerSegmentRecord(code=code, name=name)
        for name, code in _SEGMENT_TO_CODE.items()
    )
    customers = tuple(
        CustomerRecord(
            code=customer_id,
            name=CUSTOMERS[index],
            industry="综合物流",
            tier="A" if index < 10 else ("B" if index < 25 else "C"),
            credit_term_days=int(str(assign["credit_term_days"])),
            segment_code=_SEGMENT_TO_CODE[str(assign["segment"])],
        )
        for index, (customer_id, assign) in enumerate(CUSTOMER_ASSIGNMENTS.items())
    )
    products = tuple(
        LogisticsProductRecord(code=f"P-{i:02d}", name=name, level="service")
        for i, name in enumerate(PRODUCTS, 1)
    )
    regions = tuple(
        RegionRecord(code=code, name=name) for name, code in _REGION_TO_CODE.items()
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
            code="OPERATING_EXPENSE",
            name="经营费用及其他经营项目净额",
            category="operating_expense",
        ),
        ManagementAccountRecord(
            code="OPERATING_PROFIT", name="经营利润", category="operating_profit"
        ),
        ManagementAccountRecord(
            code="SALES_MARKETING_EXPENSE", name="销售及市场推广开支", category="operating_expense"
        ),
        ManagementAccountRecord(
            code="GENERAL_ADMIN_EXPENSE", name="一般及行政开支", category="operating_expense"
        ),
        ManagementAccountRecord(
            code="PRODUCT_DEVELOPMENT_EXPENSE", name="产品开发开支", category="operating_expense"
        ),
        ManagementAccountRecord(
            code="FINANCIAL_ASSET_IMPAIRMENT", name="金融资产减值", category="operating_expense"
        ),
        ManagementAccountRecord(
            code="OTHER_INCOME", name="其他收入", category="operating_profit"
        ),
        ManagementAccountRecord(
            code="OTHER_NET_GAIN_LOSS", name="其他收益及亏损净额", category="operating_profit"
        ),
        ManagementAccountRecord(
            code="NET_PROFIT", name="年度溢利或亏损", category="operating_profit"
        ),
        ManagementAccountRecord(
            code="CASH_AND_CASH_EQUIVALENTS",
            name="现金及现金等价物",
            category="working_capital",
        ),
        ManagementAccountRecord(
            code="OPERATING_CASH_FLOW", name="经营现金流", category="cash_flow"
        ),
        ManagementAccountRecord(
            code="AR_BALANCE", name="应收账款余额", category="working_capital"
        ),
        ManagementAccountRecord(
            code="TOTAL_ASSETS", name="资产总计", category="financial_position"
        ),
        ManagementAccountRecord(
            code="TOTAL_LIABILITIES", name="负债合计", category="financial_position"
        ),
        ManagementAccountRecord(
            code="TOTAL_EQUITY", name="权益总额", category="financial_position"
        ),
        ManagementAccountRecord(
            code="CURRENT_ASSETS", name="流动资产合计", category="financial_position"
        ),
        ManagementAccountRecord(
            code="CURRENT_LIABILITIES", name="流动负债合计", category="financial_position"
        ),
        ManagementAccountRecord(
            code="INVENTORY_BALANCE", name="存货余额", category="working_capital"
        ),
        ManagementAccountRecord(
            code="BORROWINGS", name="借款余额", category="financial_position"
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
        org_code = _UNIT_TO_ORG[row["business_unit"]][0]
        revenue = _d(row["revenue"])
        cost_total = _d(row["cost"])
        # 原始收入以万元计；按人民币 120 元客单价派生整数演示单量。
        order_count = (revenue * _WAN_TO_CNY / Decimal("120")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        shipment_count = order_count * Decimal("2")
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
                record_id=_rid(
                    "operating",
                    row["month"],
                    org_code,
                    row["customer_id"],
                    row["product"],
                ),
                month_key=row["month"],
                organization_code=org_code,
                customer_code=row["customer_id"],
                logistics_product_code=row["product"],
                region_code=_REGION_TO_CODE[row["region"]],
                order_count=order_count,
                shipment_count=shipment_count,
                revenue=_d(revenue * _WAN_TO_CNY),
                warehousing_cost=_d(warehousing * _WAN_TO_CNY),
                transportation_cost=_d(transportation * _WAN_TO_CNY),
                other_direct_cost=_d(other * _WAN_TO_CNY),
            )
        )
    return tuple(rows)


def _financial_actuals(
    raw: dict[str, Any],
    operating: tuple[OperatingActualRecord, ...],
) -> tuple[FinancialActualRecord, ...]:
    """构造公开披露锚定的月度/组织财务视图。

    公开年度损益、现金流和期末现金只按收入权重拆为演示明细，尾差并入
    当月最后一个组织；组织合计始终回到月度生成值，年度合计回到披露事实。
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

    rows: list[FinancialActualRecord] = []
    statement_lines_by_month = {
        row["month"]: row for row in raw["monthly_facts"]["statement_lines"]
    }
    cash_flow_by_month = {
        row["month"]: row for row in raw["monthly_facts"]["cash_flow"]
    }
    balance_sheet_by_month = {
        row["month"]: row for row in raw["monthly_facts"]["balance_sheet"]
    }
    organizations_by_month: dict[str, list[str]] = {}
    for month, org_code in by_month_org:
        organizations_by_month.setdefault(month, []).append(org_code)

    statement_accounts = (
        "SALES_MARKETING_EXPENSE",
        "GENERAL_ADMIN_EXPENSE",
        "PRODUCT_DEVELOPMENT_EXPENSE",
        "FINANCIAL_ASSET_IMPAIRMENT",
        "OTHER_INCOME",
        "OTHER_NET_GAIN_LOSS",
        "NET_PROFIT",
    )
    balance_sheet_accounts = (
        "TOTAL_ASSETS",
        "TOTAL_LIABILITIES",
        "TOTAL_EQUITY",
        "CURRENT_ASSETS",
        "CURRENT_LIABILITIES",
        "AR_BALANCE",
        "INVENTORY_BALANCE",
        "BORROWINGS",
    )
    all_accounts = (
        "REVENUE",
        "WAREHOUSING_COST",
        "TRANSPORTATION_COST",
        "OTHER_DIRECT_COST",
        "GROSS_PROFIT",
        "OPERATING_EXPENSE",
        "OPERATING_PROFIT",
        *statement_accounts,
        "OPERATING_CASH_FLOW",
        "CASH_AND_CASH_EQUIVALENTS",
        *balance_sheet_accounts,
    )
    for month in sorted(organizations_by_month):
        month_organizations = sorted(organizations_by_month[month])
        monthly_revenue = sum(
            (by_month_org[(month, code)]["REVENUE"] for code in month_organizations),
            Decimal("0"),
        )
        statement_lines = statement_lines_by_month[month]
        cash_flow = cash_flow_by_month[month]
        balance_sheet = balance_sheet_by_month[month]
        statement_source_keys = {"NET_PROFIT": "net_profit"}
        monthly_values = {
            account: Decimal(
                statement_lines[statement_source_keys.get(account, account)]
            )
            * _WAN_TO_CNY
            for account in statement_accounts
        }
        monthly_values["OPERATING_CASH_FLOW"] = (
            Decimal(cash_flow["ocf"]) * _WAN_TO_CNY
        )
        monthly_values["CASH_AND_CASH_EQUIVALENTS"] = Decimal(
            cash_flow["cash_balance"]
        ) * _WAN_TO_CNY
        monthly_values.update(
            {
                account: Decimal(balance_sheet[account]) * _WAN_TO_CNY
                for account in balance_sheet_accounts
            }
        )
        allocated: dict[str, dict[str, Decimal]] = {}
        for account, total in monthly_values.items():
            account_rows: dict[str, Decimal] = {}
            running = Decimal("0")
            for org_code in month_organizations[:-1]:
                amount = _d(
                    total
                    * by_month_org[(month, org_code)]["REVENUE"]
                    / monthly_revenue
                )
                account_rows[org_code] = amount
                running += amount
            account_rows[month_organizations[-1]] = _d(total - running)
            allocated[account] = account_rows

        for org_code in month_organizations:
            values = {
                **by_month_org[(month, org_code)],
                **{
                    account: account_rows[org_code]
                    for account, account_rows in allocated.items()
                },
            }
            values["OPERATING_EXPENSE"] = sum(
                (
                    values[account]
                    for account in (
                        "SALES_MARKETING_EXPENSE",
                        "GENERAL_ADMIN_EXPENSE",
                        "PRODUCT_DEVELOPMENT_EXPENSE",
                        "FINANCIAL_ASSET_IMPAIRMENT",
                    )
                ),
                Decimal("0"),
            )
            values["OPERATING_EXPENSE"] -= (
                values["OTHER_INCOME"] + values["OTHER_NET_GAIN_LOSS"]
            )
            values["OPERATING_PROFIT"] = (
                values["GROSS_PROFIT"] - values["OPERATING_EXPENSE"]
            )
            for account in all_accounts:
                rows.append(
                    FinancialActualRecord(
                        record_id=_rid("financial", month, org_code, account),
                        month_key=month,
                        organization_code=org_code,
                        management_account_code=account,
                        amount=values[account],
                    )
                )

    return tuple(rows)


def _budgets(raw_rows: list[dict[str, Any]]) -> tuple[MonthlyBudgetRecord, ...]:
    rows: list[MonthlyBudgetRecord] = []
    for row in raw_rows:
        month = row["month"]
        org_code = _UNIT_TO_ORG[row["business_unit"]][0]
        segment_code = _SEGMENT_TO_CODE[row["customer_segment"]]
        account = row["account"]
        rows.append(
            MonthlyBudgetRecord(
                record_id=_rid("budget", month, org_code, segment_code,
                               row["product"], account),
                month_key=month,
                organization_code=org_code,
                customer_segment_code=segment_code,
                logistics_product_code=row["product"],
                management_account_code=account,
                scenario_code=_BUDGET_SCENARIO,
                metric_code=_METRIC_CODE_MAP[account],
                amount=_d(Decimal(row["amount"]) * _WAN_TO_CNY),
            )
        )
    return tuple(rows)


def _ar_collections(raw_rows: list[dict[str, Any]]) -> tuple[ArCollectionRecord, ...]:
    rows: list[ArCollectionRecord] = []
    for row in raw_rows:
        month = row["month"]
        customer_code = row["customer_id"]
        bucket_code = row["bucket"]
        stem = month.replace("-", "") + "-" + customer_code + "-" + bucket_code.replace("-", "")
        rows.append(
            ArCollectionRecord(
                record_id=_rid("ar", month, customer_code, bucket_code),
                month_key=month,
                customer_code=customer_code,
                invoice_number=f"INV-SYN-{stem}",
                aging_bucket=bucket_code,
                receivable_balance=_d(Decimal(row["balance"]) * _WAN_TO_CNY),
                due_amount=_d(Decimal(row["due"]) * _WAN_TO_CNY),
                overdue_amount=_d(Decimal(row["overdue"]) * _WAN_TO_CNY),
                collected_amount=_d(Decimal(row["collected"]) * _WAN_TO_CNY),
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
            batch_code="DAMAI_DEMO_2023_03",
            contract_version="flow.excel.v1",
            analysis_start_month=_ANALYSIS_MONTHS[0],
            analysis_end_month=_ANALYSIS_MONTHS[-1],
            comparison_start_month=_COMPARE_MONTHS[0],
            comparison_end_month=_COMPARE_MONTHS[-1],
            currency="CNY",
            actual_scenario_code="ACTUAL",
            budget_scenario_code=_BUDGET_SCENARIO,
            budget_version_label="DEMO V1",
            generated_at=datetime(2026, 10, 13, 0, 0, tzinfo=UTC),
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
