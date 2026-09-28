from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.build_public_financial_sample_freeze import build_manifest, write_manifest

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTATION_SHA = "eb2b7f3cbadec0c36eb4b36473c6321d69aa4fff"
FREEZE_PATH = ROOT / "validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml"


class PublicFinancialSampleFreezeTests(unittest.TestCase):
    def test_financial_report_registry_is_valid_yaml(self) -> None:
        registry = ROOT / "validation/financial_reports/manifest.yaml"
        self.assertIsInstance(yaml.safe_load(registry.read_text(encoding="utf-8")), dict)

    def test_registered_oracle_files_are_valid_yaml(self) -> None:
        oracle_dir = ROOT / "validation/financial_reports/oracle"
        for oracle in sorted(oracle_dir.glob("*.yaml")):
            with self.subTest(oracle=oracle.name):
                self.assertIsInstance(yaml.safe_load(oracle.read_text(encoding="utf-8")), dict)

    def test_registered_oracle_sha_claims_match_current_bytes(self) -> None:
        registry = yaml.safe_load(
            (ROOT / "validation/financial_reports/manifest.yaml").read_text(encoding="utf-8")
        )
        for holdout in registry["holdouts"]:
            precise = next(
                value
                for key, value in holdout.items()
                if key.startswith("key_items_precise_") and isinstance(value, dict)
            )
            oracle_path = ROOT / precise["oracle_file"]
            with self.subTest(sample=holdout["id"]):
                self.assertEqual(
                    hashlib.sha256(oracle_path.read_bytes()).hexdigest(),
                    precise["oracle_sha256"],
                )

    def test_freeze_audits_oracle_and_holdout_limits_without_claiming_c_level(self) -> None:
        manifest = build_manifest(ROOT, implementation_sha=IMPLEMENTATION_SHA)
        audit = manifest["independent_validation"]

        self.assertEqual(audit["full_row_oracles_for_frozen_reports"], 0)
        self.assertEqual(audit["registered_holdout_oracles"], 5)
        self.assertEqual(audit["legacy_first_run"]["total"], 199)
        self.assertEqual(audit["legacy_first_run"]["rows_extracted"], 0)
        self.assertEqual(audit["legacy_first_run"]["not_comparable"], 199)
        self.assertEqual(audit["oracle_claim_mismatches"], [])
        self.assertEqual(
            audit["historical_oracle_claim_mismatches"],
            ["alibaba_fy2027q1", "xiaomi_2026h1"],
        )
        self.assertFalse(manifest["c_level_passed"])

    def test_manifest_freezes_all_fourteen_report_identities_and_coverage(self) -> None:
        manifest = build_manifest(ROOT, implementation_sha=IMPLEMENTATION_SHA)

        self.assertEqual(manifest["implementation_sha"], IMPLEMENTATION_SHA)
        self.assertEqual(manifest["report_count"], 14)
        self.assertEqual(len(manifest["reports"]), 14)
        self.assertEqual(manifest["coverage"]["l0_values"], 1532)
        self.assertEqual(manifest["coverage"]["l1_values"], 1776)
        self.assertEqual(manifest["coverage"]["l1_located"], 1776)
        self.assertEqual(manifest["coverage"]["l1_unlocated"], 0)

        baba_periods = [
            row
            for row in manifest["reports"]
            if row["sample"] in {"alibaba_2019fy", "alibaba_2020fy"}
        ]
        self.assertEqual(len(baba_periods), 2)
        self.assertEqual(len({row["source_pdf"] for row in baba_periods}), 1)
        self.assertEqual(len({row["period_label"] for row in baba_periods}), 2)
        self.assertNotEqual(baba_periods[0]["l1_values"], 0)
        self.assertNotEqual(baba_periods[1]["l1_values"], 0)

    def test_checked_in_manifest_is_deterministic_and_all_hashes_match(self) -> None:
        expected = build_manifest(ROOT, implementation_sha=IMPLEMENTATION_SHA)
        generator = ROOT / "scripts/build_public_financial_sample_freeze.py"
        self.assertEqual(
            expected["inputs"]["freeze_generator"]["sha256"],
            hashlib.sha256(generator.read_bytes()).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "freeze.yaml"
            write_manifest(expected, output)
            self.assertEqual(FREEZE_PATH.read_bytes(), output.read_bytes())

        for row in expected["reports"]:
            source_pdf = ROOT / row["source_pdf"]
            source_yaml = ROOT / row["active_yaml"]
            self.assertEqual(
                hashlib.sha256(source_pdf.read_bytes()).hexdigest(),
                row["source_pdf_sha256"],
            )
            self.assertEqual(
                hashlib.sha256(source_yaml.read_bytes()).hexdigest(),
                row["active_yaml_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
