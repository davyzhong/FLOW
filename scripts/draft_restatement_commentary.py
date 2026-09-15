#!/usr/bin/env python3
"""T10-B6：重述差异说明起草（确定性，无模型参与）。

D054 原则的 v1 工程化：叙事全部由确定性引擎输出组装——每个数字都来自
重述差异计算（compute_diff）或事实库，零模型生成；每段附证据引用
（报告版本 id + 行项目 + 列）。后续「AI 润色/扩展」只能在此草稿之上追加
非数字叙事，且正式数字通道仍走确定性引擎（一致性检查由 L0/L1 基准守门）。

用法：
  python3 scripts/draft_restatement_commentary.py --stock-code 002352.SZ \\
      --period-label 2026Q1 [--report-kind 一季报]
退出码：0 = 出稿；2 = 无可比版本。
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "services/api" / "src"))

import statement_restatement_diff as diff_mod  # noqa: E402


def _fmt(value: str | None) -> str:
    if value is None:
        return "（无值）"
    return str(Decimal(value).normalize())


def draft(stock_code: str, period_label: str, report_kind: str | None) -> dict | None:
    diff = diff_mod.compute_diff(stock_code, period_label, report_kind)
    if diff is None:
        return None
    chain = diff["supersedes_chain"]

    lines: list[str] = []
    lines.append(
        f"# 重述差异说明：{stock_code} {period_label}"
        f"{('（' + report_kind + '）') if report_kind else ''}"
    )
    lines.append("")
    lines.append(
        f"本说明由确定性引擎自动起草（数字未经任何模型生成），"
        f"重述链 v{chain['superseded_version']} → v{chain['current_version']}；"
        f"被取代版本 id `{chain['superseded_id']}`，当前版本 id `{chain['current_id']}`。"
    )
    lines.append("")

    changed = diff["changed"]
    if changed:
        lines.append(f"## 数值变更（{len(changed)} 处）")
        lines.append("")
        for item in changed:
            key = item["key"]
            lines.append(
                f"- {key[0]}「{key[1]}」（第 {key[2] + 1} 行，{key[3]} 列）："
                f"{_fmt(item['old'])} → {_fmt(item['new'])}"
                + (f"（变动 {item['delta']}）" if item["delta"] else "")
            )
        lines.append("")

    if diff["added"]:
        lines.append(f"## 新增行（{len(diff['added'])} 处）")
        lines.append("")
        for item in diff["added"][:20]:
            key = item["key"]
            lines.append(f"- {key[0]}「{key[1]}」{key[3]} 列 = {_fmt(item.get('new'))}")
        lines.append("")

    if diff["removed"]:
        lines.append(f"## 删除行（{len(diff['removed'])} 处）")
        lines.append("")
        for item in diff["removed"][:20]:
            key = item["key"]
            lines.append(f"- {key[0]}「{key[1]}」{key[3]} 列（原 {_fmt(item.get('old'))}）")
        lines.append("")

    if not (changed or diff["added"] or diff["removed"]):
        lines.append("两版本数值完全一致，差异仅出现在非数值元数据。")
        lines.append("")

    lines.append("---")
    lines.append(
        "证据引用：全部数值来自事实库相邻版本比对"
        "（scripts/statement_restatement_diff.py compute_diff）；"
        "发布前须经分专员人工终审（AI 不得自行发布）。"
    )
    return {"markdown": "\n".join(lines), "diff": diff}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-code", required=True)
    parser.add_argument("--period-label", required=True)
    parser.add_argument("--report-kind", default=None)
    args = parser.parse_args()

    result = draft(args.stock_code, args.period_label, args.report_kind)
    if result is None:
        print("找不到同身份的两个版本（无重述可比）", file=sys.stderr)
        return 2
    print(result["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
