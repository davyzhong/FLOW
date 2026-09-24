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
