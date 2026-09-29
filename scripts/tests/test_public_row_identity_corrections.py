from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import unittest
from pathlib import Path

import yaml

import scripts.build_public_c_level_ledgers as ledger_builder
from scripts.build_answer_set_l1 import build as build_l1_answer_set


class PublicRowIdentityCorrectionTests(unittest.TestCase):
    def _apply(self, payload: dict) -> dict:
        try:
            adapter = importlib.import_module("scripts.public_statement_row_identity")
        except ModuleNotFoundError:
            self.fail("应提供版本化行身份修订适配器")
        return adapter.apply_public_row_identity_corrections(payload)

    def test_runtime_correction_adapter_exists(self) -> None:
        self.assertIsNotNone(
            importlib.util.find_spec("scripts.public_statement_row_identity"),
            "seed、L0/L1 与 P5 应通过同一版本化行身份适配器",
        )

    def test_versioned_row_identity_corrections_exist(self) -> None:
        root = Path(__file__).resolve().parents[2]
        corrections = root / "validation/financial_reports/corrections/public-row-identity-map-v1.csv"
        self.assertTrue(corrections.is_file(), "应存在不可变原件之外的版本化行身份修订层")

    def test_alibaba_identity_overrides_keep_values_and_expand_source_row_scope(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source_path = root / "docs/implementation/p5/alibaba_2020fy_statements.yaml"
        payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        before = json.dumps(payload["statements"], ensure_ascii=False, sort_keys=True)
        corrected = self._apply(payload)
        self.assertEqual(
            json.dumps(payload["statements"], ensure_ascii=False, sort_keys=True), before
        )
        cash_rows = corrected["statements"]["合并现金流量表"]
        self.assertIn(
            "匯率變動對現金及現金等價物、受限制現金及應收託管資金的影響",
            {row["item"] for row in cash_rows},
        )
        self.assertIn(
            "流动资产：證券投資",
            {row["item"] for row in corrected["statements"]["合并资产负债表"]},
        )
        original_rows = payload["statements"]["合并现金流量表"]
        original = next(row for row in original_rows if row["item"] == "匯率變動對現金的影響")
        updated = next(
            row for row in cash_rows
            if row["item"] == "匯率變動對現金及現金等價物、受限制現金及應收託管資金的影響"
        )
        self.assertEqual(
            {key: value for key, value in original.items() if key not in {"item", "page", "source_text_label"}},
            {key: value for key, value in updated.items() if key not in {"item", "page", "source_text_label"}},
        )
        self.assertEqual(updated["page"], 43)

    def test_cainiao_overrides_disambiguate_noncurrent_groups_and_pin_source_pages(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source_path = root / "docs/implementation/p5/cainiao_2023fy_statements.yaml"
        payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        corrected = self._apply(payload)
        rows = corrected["statements"]["合并资产负债表"]
        asset = next(row for row in rows if row["item"] == "非流动资产：按公允价值计量的金融资产")
        liability = next(row for row in rows if row["item"] == "非流动负债：借款")
        self.assertEqual(asset["page"], 466)
        self.assertEqual(liability["page"], 467)

    def test_adapter_fails_closed_when_candidate_values_do_not_match(self) -> None:
        root = Path(__file__).resolve().parents[2]
        payload = yaml.safe_load(
            (root / "docs/implementation/p5/alibaba_2020fy_statements.yaml").read_text(encoding="utf-8")
        )
        row = next(
            item for item in payload["statements"]["合并现金流量表"]
            if item["item"] == "匯率變動對現金的影響"
        )
        row["本期发生额"] += 1
        with self.assertRaisesRegex(ValueError, "未能唯一匹配来源行"):
            self._apply(payload)

    def test_l1_builder_emits_v5_scoped_row_anchors(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temporary:
            payload = build_l1_answer_set(
                Path(temporary) / "answer-set.yaml",
                version=5,
                supersedes="config/statements/answer_set_l1_v4.yaml",
            )
        entries = payload["entries"]
        cash_matches = [
            row for row in entries
            if row["source_pdf"].endswith("BABA_FY2020_annual_results.pdf")
            and row["period_label"] == "FY2020"
            and row["item"].startswith("匯率變動對現金及現金等價物")
            and row["column"] == "本期发生额"
        ]
        cainiao_matches = [
            row for row in entries
            if row["source_pdf"].endswith("Cainiao_application_proof_20230926.pdf")
            and row["period_label"] == "FY2023"
            and row["item"] == "非流动资产：按公允价值计量的金融资产"
            and row["column"] == "本期发生额"
        ]
        self.assertEqual(len(cash_matches), 1)
        self.assertEqual(len(cainiao_matches), 1)
        cash = cash_matches[0]
        cainiao = cainiao_matches[0]
        self.assertEqual(
            (payload["version"], payload["supersedes"]),
            (5, "config/statements/answer_set_l1_v4.yaml"),
        )
        self.assertEqual((cash["match_mode"], cash["page"]), ("strong", 43))
        self.assertEqual((cainiao["match_mode"], cainiao["page"]), ("strong", 466))
        self.assertEqual(payload["coverage"]["values_total"], 1776)
        self.assertEqual(payload["coverage"]["values_located"], 1776)

    def test_identity_map_is_derived_from_adjudicated_candidates(self) -> None:
        self.assertTrue(hasattr(ledger_builder, "public_row_identity_map_v1"))
        rows = ledger_builder.public_row_identity_map_v1()
        self.assertEqual(len(rows), 40)
        self.assertEqual(sum(int(row["candidate_cells"]) for row in rows), 79)
        self.assertEqual(len({(row["source_pdf"], row["statement"], row["source_item"]) for row in rows}), 40)
        baba = next(
            row for row in rows
            if row["report"] == "BABA_FY2020_annual_results"
            and row["statement"] == "合并资产负债表"
        )
        self.assertEqual(
            json.loads(baba["source_values_json"]),
            {"期初余额": "9927", "期末余额": "4234"},
        )
        self.assertEqual(baba["candidate_cells"], "2")
        self.assertEqual(baba["corrected_item"], "流动资产：證券投資")
        self.assertIn("sample", baba)
        self.assertEqual(baba["sample"], "alibaba_2020fy")

    def test_checked_in_identity_map_matches_rebuild_and_source_hashes(self) -> None:
        root = Path(__file__).resolve().parents[2]
        path = root / "validation/financial_reports/corrections/public-row-identity-map-v1.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            actual = list(csv.DictReader(handle))
        self.assertEqual(actual, ledger_builder.public_row_identity_map_v1())
        self.assertTrue(all("sample" in row for row in actual))
        for row in actual:
            self.assertEqual(ledger_builder.sha256(root / row["source_pdf"]), row["source_pdf_sha256"])
            if row["sample"] == "alibaba_2023fy":
                source_path = root / "validation/financial_reports/corrections/alibaba_2023fy_statements_v2.yaml"
            else:
                source_path = root / f"docs/implementation/p5/{row['sample']}_statements.yaml"
            payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
            source_rows = [
                item for item in payload["statements"][row["statement"]]
                if item["item"] == row["source_item"]
            ]
            self.assertEqual(len(source_rows), 1, row["sample"] + "/" + row["source_item"])
            expected_values = json.loads(row["source_values_json"])
            self.assertEqual(
                {key: str(source_rows[0][key]) for key in expected_values},
                expected_values,
                row["sample"] + "/" + row["source_item"],
            )


if __name__ == "__main__":
    unittest.main()
