"""Fail-closed contracts for the U8 frozen-baseline acceptance gate."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.u8_acceptance_evidence import validate_evidence

REPO = Path(__file__).resolve().parents[2]


def valid_evidence(mode: str = "full") -> dict:
    return {
        "schema_version": 1,
        "mode": mode,
        "base_url": "https://localhost:3443",
        "tls_verified": True,
        "health_status": 200,
        "web_status": 200,
        "downloads": [
            {"expected_sha256": "a" * 64, "actual_sha256": "a" * 64},
            {"expected_sha256": "b" * 64, "actual_sha256": "b" * 64},
        ],
        "restore_exit_code": 0,
        "critical_tables": {
            "statement_report": {"before": 11, "after": 11},
            "objective_report_snapshot": {"before": 12, "after": 12},
        },
        "expected_payload_hash": "c" * 64,
        "restored_payload_hash": "c" * 64,
        "skipped": [],
    }


class EvidenceValidationTests(unittest.TestCase):
    def assert_invalid(self, mutation, fragment: str) -> None:
        evidence = valid_evidence()
        mutation(evidence)
        self.assertIn(fragment, " ".join(validate_evidence(evidence)))

    def test_valid_full_and_restore_modes_pass(self) -> None:
        self.assertEqual(validate_evidence(valid_evidence("full")), [])
        restore = valid_evidence("restore-u8-baseline")
        restore["downloads"] = []
        self.assertEqual(validate_evidence(restore), [])

    def test_https_url_and_tls_are_required(self) -> None:
        self.assert_invalid(lambda e: e.update(base_url="http://localhost:8000"), "https")
        self.assert_invalid(lambda e: e.update(tls_verified=False), "TLS")

    def test_every_download_sha_must_match(self) -> None:
        self.assert_invalid(
            lambda e: e["downloads"][0].update(actual_sha256="d" * 64), "SHA-256"
        )
        self.assert_invalid(lambda e: e.update(downloads=[]), "download")

    def test_restore_and_critical_tables_must_match(self) -> None:
        self.assert_invalid(lambda e: e.update(restore_exit_code=1), "pg_restore")
        self.assert_invalid(
            lambda e: e["critical_tables"]["statement_report"].update(after=10),
            "critical table",
        )

    def test_payload_hash_and_health_must_match(self) -> None:
        self.assert_invalid(lambda e: e.update(restored_payload_hash="d" * 64), "payload hash")
        self.assert_invalid(lambda e: e.update(health_status=503), "health")

    def test_skips_are_never_accepted(self) -> None:
        self.assert_invalid(lambda e: e.update(skipped=["application health"]), "skip")

    def test_unknown_mode_fails(self) -> None:
        self.assert_invalid(lambda e: e.update(mode="maybe"), "mode")


class AcceptanceScriptContractTests(unittest.TestCase):
    def run_gate(self, mode: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        merged = dict(os.environ)
        merged.update(env or {})
        return subprocess.run(
            ["bash", "scripts/accept_u8_production.sh", mode],
            cwd=REPO,
            env=merged,
            text=True,
            capture_output=True,
        )

    def test_full_requires_explicit_https_base_url(self) -> None:
        proc = self.run_gate("full", {"FLOW_U8_BASE_URL": ""})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("FLOW_U8_BASE_URL", proc.stdout + proc.stderr)

    def test_restore_mode_requires_backup_and_isolated_database(self) -> None:
        proc = self.run_gate(
            "restore-u8-baseline",
            {
                "FLOW_U8_BASE_URL": "https://localhost:3443",
                "FLOW_U8_BACKUP_PATH": "",
                "FLOW_U8_RESTORE_DATABASE": "",
            },
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("FLOW_U8_BACKUP_PATH", proc.stdout + proc.stderr)

    def test_unknown_mode_fails(self) -> None:
        proc = self.run_gate("unknown", {"FLOW_U8_BASE_URL": "https://localhost:3443"})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unknown mode", (proc.stdout + proc.stderr).lower())


class DownloadVerifierTests(unittest.TestCase):
    def test_empty_attempts_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            attempts = Path(tmp) / "attempts.json"
            summary = Path(tmp) / "summary.json"
            attempts.write_text('{"attempts": []}', encoding="utf-8")
            proc = subprocess.run(
                [
                    "python3",
                    "scripts/u8a_download_attempts.py",
                    str(attempts),
                    str(summary),
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(json.loads(summary.read_text(encoding="utf-8")), {"downloads": []})


class JourneyEvidenceTests(unittest.TestCase):
    def test_checked_in_jsonl_is_machine_readable(self) -> None:
        evidence = REPO / "docs/operations/u8a-journey-evidence.jsonl"
        for line_number, line in enumerate(evidence.read_text(encoding="utf-8").splitlines(), 1):
            with self.subTest(line=line_number):
                json.loads(line)

    def test_restore_script_cannot_swallow_restore_or_health_failure(self) -> None:
        source = (REPO / "scripts/backup_restore_drill.sh").read_text(encoding="utf-8")
        self.assertNotIn("pg_restore -U flow -d flow --no-owner 2>&1 | grep -v 'already exists' || true", source)
        self.assertNotIn("跳过应用层健康检查", source)

    def test_api_image_contains_pinned_chromium_runtime_for_pdf(self) -> None:
        source = (REPO / "infra/api.Dockerfile").read_text(encoding="utf-8")
        self.assertIn("chromium", source)
        self.assertIn("chromium-sandbox", source)
        self.assertIn("FLOW_CHROMIUM_PATH", source)
        self.assertIn("/usr/bin/chromium", source)


if __name__ == "__main__":
    unittest.main()
