"""公开财报 C 级逐格台账的数量、来源身份和未决状态回归。"""

from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path

from scripts.build_public_c_level_ledgers import (
    confirmed_42,
    jdl_ledger,
    suspicion_candidates,
    suspicion_groups,
)


class PublicCLevelLedgerTests(unittest.TestCase):
    def test_jdl_rows_preserve_source_and_unknown_status(self) -> None:
        rows = jdl_ledger()
        self.assertEqual(len(rows), 222)
        self.assertEqual(sum(row["status"] == "confirmed_wrong_statement_attribution" for row in rows), 22)
        self.assertEqual(sum(row["status"] == "source_line_value_verified" for row in rows), 179)
        self.assertEqual(sum(row["status"] == "source_line_blank_verified" for row in rows), 5)
        self.assertEqual(
            sum(
                row["status"] == "source_line_verified_statement_boundary_unresolved"
                for row in rows
            ),
            16,
        )
        self.assertFalse(any(row["status"] == "unknown_source_readability" for row in rows))
        self.assertTrue(all(row["source_pdf_sha256"] == "809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c" for row in rows))
        self.assertTrue(all(row["readable_twin_pdf_sha256"] == "32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009" for row in rows))
        self.assertTrue(all(row["review_bundle_sha256"] == "748d7d3de96c312ed76d11effe5ec1fb3a00f614908bfc05155e2237e7f1f4cf" for row in rows))
        for row in rows:
            if row["status"].startswith("source_line_"):
                self.assertNotIn("未定位", row["source_page_physical"])
                self.assertIn("物理页", row["source_coordinate"])
                self.assertIn("英文原文：", row["source_coordinate"])
                self.assertEqual(row["corrected_extraction_value"], row["review_bundle_value"])
                if row["review_bundle_value"]:
                    value = int(row["review_bundle_value"])
                    token = f"{abs(value):,}"
                    if value < 0:
                        token = f"({token})"
                else:
                    token = "—"
                evidence_line = row["source_coordinate"].split("英文原文：", 1)[1]
                source_values = re.findall(r"\(?\d[\d,]*\)?|—", evidence_line)[-2:]
                source_index = (
                    0 if row["column"] in {"value_current", "value_end"} else 1
                )
                self.assertEqual(source_values[source_index], token)

    def test_jdl_source_crosswalk_covers_each_unresolved_cell_once(self) -> None:
        root = Path(__file__).resolve().parents[2]
        path = (
            root
            / "validation/financial_reports/review-inputs/jdl_readable_twin_crosswalk_v1.csv"
        )
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        original_sha = "809957cc3f42a77227963ef327cc74e08abf4666d91f0866b0aa6e3d50b85c5c"
        twin_sha = "32a99c3a4341a32db84073eeb93c9679969b0ad8216514707cdf9d2dd1825009"
        self.assertEqual(len(rows), 200)
        self.assertEqual(len({row["ledger_id"] for row in rows}), 200)
        self.assertTrue(all(row["source_pdf_sha256"] == original_sha for row in rows))
        self.assertTrue(all(row["readable_twin_pdf_sha256"] == twin_sha for row in rows))
        unresolved = [
            row
            for row in rows
            if row["status"] == "source_line_verified_statement_boundary_unresolved"
        ]
        self.assertEqual(len(unresolved), 16)
        self.assertTrue(
            all(
                row["source_page_physical"] == "107" and row["source_page_printed"] == "106"
                for row in unresolved
            )
        )

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
        self.assertEqual(sum(int(row["reconstructed_candidate_count"]) for row in rows), 112)
        self.assertTrue(all(row["status"] == "candidate_members_reconstructed_two_cell_gap_open" for row in rows))
        self.assertTrue(all("唯一111；与总表109差2格" in row["arithmetic_reconciliation"] for row in rows))

    def test_suspected_cell_candidates_reconstruct_111_unique_cells(self) -> None:
        rows = suspicion_candidates()
        self.assertEqual(len(rows), 111)
        by_group = {}
        for row in rows:
            for group_id in row["candidate_groups"].split(";"):
                by_group[group_id] = by_group.get(group_id, 0) + 1
        self.assertEqual(by_group, {
            "S109-BABA-FY2020-CURRENT": 28,
            "S109-ALI-CASH-SCOPE": 56,
            "S109-ALI-EQUITY-CURRENT": 14,
            "S109-CAINIAO-NONCURRENT": 10,
            "S109-JDL-ATTRIBUTION": 4,
        })
        duplicated = [row for row in rows if ";" in row["candidate_groups"]]
        self.assertEqual(len(duplicated), 1)
        self.assertEqual(duplicated[0]["item"], "股權證券及其他投資")
        self.assertEqual(duplicated[0]["column"], "value_current")
        overage = [row for row in rows if row["status"] == "excess_two_vs_FY2020_material_count_unresolved"]
        self.assertEqual({(row["item"], row["column"], row["candidate_value"]) for row in overage}, {
            ("股權證券及其他投資", "value_begin", "9927"),
            ("股權證券及其他投資", "value_end", "4234"),
        })
        self.assertEqual(sum(row["status"] == "candidate_not_adjudicated" for row in rows), 109)

    def test_checked_in_ledgers_match_generator(self) -> None:
        root = Path(__file__).resolve().parents[2]
        ledger_dir = root / "validation/financial_reports/review-ledgers"
        for filename, expected in (
            ("jdl-222-cell-reconciliation-v1.csv", jdl_ledger()),
            ("confirmed-42-exceptions-v1.csv", confirmed_42()),
            ("suspected-109-group-reconciliation-v1.csv", suspicion_groups()),
            ("suspected-109-cell-candidates-v1.csv", suspicion_candidates()),
        ):
            with (ledger_dir / filename).open(encoding="utf-8", newline="") as stream:
                self.assertEqual(list(csv.DictReader(stream)), expected, filename)


if __name__ == "__main__":
    unittest.main()
