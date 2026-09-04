from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.summarize_dashboard import read_dashboard


class SummarizeDashboardTests(unittest.TestCase):
    def test_read_dashboard_uses_the_captured_json_file(self) -> None:
        payload = {"state": "ready", "context": {"batch_id": "演示批次"}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overview.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(read_dashboard(str(path)), payload)

    def test_missing_files_and_urls_are_rejected(self) -> None:
        for value in ("", "/missing/overview.json", "https://example.com/overview.json"):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                read_dashboard(value)


if __name__ == "__main__":
    unittest.main()
