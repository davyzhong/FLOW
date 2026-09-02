from __future__ import annotations

import json
import sys
from pathlib import Path


def read_dashboard(payload_path: str) -> dict[str, object]:
    path = Path(payload_path)
    if path.suffix != ".json" or not path.is_file():
        raise SystemExit(f"需要一个已存在的仪表盘 overview JSON 文件，收到: {payload_path!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    payload = read_dashboard(sys.argv[1] if len(sys.argv) > 1 else "")
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
