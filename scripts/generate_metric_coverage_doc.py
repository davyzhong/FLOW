#!/usr/bin/env python3
"""生成指标执行覆盖清单（C02 证据，机器生成勿手改）。

用法：cd services/api && uv run python ../../scripts/generate_metric_coverage_doc.py
"""
from pathlib import Path

from flow_api.metric_library_store.binding import (
    ExecutionKind,
    build_execution_binding,
    coverage_summary,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "docs/implementation/objective-analysis/metric-execution-coverage.md"

KIND_LABELS = {
    ExecutionKind.ENGINE: "引擎执行（库内目录）",
    ExecutionKind.FACTS: "事实 AST 执行",
    ExecutionKind.NARRATIVE: "叙述定义（暂不执行）",
}


def main() -> int:
    bindings = build_execution_binding()
    summary = coverage_summary(bindings)
    lines = [
        "# 指标执行覆盖清单（C02）",
        "",
        f"- 生成：2026-09-06，由 `scripts/generate_metric_coverage_doc.py` 机械生成",
        f"- 总数：{summary['total']}；engine（指标引擎）：{summary['engine']}；"
        f"facts（事实 AST）：{summary['facts']}；narrative（暂不执行）：{summary['narrative']}",
        "- 对等性门禁：`tests/metrics/test_dictionary_execution_parity.py`（同指标同输入双路径一致 + 本清单防漂移）",
        "",
        "| 指标 | 名称 | 集合 | 绑定 | 执行器 / 缺失原因 |",
        "|---|---|---|---|---|",
    ]
    for binding in bindings:
        executor = binding.executor or binding.reason or "—"
        lines.append(
            f"| `{binding.metric_code}` | {binding.name} | {binding.collection} "
            f"| {KIND_LABELS[binding.kind]} | {executor} |"
        )
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
