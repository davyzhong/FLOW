from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import holdout_u4_run
from scripts.holdout_u4_run import diff_sample, find_row


class HoldoutU4RunTests(unittest.TestCase):
    def test_default_run_targets_only_demoted_legacy_regressions(self) -> None:
        self.assertTrue(hasattr(holdout_u4_run, "selected_samples"))
        self.assertEqual(
            list(holdout_u4_run.selected_samples(None)),
            ["sf_2026h1", "tencent_fy2025", "zto_2026q1"],
        )

    def test_new_holdouts_run_only_when_explicitly_selected(self) -> None:
        self.assertTrue(hasattr(holdout_u4_run, "selected_samples"))
        self.assertEqual(
            list(holdout_u4_run.selected_samples(["xiaomi_2026h1", "alibaba_fy2027q1"])),
            ["xiaomi_2026h1", "alibaba_fy2027q1"],
        )

    def test_run_id_selects_non_overwriting_evidence_directory(self) -> None:
        with patch.dict("os.environ", {"FLOW_HOLDOUT_RUN_ID": "2026-09-29-adapter-v2"}):
            self.assertTrue(hasattr(holdout_u4_run, "holdout_output_dir"))
            output_dir = holdout_u4_run.holdout_output_dir(Path("/repo"))

        self.assertEqual(
            output_dir,
            Path("/repo/validation/financial_reports/holdout_runs/2026-09-29-adapter-v2"),
        )

    def test_find_row_prefers_explicit_parenthetical_alias_over_shorter_substring(self) -> None:
        rows = [
            {"item": "净利润"},
            {"item": "归属于母公司股东的净利润"},
        ]

        row = find_row(
            rows,
            "归属于上市公司股东的净利润（归属于母公司股东的净利润）",
        )

        self.assertEqual(row, rows[1])

    def test_find_row_normalizes_optional_parenthetical_activity_wording(self) -> None:
        row = find_row(
            [{"item": "经营活动产生/(使用)的现金流量净额"}],
            "经营活动产生的现金流量净额",
        )

        self.assertEqual(row["item"], "经营活动产生/(使用)的现金流量净额")

    def test_find_row_uses_explicit_reported_label_aliases(self) -> None:
        row = find_row([{"item": "收入合計"}], "收入")

        self.assertEqual(row["item"], "收入合計")

    def test_find_row_matches_transliterated_label_without_value_guidance(self) -> None:
        row = find_row(
            [{"item": "經營活動所得現金流量淨額"}],
            "经营活动所得现金流量净额",
        )

        self.assertEqual(row["item"], "經營活動所得現金流量淨額")

    def test_find_row_collapses_only_identical_duplicate_values(self) -> None:
        duplicate_rows = [
            {"item": "淨利潤", "本期发生额": 2156356, "page": 10},
            {"item": "淨利潤", "本期发生额": 2156356, "page": 10},
        ]
        conflicting_rows = [
            {"item": "淨利潤", "本期发生额": 2156356, "page": 10},
            {"item": "淨利潤", "本期发生额": 2140000, "page": 10},
        ]

        self.assertEqual(find_row(duplicate_rows, "淨利潤"), duplicate_rows[0])
        self.assertIsNone(find_row(conflicting_rows, "淨利潤"))

    def test_diff_reads_current_period_value_from_statement_extraction(self) -> None:
        extracted = {
            "statements": {
                "合并利润表": [
                    {"item": "营业收入", "本期发生额": 155506421, "上期发生额": 146858174}
                ]
            }
        }
        oracle = {
            "key_items": [],
            "supplementary_lines": [{"item": "营业收入", "value": "155,506,421", "page": "90"}],
        }

        diff = diff_sample("sf_2026h1", extracted, oracle)

        self.assertEqual(diff["counts"], {"matched": 1, "mismatched": 0, "not_comparable": 0})
        self.assertEqual(diff["results"][0]["extracted_value"], 155506421)

    def test_diff_uses_period_end_value_for_balance_sheet_rows(self) -> None:
        extracted = {
            "statements": {
                "合并资产负债表": [
                    {"item": "资产总计", "期末余额": 228885266, "期初余额": 216469037}
                ]
            }
        }
        oracle = {
            "key_items": [],
            "supplementary_lines": [{"item": "资产总计", "value": "228,885,266", "page": "86"}],
        }

        diff = diff_sample("sf_2026h1", extracted, oracle)

        self.assertEqual(diff["counts"]["matched"], 1)
        self.assertEqual(diff["results"][0]["extracted_value"], 228885266)

    def test_diff_scopes_duplicate_item_names_to_oracle_statement(self) -> None:
        extracted = {
            "statements": {
                "合并利润表": [{"item": "少数股东损益", "本期发生额": 468112}],
                "合并综合收益表": [{"item": "少数股东损益", "本期发生额": 522239}],
            }
        }
        oracle = {
            "key_items": [],
            "supplementary_lines": [
                {
                    "statement": "合并利润表",
                    "item": "少数股东损益",
                    "value": "468,112",
                    "page": "90",
                }
            ],
        }

        diff = diff_sample("sf_2026h1", extracted, oracle)

        self.assertEqual(diff["counts"]["matched"], 1)
        self.assertEqual(diff["results"][0]["extracted_value"], 468112)


if __name__ == "__main__":
    unittest.main()
