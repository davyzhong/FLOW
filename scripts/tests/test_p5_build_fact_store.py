from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.p5_build_fact_store import build_from_yaml, build_jdl_full, load_alias


class UnconfiguredStatementRetentionTest(unittest.TestCase):
    def test_unconfigured_statement_rows_are_preserved_as_unmapped(self) -> None:
        import yaml

        payload = {
            "statements": {
                "合并利润表": [
                    {"item": "收入", "本期发生额": 100, "上期发生额": 90}
                ],
                "合并综合收益表": [
                    {"item": "其他综合收益", "本期发生额": 12, "上期发生额": -3},
                    {"item": "表头", "本期发生额": None, "上期发生额": None},
                ],
            }
        }
        alias = {
            "companies": {
                "example": {
                    "statements": {
                        "合并利润表": {
                            "roles": {"本期发生额": "cur", "上期发生额": "prev_yoy"},
                            "map": {"收入": "is.revenue"},
                        }
                    }
                }
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "extraction.yaml"
            source.write_text(
                yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8"
            )
            facts, unmapped = build_from_yaml(
                "example",
                "FY2025",
                str(source),
                "fixture.pdf",
                "元",
                alias,
                spec_key="example",
            )

        self.assertEqual(len(facts), 2)
        self.assertEqual(len(unmapped), 1)
        self.assertEqual(unmapped[0]["statement"], "合并综合收益表")
        self.assertEqual(unmapped[0]["item"], "其他综合收益")
        self.assertIn("报表类型未配置", unmapped[0]["reason"])

    def test_jdl_v3_comprehensive_income_rows_keep_their_statement_type(self) -> None:
        _facts, unmapped = build_jdl_full(load_alias())
        comprehensive_rows = [
            row for row in unmapped if row["statement"] == "合并综合收益表"
        ]

        self.assertEqual(len(comprehensive_rows), 9)
        self.assertTrue(
            all("报表类型未配置" in row["reason"] for row in comprehensive_rows)
        )


if __name__ == "__main__":
    unittest.main()
