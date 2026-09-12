#!/usr/bin/env python3
"""从 metric_dictionary v1.1 生成人读内部指标库文档（Markdown）。

用法：cd services/api && .venv/bin/python ../../scripts/generate_metric_library_doc.py
输入：config/metrics/metric_dictionary_v1_1.yaml
输出：docs/implementation/metric-library-v1.1.md
"""
from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "config/metrics/metric_dictionary_v1_1.yaml"
OUT = ROOT / "docs/implementation/metric-library-v1.1.md"

DOMAIN_ORDER = ["profitability", "solvency", "operation", "cashflow", "growth", "value", "scale"]
DIMENSION_LABELS = {
    "trend": "趋势", "structure": "结构", "benchmark": "对标", "warning": "预警",
    "dupont": "杜邦归因", "cash_link": "现金勾稽", "value": "价值评估",
}
TIER_LABELS = {"core": "常用", "professional": "专业"}


def main() -> int:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    entries = data["metrics_general"] + data["metrics_logistics"]
    domains: dict[str, str] = data["domains"]

    lines: list[str] = [
        "# FLOW 内部财务指标库 v1.1",
        "",
        f"- 字典：`{data['dictionary_id']}`（{data.get('revision', 'v1.1')}，{len(entries)} 条 = 通用 {len(data['metrics_general'])} + 物流 {len(data['metrics_logistics'])}）",
        f"- 决策依据：{data['decision_ref']}",
        "- 四要素：每个指标含 (a) 常用/专业分层、(b) 计算公式（结构化 formula + text）、(c) 分析维度、(d) 底层依赖指标（depends_on + 报表项目取数）。",
        "- 分析维度词表：趋势（多期方向）、结构（构成/拆解）、对标（行业/预算/标杆）、预警（阈值监控）、杜邦归因（因子分解）、现金勾稽（利润-现金验证）、价值评估（相对资本成本）。",
        "- 本文档由 `scripts/generate_metric_library_doc.py` 从 YAML 机械生成；治理以 YAML + 指标库界面为准。",
        "",
    ]

    tier_stats = {"core": 0, "professional": 0}
    for e in entries:
        tier_stats[e.get("tier", "professional")] += 1
    lines += [
        f"分层统计：常用 {tier_stats['core']} 条 / 专业 {tier_stats['professional']} 条。",
        "",
    ]

    by_domain: OrderedDict[str, list[dict]] = OrderedDict()
    for e in entries:
        by_domain.setdefault(e["domain"], []).append(e)

    for domain in [d for d in DOMAIN_ORDER if d in by_domain] + [d for d in by_domain if d not in DOMAIN_ORDER]:
        label = domains.get(domain, domain)
        items = sorted(by_domain[domain], key=lambda x: (x.get("tier") != "core", x["metric_code"]))
        lines += [f"## {label}（{len(items)} 条）", ""]
        lines += ["| 指标 | code | 分层 | 公式 | 分析维度 | 底层依赖 |", "|---|---|---|---|---|---|"]
        for e in items:
            tier = TIER_LABELS.get(e.get("tier", "professional"), "专业")
            dims = "、".join(DIMENSION_LABELS.get(d, d) for d in e.get("analysis_dimensions", [])) or "—"
            deps = e.get("depends_on") or []
            deps_txt = "、".join(deps) if deps else "报表项目直取"
            name = e["name"] + ("（MPM）" if e.get("mpm") else "")
            lines.append(f"| {name} | `{e['metric_code']}` | {tier} | {e['formula_text']} | {dims} | {deps_txt} |")
        lines.append("")
        # 逐条要点（口径与警告）
        special = [e for e in items if e.get("benchmark") or e.get("alternative_calibers")]
        if special:
            lines += [f"### {label}·口径与解读要点", ""]
            for e in special:
                bits = []
                if e.get("benchmark"):
                    bits.append(f"解读：{e['benchmark']}")
                if e.get("alternative_calibers"):
                    bits.append(f"备选口径：{'；'.join(e['alternative_calibers'])}")
                lines.append(f"- **{e['name']}**：{'；'.join(bits)}")
            lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written {OUT.name} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
