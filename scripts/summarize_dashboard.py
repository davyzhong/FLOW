from __future__ import annotations

import json
import sys
import urllib.request


def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:13100"
    with urllib.request.urlopen(
        f"{base_url}/api/v1/dashboard/overview", timeout=15
    ) as response:
        payload = json.load(response)
    summary = {
        "state": payload["state"],
        "batch_id": payload["context"]["batch_id"],
        "metric_snapshot_id": payload["context"]["metric_snapshot_id"],
        "analysis_run_id": payload["context"]["analysis_run_id"],
        "metric_cards": len(payload["metric_cards"]),
        "trend_months": payload["trends"]["coverage_count"],
        "findings": len(payload["findings"]),
        "products": len(payload["product_table"]["rows"]),
    }
    if summary["state"] != "ready" or summary["metric_cards"] != 8:
        raise SystemExit(f"dashboard readiness check failed: {summary}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
