from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from scripts.summarize_dashboard import read_dashboard


class SummarizeDashboardTests(unittest.TestCase):
    def test_read_dashboard_allows_for_first_request_compilation(self) -> None:
        payload = {
            "state": "ready",
            "context": {
                "batch_id": "batch",
                "metric_snapshot_id": "snapshot",
                "analysis_run_id": "run",
            },
            "metric_cards": [{}] * 8,
            "trends": {"coverage_count": 12},
            "findings": [{}] * 4,
            "product_table": {"rows": [{}] * 8},
        }

        with patch(
            "scripts.summarize_dashboard.urllib.request.urlopen",
            return_value=io.BytesIO(json.dumps(payload).encode("utf-8")),
        ) as urlopen:
            actual = read_dashboard(3000)

        self.assertEqual(actual, payload)
        self.assertEqual(
            urlopen.call_args.args[0],
            "http://127.0.0.1:3000/api/v1/dashboard/overview",
        )
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 60)


if __name__ == "__main__":
    unittest.main()
