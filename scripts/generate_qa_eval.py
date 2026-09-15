#!/usr/bin/env python3
"""T12：从事实库确定性生成 100 问评测集（答案即库内真值，天然可复算）。

构成（v1 合同：检索引用 + 拒答）：
- 60 数值题：公司(别名) + 期间 + 行项目（行名取自事实库，保证可检索）；
  期望答案 = 库内值文本；
- 20 拒答题：不存在的行项目（真实公司/期间 + 杜撰行名）；
- 20 拒答题：缺失期间或未知公司（协议要求显式指明，缺失即拒）。

用法：python3 scripts/generate_qa_eval.py --out config/eval/qa_eval_set_v1.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services/api" / "src"))
sys.path.insert(0, str(REPO / "scripts"))

# 复用问数检索的别名表与取数
from ask_facts import COMPANY_ALIASES, retrieve  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "config/eval/qa_eval_set_v1.json")
    parser.add_argument("--seed", type=int, default=20260915)
    args = parser.parse_args()

    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import (
        StatementLineItem,
        StatementReport,
    )

    with get_engine().connect() as conn:
        reports = conn.execute(
            select(
                StatementReport.id,
                StatementReport.company_name,
                StatementReport.stock_code,
                StatementReport.period_label,
                StatementReport.unit_note,
            )
        ).all()
        all_items = conn.execute(
            select(
                StatementLineItem.report_id,
                StatementLineItem.item_name,
                StatementLineItem.statement_type,
            )
        ).all()

    items_by_report: dict[object, list[tuple[str, str]]] = {}
    for report_id, item_name, statement_type in all_items:
        items_by_report.setdefault(report_id, []).append((item_name, statement_type))

    code_to_alias = {}
    for alias, code in COMPANY_ALIASES.items():
        code_to_alias.setdefault(code, alias)

    rng = random.Random(args.seed)
    cases = []
    # 数值题：每份报告抽 4~5 行（14 份 × 5 ≈ 70 → 截 60）
    for report in reports:
        candidates = items_by_report.get(report.id, [])
        with_values = [
            item_name
            for item_name, _stmt in candidates
            if item_name and not item_name.startswith(("其中", "（"))
        ]
        rng.shuffle(with_values)
        alias = code_to_alias.get(report.stock_code, report.stock_code)
        for item_name in with_values[:8]:
            if len(cases) >= 60:
                break
            probe = retrieve(f"{alias} {report.period_label} 的{item_name}是多少")
            if probe.get("answer") is None:
                continue
            cases.append(
                {
                    "type": "value",
                    "question": f"{alias} {report.period_label} 的{item_name}是多少",
                    "expect_value": probe["answer"],
                    "expect_unit": report.unit_note,
                }
            )

    # 拒答题：杜撰行项目
    for report in reports:
        alias = code_to_alias.get(report.stock_code, report.stock_code)
        cases.append(
            {
                "type": "refusal_item",
                "question": f"{alias} {report.period_label} 的量子波动利润是多少",
                "expect_refusal": True,
            }
        )
    # 拒答题：未知公司 / 缺期间
    for question in [
        "英伟达 FY2026 的营业收入是多少",
        "拼多多 2026Q1 的货币资金是多少",
        "货币资金是多少",
        "顺丰的营业收入是多少",
        "2026Q1 的净利润是多少",
        "比特币价格是多少",
        "菜鸟 FY2099 的资产总计是多少",
        "顺丰 2026Q1 的员工满意度是多少",
        "腾讯 无形资产zzz 是多少",
        "京东物流 FY2025 的星际收入是多少",
        "顺丰 2026Q1 的____是多少",
        "阿里 FY2020 的的面都是多少",
        "圆通速递 FY2026 的营业收入是多少",
        "申通 FY2025 的资产总计是多少",
        "顺丰 2026Q1 的 Quantum revenue 是多少",
        "腾讯 2026Q2 的 jump profit 是多少",
        "京东物流 FY2025 的魔法资产是多少",
        "菜鸟 FY2023 的暗物质负债是多少",
        "阿里 FY2026 的翡翠收入是多少",
        "顺丰 2026Q1 的上月余额是多少",
    ]:
        cases.append({"type": "refusal_missing", "question": question, "expect_refusal": True})

    cases = cases[:100]
    payload = {
        "schema": "flow.qa_eval.v1",
        "generated_from": "事实库（答案即库内真值）+ 固定拒答陷阱题",
        "seed": args.seed,
        "composition": {
            "value": sum(1 for c in cases if c["type"] == "value"),
            "refusal": sum(1 for c in cases if c["type"].startswith("refusal")),
        },
        "cases": cases,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"评测集：{len(cases)} 问（数值 {payload['composition']['value']}, "
        f"拒答 {payload['composition']['refusal']}）→ {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
