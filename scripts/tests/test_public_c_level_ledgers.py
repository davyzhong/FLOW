"""公开财报 C 级逐格台账的数量、来源身份和未决状态回归。"""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.build_public_c_level_ledgers import (
    confirmed_42,
    jdl_ledger,
    suspicion_groups,
)


class PublicCLevelLedgerTests(unittest.TestCase):
    def test_jdl_rows_preserve_source_and_unknown_status(self) -> None:
        rows = jdl_ledger()
        self.assertEqual(len(rows), 222)
        self.assertEqual(sum(row["status"] == "confirmed_wrong_statement_attribution" for row in rows), 22)
        self.assertEqual(sum(row["status"] == "unknown_source_readability" for row in rows), 200)
        self.assertTrue(all(row["source_pdf_sha256"] == "809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c" for row in rows))
        self.assertTrue(all(row["readable_twin_pdf_sha256"] == "32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009" for row in rows))
        self.assertTrue(all(row["review_bundle_sha256"] == "748d7d3de96c312ed76d11effe5ec1fb3a00f614908bfc05155e2237e7f1f4cf" for row in rows))

    def test_confirmed_42_are_unique_and_classified(self) -> None:
        rows = confirmed_42()
        self.assertEqual(len(rows), 42)
        self.assertEqual(len({row["finding_id"] for row in rows}), 42)
        self.assertEqual(sum(row["company"] == "菜鸟集团" for row in rows), 19)
        self.assertEqual(sum(row["company"] == "京东物流" for row in rows), 22)
        self.assertEqual(sum(row["company"] == "阿里巴巴" for row in rows), 1)

    def test_suspected_groups_disclose_arithmetic_conflict(self) -> None:
        rows = suspicion_groups()
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(int(row["reported_cell_count"]) for row in rows), 121)
        self.assertTrue(all(row["status"] == "unresolved_count_or_membership_mismatch" for row in rows))
        self.assertTrue(all("相差11格" in row["arithmetic_reconciliation"] for row in rows))

    def test_checked_in_ledgers_match_generator(self) -> None:
        root = Path(__file__).resolve().parents[2]
        ledger_dir = root / "validation/financial_reports/review-ledgers"
        for filename, expected in (
            ("jdl-222-cell-reconciliation-v1.csv", jdl_ledger()),
            ("confirmed-42-exceptions-v1.csv", confirmed_42()),
            ("suspected-109-group-reconciliation-v1.csv", suspicion_groups()),
        ):
            with (ledger_dir / filename).open(encoding="utf-8", newline="") as stream:
                self.assertEqual(list(csv.DictReader(stream)), expected, filename)


if __name__ == "__main__":
    unittest.main()
