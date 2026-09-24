"""Task 4 (发行版) tests: damai CanonicalPackage conversion + deterministic release.

计划《大麦物流演示数据实施计划》Task 4 —— 先写失败测试固定合同：
- 转换守恒：canonical 包的收入/成本/AR 桶/预算合计与大麦 dict 严格一致；
- 构建确定性：同一版本两次构建，JSONL/YAML/manifest 字节一致、XLSX 语义一致；
- 期间合同：24 个连续期间（comparison 2024-09~2025-08 + analysis 2025-09~2026-08）。
"""

from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from flow_api.fixtures.damai.canonical import build_damai_canonical_package
from flow_api.fixtures.damai.generator import build_damai_package

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _sum_decimal(values) -> Decimal:
    return sum((Decimal(v) for v in values), Decimal("0"))


class ConversionConservationTests(unittest.TestCase):
    """大麦 dict → CanonicalPackage 转换必须逐项守恒。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = build_damai_package()
        cls.package = build_damai_canonical_package()

    def test_period_contract(self) -> None:
        self.assertEqual(len(self.package.periods), 24)
        windows = {p.window for p in self.package.periods}
        self.assertEqual(windows, {"comparison", "analysis"})
        months = [p.month_key for p in self.package.periods]
        self.assertEqual(months[0], "2024-09")
        self.assertEqual(months[-1], "2026-08")

    def test_operating_revenue_conserved(self) -> None:
        raw_total = _sum_decimal(
            row["revenue"] for row in self.raw["monthly_facts"]["operating_actual"]
        )
        pkg_total = _sum_decimal(row.revenue for row in self.package.operating_actuals)
        self.assertEqual(raw_total, pkg_total)

    def test_operating_cost_conserved_via_three_way_split(self) -> None:
        raw_total = _sum_decimal(
            row["cost"] for row in self.raw["monthly_facts"]["operating_actual"]
        )
        pkg_total = _sum_decimal(
            row.warehousing_cost + row.transportation_cost + row.other_direct_cost
            for row in self.package.operating_actuals
        )
        self.assertEqual(raw_total, pkg_total)

    def test_gross_profit_conserved(self) -> None:
        raw_total = _sum_decimal(
            _sum_decimal(row["revenue"] for row in [r]) - _sum_decimal(row["cost"] for row in [r])
            for r in self.raw["monthly_facts"]["operating_actual"]
        )
        pkg_revenue = _sum_decimal(row.revenue for row in self.package.operating_actuals)
        pkg_cost = _sum_decimal(
            row.warehousing_cost + row.transportation_cost + row.other_direct_cost
            for row in self.package.operating_actuals
        )
        self.assertEqual(raw_total, pkg_revenue - pkg_cost)

    def test_budget_conserved(self) -> None:
        raw_total = _sum_decimal(
            row["revenue"] for row in self.raw["monthly_facts"]["budget"]
        )
        pkg_total = _sum_decimal(
            row.amount
            for row in self.package.monthly_budgets
            if row.metric_code == "REVENUE"
        )
        self.assertEqual(raw_total, pkg_total)

    def test_ar_buckets_conserved(self) -> None:
        raw = self.raw["monthly_facts"]["ar_aging"]
        for bucket_field, bucket_code in (
            ("b_current", "current"),
            ("b_31_60", "31-60"),
            ("b_61_90", "61-90"),
            ("b_90_plus", "90+"),
        ):
            raw_total = _sum_decimal(row[bucket_field] for row in raw)
            pkg_total = _sum_decimal(
                row.receivable_balance
                for row in self.package.ar_collections
                if row.aging_bucket == bucket_code
            )
            self.assertEqual(raw_total, pkg_total, bucket_code)
        raw_collected = _sum_decimal(row["collected"] for row in raw)
        pkg_collected = _sum_decimal(
            row.collected_amount for row in self.package.ar_collections
        )
        self.assertEqual(raw_collected, pkg_collected)

    def test_financial_revenue_matches_operating(self) -> None:
        op_total = _sum_decimal(row.revenue for row in self.package.operating_actuals)
        fin_total = _sum_decimal(
            row.amount
            for row in self.package.financial_actuals
            if row.management_account_code == "REVENUE"
        )
        self.assertEqual(op_total, fin_total)

    def test_single_enterprise_scope(self) -> None:
        orgs = self.package.organizations
        parents = {o.code for o in orgs if o.level == "group"}
        self.assertEqual(len(parents), 1)


class ReleaseBuildTests(unittest.TestCase):
    """构建确定性：两次构建字节一致；manifest 计数与汇总匹配。"""

    def test_build_release_is_deterministic(self) -> None:
        import sys

        if str(REPOSITORY_ROOT) not in sys.path:
            sys.path.insert(0, str(REPOSITORY_ROOT))
        from scripts.build_damai_demo import build_release

        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = build_release(Path(first))
            two = build_release(Path(second))
            self.assertEqual(one["manifest"], two["manifest"])
            for rel, digest in one["files"].items():
                self.assertEqual(digest, two["files"][rel], rel)
            # 逐文件对账：文本产物字节一致；xlsx 为语义指纹（zip 容器非字节确定）
            import hashlib

            for rel, digest in one["files"].items():
                content = (Path(first) / rel).read_bytes()
                actual = (
                    two["files"][rel]
                    if rel.endswith(".xlsx")
                    else hashlib.sha256(content).hexdigest()
                )
                self.assertEqual(actual, digest, rel)

    def test_release_contains_contracted_files(self) -> None:
        import sys

        if str(REPOSITORY_ROOT) not in sys.path:
            sys.path.insert(0, str(REPOSITORY_ROOT))
        from scripts.build_damai_demo import REQUIRED_FILES, build_release

        with tempfile.TemporaryDirectory() as td:
            result = build_release(Path(td))
            for rel in REQUIRED_FILES:
                self.assertIn(rel, result["files"], rel)
            manifest = result["manifest"]
            self.assertTrue(manifest["synthetic"])
            self.assertEqual(manifest["periods"]["total"], 24)
            self.assertEqual(manifest["periods"]["analysis"], 12)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Task A1 红灯：全量数据合同（规格 §3.3 / 计划 §6 验收下限）
# 明细级 1,920 经营 / 10,752 预算 / 4,800 AR；禁止 *-AGG / R-ALL 冒充明细。
# ---------------------------------------------------------------------------

AGG_CODES = {"DM-AGG", "P-AGG", "R-ALL"}
BUDGET_RAW_LINE_ACCOUNTS = (
    "REVENUE",
    "WAREHOUSING_COST",
    "TRANSPORTATION_COST",
    "OTHER_DIRECT_COST",
    "OPERATING_EXPENSE",
    "OPERATING_PROFIT",
    "OPERATING_CASH_FLOW",
)
AR_FIVE_BUCKETS = ("current", "1-30", "31-60", "61-90", "90+")


class FullDimensionContractTests(unittest.TestCase):
    """规格 §3.3 可导入粒度合同：明细真实进入 canonical。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.package = build_damai_canonical_package()

    def test_organizations_are_one_group_plus_four_units(self) -> None:
        orgs = self.package.organizations
        groups = [o for o in orgs if o.level == "group"]
        units = [o for o in orgs if o.level == "business_unit"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(units), 4, f"业务单元必须 4 个，实际 {len(units)}")
        for unit in units:
            self.assertEqual(unit.parent_code, groups[0].code)

    def test_dimensions_reach_canonical_without_aggregate_members(self) -> None:
        self.assertEqual(len(self.package.customer_segments), 4)
        self.assertEqual(len(self.package.customers), 40)
        self.assertEqual(len(self.package.logistics_products), 8)
        self.assertEqual(len(self.package.regions), 6)
        for customer in self.package.customers:
            self.assertNotIn(customer.code, AGG_CODES)
            self.assertIn(customer.segment_code, {s.code for s in self.package.customer_segments})

    def test_operating_actuals_detail_grain_1920(self) -> None:
        rows = self.package.operating_actuals
        self.assertEqual(len(rows), 1920, f"经营明细必须 24×40×2=1920 条，实际 {len(rows)}")
        for row in rows:
            self.assertNotIn(row.customer_code, AGG_CODES)
            self.assertNotIn(row.logistics_product_code, AGG_CODES)
            self.assertNotIn(row.region_code, AGG_CODES)

    def test_every_analysis_month_covers_all_dimensions(self) -> None:
        rows = [r for r in self.package.operating_actuals if r.month_key >= "2025-09"]
        by_month: dict[str, list] = {}
        for row in rows:
            by_month.setdefault(row.month_key, []).append(row)
        self.assertEqual(len(by_month), 12)
        for month, month_rows in sorted(by_month.items()):
            self.assertEqual(len({r.customer_code for r in month_rows}), 40, month)
            self.assertEqual(len({r.logistics_product_code for r in month_rows}), 8, month)
            self.assertEqual(len({r.region_code for r in month_rows}), 6, month)
            self.assertEqual(len({r.organization_code for r in month_rows}), 4, month)

    def test_financial_actuals_24_months_4_units_core_accounts(self) -> None:
        rows = self.package.financial_actuals
        core = {
            "REVENUE", "WAREHOUSING_COST", "TRANSPORTATION_COST",
            "OTHER_DIRECT_COST", "GROSS_PROFIT", "OPERATING_EXPENSE",
            "OPERATING_PROFIT",
        }
        cells = {(r.month_key, r.organization_code) for r in rows}
        self.assertEqual(len(cells), 24 * 4, f"财务实际须覆盖 24 月×4 单元，实际 {len(cells)}")
        by_cell: dict[tuple, set] = {}
        for row in rows:
            by_cell.setdefault((row.month_key, row.organization_code), set()).add(
                row.management_account_code
            )
        for cell, accounts in by_cell.items():
            self.assertTrue(core <= accounts, f"{cell} 缺核心科目 {core - accounts}")

    def test_budget_10752_raw_lines_with_cell_identity(self) -> None:
        rows = self.package.monthly_budgets
        self.assertEqual(len(rows), 10752, f"预算必须 12×4×4×8×7=10752 条，实际 {len(rows)}")
        cells: dict[tuple, dict[str, Decimal]] = {}
        for row in rows:
            key = (row.month_key, row.organization_code,
                   row.customer_segment_code, row.logistics_product_code)
            cells.setdefault(key, {})[row.management_account_code] = row.amount
        self.assertEqual(len(cells), 12 * 4 * 4 * 8)
        for key, lines in cells.items():
            self.assertEqual(set(lines), set(BUDGET_RAW_LINE_ACCOUNTS), key)
            identity = (
                lines["REVENUE"]
                - lines["WAREHOUSING_COST"]
                - lines["TRANSPORTATION_COST"]
                - lines["OTHER_DIRECT_COST"]
                - lines["OPERATING_EXPENSE"]
            )
            self.assertEqual(identity, lines["OPERATING_PROFIT"],
                             f"{key} 预算恒等式不闭合")
            self.assertIn("OPERATING_CASH_FLOW", lines)

    def test_budget_metric_codes_follow_engine_contract(self) -> None:
        """规格 §3.3：3 类成本统一 DIRECT_COST；期间费用 OPERATING_EXPENSE。"""
        mapping = {}
        for row in self.package.monthly_budgets:
            mapping.setdefault(row.management_account_code, set()).add(row.metric_code)
        for account in ("WAREHOUSING_COST", "TRANSPORTATION_COST", "OTHER_DIRECT_COST"):
            self.assertEqual(mapping.get(account), {"DIRECT_COST"}, account)
        self.assertEqual(mapping.get("REVENUE"), {"REVENUE"})
        self.assertEqual(mapping.get("OPERATING_EXPENSE"), {"OPERATING_EXPENSE"})
        self.assertEqual(mapping.get("OPERATING_PROFIT"), {"OPERATING_PROFIT"})
        self.assertEqual(mapping.get("OPERATING_CASH_FLOW"), {"OPERATING_CASH_FLOW"})

    def test_ar_4800_rows_five_buckets_per_customer_month(self) -> None:
        rows = self.package.ar_collections
        self.assertEqual(len(rows), 4800, f"AR 必须 24×40×5=4800 条，实际 {len(rows)}")
        cells: dict[tuple, list] = {}
        for row in rows:
            self.assertNotIn(row.customer_code, AGG_CODES)
            cells.setdefault((row.month_key, row.customer_code), []).append(row)
        self.assertEqual(len(cells), 24 * 40)
        for key, cell_rows in cells.items():
            buckets = sorted(r.aging_bucket for r in cell_rows)
            self.assertEqual(buckets, sorted(AR_FIVE_BUCKETS), key)

    def test_ar_bucket_sum_equals_outstanding_and_non_negative(self) -> None:
        cells: dict[tuple, list] = {}
        for row in self.package.ar_collections:
            cells.setdefault((row.month_key, row.customer_code), []).append(row)
        for key, cell_rows in cells.items():
            total = sum((r.receivable_balance for r in cell_rows), Decimal("0"))
            due = sum((r.due_amount for r in cell_rows), Decimal("0"))
            overdue = sum((r.overdue_amount for r in cell_rows), Decimal("0"))
            # 未到期 + 逾期 = 应收余额（规格 §5.1 定义约束）
            self.assertEqual(due + overdue, total, key)
            for row in cell_rows:
                self.assertGreaterEqual(row.receivable_balance, Decimal("0"))
                self.assertGreaterEqual(row.collected_amount, Decimal("0"))
