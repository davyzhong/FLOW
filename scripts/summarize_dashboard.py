from __future__ import annotations

import json
import sys
import urllib.request

# 本工具只服务本机运行栈（test_dashboard.sh）：主机为字面常量，仅允许通过
# int 类型的端口参数指向本机仪表盘，不存在外部输入进入 URL 主机的路径。
DASHBOARD_URL_TEMPLATE = "http://127.0.0.1:{port}/api/v1/dashboard/overview"
DEFAULT_PORT = 13100


def read_dashboard(port: int) -> dict[str, object]:
    with urllib.request.urlopen(DASHBOARD_URL_TEMPLATE.format(port=port), timeout=60) as response:
        return json.load(response)


def main() -> None:
    port = DEFAULT_PORT
    if len(sys.argv) > 1 and sys.argv[1].strip():
        port = int(sys.argv[1])  # 只接受纯端口数字，拒绝任何 URL 形态的外部输入
    payload = read_dashboard(port)
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
