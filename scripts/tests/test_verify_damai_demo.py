"""verify_damai_demo 纯函数契约测试（Task C1）。

覆盖不依赖数据库的部分：发行包 manifest 对账（真实 fixtures）与 verdict 聚合语义。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_damai_demo  # noqa: E402


class ReleaseManifestCheckTest(unittest.TestCase):
    def test_real_release_package_passes(self) -> None:
        checks = verify_damai_demo.check_release_manifest(ROOT)
        self.assertEqual({check["name"] for check in checks}, {
            "release_manifest.files",
            "release_manifest.row_counts",
        })
        for check in checks:
            self.assertTrue(check["passed"], f"{check['name']}: {check['detail']}")

    def test_missing_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checks = verify_damai_demo.check_release_manifest(Path(tmp))
        self.assertFalse(checks[0]["passed"])

    def test_tampered_file_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "fixtures/damai"
            package.mkdir(parents=True)
            data_file = package / "canonical/periods.jsonl"
            data_file.parent.mkdir(parents=True)
            data_file.write_text('{"month_key": "2024-09"}\n', encoding="utf-8")
            manifest = {
                "files": {"canonical/periods.jsonl": "0" * 64},
                "row_counts": {"canonical/periods.jsonl": 1},
            }
            (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            checks = verify_damai_demo.check_release_manifest(Path(tmp))
        by_name = {check["name"]: check for check in checks}
        self.assertFalse(by_name["release_manifest.files"]["passed"], "篡改必须被 SHA 检出")
        self.assertTrue(by_name["release_manifest.row_counts"]["passed"])


class SummarizeTest(unittest.TestCase):
    def test_ok_only_when_all_pass(self) -> None:
        checks = [
            {"name": "a", "passed": True, "detail": ""},
            {"name": "b", "passed": False, "detail": "boom"},
        ]
        verdict = verify_damai_demo.summarize(checks)
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["failed"], ["b"])
        self.assertEqual(verdict["total"], 2)

    def test_all_pass(self) -> None:
        verdict = verify_damai_demo.summarize([{"name": "a", "passed": True, "detail": ""}])
        self.assertTrue(verdict["ok"])
        self.assertEqual(verdict["failed"], [])


class LatestDamaiReportCountTest(unittest.TestCase):
    def test_historical_versions_do_not_inflate_current_report_count(self) -> None:
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE statement_report (stock_code TEXT, report_kind TEXT, "
                    "period_label TEXT, version INTEGER, status TEXT)"
                ))
                connection.execute(text(
                    "INSERT INTO statement_report VALUES "
                    "('DAMAI.SYN','年报','FY2025',1,'published'), "
                    "('DAMAI.SYN','年报','FY2025',2,'published'), "
                    "('DAMAI.SYN','年报','FY2026',1,'published'), "
                    "('OTHER','年报','FY2025',1,'published')"
                ))
                count = verify_damai_demo.count_latest_published_damai_reports(connection)
            self.assertEqual(count, 2)
        finally:
            engine.dispose()

    def test_latest_unpublished_version_is_not_counted_as_published(self) -> None:
        engine = create_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE statement_report (stock_code TEXT, report_kind TEXT, "
                    "period_label TEXT, version INTEGER, status TEXT)"
                ))
                connection.execute(text(
                    "INSERT INTO statement_report VALUES "
                    "('DAMAI.SYN','年报','FY2025',1,'published'), "
                    "('DAMAI.SYN','年报','FY2025',2,'draft'), "
                    "('DAMAI.SYN','年报','FY2026',1,'published')"
                ))
                count = verify_damai_demo.count_latest_published_damai_reports(connection)
            self.assertEqual(count, 1)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
