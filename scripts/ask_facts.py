#!/usr/bin/env python3
"""T12：AI 问数 v1（检索引用型，确定性实现）。

v1 合同（docs/50_plans/work_items/PUBLIC--ai-qa-v1.md）：
- 问题 → 事实检索（公司 × 行项目 × 期间）→ 组织答案；
- 每个答案必须附事实引用（报告 id / 原文路径 / PDF 页锚）；
- 无事实支撑 → 显式拒答（refusal），绝不编造。

实现说明：v1 的检索与组织完全确定性（无模型调用）；同形输入永远同答，
评测可复现。多轮/计算类问题不在 v1 范围。

用法：
  python3 scripts/ask_facts.py --question "顺丰 2026Q1 的货币资金是多少"
  python3 scripts/ask_facts.py --eval config/eval/qa_eval_set_v1.json   # 评测
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services/api" / "src"))

# 公司别名 → stock_code（数据集规模小，静态表即可；扩数据集时迁移到 DB 配置）
COMPANY_ALIASES = {
    "顺丰": "002352.SZ",
    "sf": "002352.SZ",
    "阿里巴巴": "9988.HK",
    "阿里": "9988.HK",
    "baba": "9988.HK",
    "腾讯": "0700.HK",
    "tencent": "0700.HK",
    "京东物流": "2618.HK",
    "jdl": "2618.HK",
    "菜鸟": "PVT.CAINIAO",
    "圆通": "600233.SH",
}

# 常见期间写法归一
PERIOD_ALIASES = {
    "2026q1": "2026Q1",
    "2026q2": "2026Q2",
    "fy2026": "FY2026",
    "fy2025": "FY2025",
    "fy2024": "FY2024",
    "fy2023": "FY2023",
    "fy2022": "FY2022",
    "fy2021": "FY2021",
    "fy2020": "FY2020",
    "fy2019": "FY2019",
}

COLUMNS = ("value_end", "value_begin", "value_current", "value_prior")
COLUMN_LABELS = {
    "value_end": "期末余额",
    "value_begin": "期初余额",
    "value_current": "本期发生额",
    "value_prior": "上期发生额",
}


def _norm(text: str) -> str:
    return text.replace(" ", "").lower()


def retrieve(question: str) -> dict:
    """确定性检索：返回答案 dict（answer / refusal + citations）。"""
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import (
        StatementLineItem,
        StatementReport,
    )

    question_norm = _norm(question)

    # 1) 公司识别
    stock_code = None
    for alias, code in COMPANY_ALIASES.items():
        if _norm(alias) in question_norm:
            stock_code = code
            break
    # 2) 期间识别
    period_label = None
    for alias, period in PERIOD_ALIASES.items():
        if alias in question_norm:
            period_label = period
            break
    if stock_code is None or period_label is None:
        return {
            "answer": None,
            "refusal": "missing_company_or_period",
            "reason": "未能从问题中识别公司与期间，需指明（如：顺丰 2026Q1 的货币资金）",
        }

    # 3) 行项目检索：问题中去除公司/期间词后的余量做包含匹配
    remainder = question_norm
    for alias in COMPANY_ALIASES:
        remainder = remainder.replace(_norm(alias), "")
    for alias in PERIOD_ALIASES:
        remainder = remainder.replace(alias, "")
    remainder = remainder.replace("的", "").replace("是多少", "").replace("?", "").replace("？", "")
    # 去尾问句助词（strip 语义在此是有意的字符集裁剪）
    for suffix in ("元", "百万元", "千万元", "亿元", "万", "千", "百"):
        if remainder.endswith(suffix):
            remainder = remainder[: -len(suffix)]
            break

    with get_engine().connect() as conn:
        report = conn.execute(
            select(StatementReport).where(
                StatementReport.stock_code == stock_code,
                StatementReport.period_label == period_label,
            )
        ).first()
        if report is None:
            return {
                "answer": None,
                "refusal": "report_not_found",
                "reason": f"事实库中没有 {stock_code} {period_label} 的报告",
            }
        rows = conn.execute(
            select(
                StatementLineItem.item_name,
                StatementLineItem.statement_type,
                StatementLineItem.value_end,
                StatementLineItem.value_begin,
                StatementLineItem.value_current,
                StatementLineItem.value_prior,
                StatementLineItem.page_number,
                StatementLineItem.page_anchor,
            ).where(StatementLineItem.report_id == report.id)
        ).all()

    matches = [
        r
        for r in rows
        if remainder and _norm(remainder) in _norm(r[0])
    ]
    if not matches:
        return {
            "answer": None,
            "refusal": "item_not_found",
            "reason": f"{report.company_name} {period_label} 报表中未检索到「{remainder}」行项目",
        }
    row = matches[0]
    value_by_column = {
        "value_end": row[2],
        "value_begin": row[3],
        "value_current": row[4],
        "value_prior": row[5],
    }
    present = {c: v for c, v in value_by_column.items() if v is not None}
    if not present:
        return {
            "answer": None,
            "refusal": "no_value",
            "reason": f"「{row[0]}」在本期报表中无数值",
        }
    citations = [
        {
            "report_id": str(report.id),
            "source_ref": report.source_ref,
            "statement_type": row[1],
            "item": row[0],
            "column": COLUMN_LABELS.get(column, column),
            "page": row[6],
            "page_anchor": row[7],
        }
        for column in present
    ]
    values_text = "；".join(
        f"{COLUMN_LABELS.get(c, c)} {v}" for c, v in present.items()
    )
    return {
        "answer": values_text,
        "unit": report.unit_note,
        "refusal": None,
        "citations": citations,
    }


def run_eval(eval_path: Path) -> dict:
    cases = json.loads(eval_path.read_text(encoding="utf-8"))["cases"]
    passed = 0
    failures = []
    for case in cases:
        result = retrieve(case["question"])
        ok = False
        if case.get("expect_refusal"):
            ok = result.get("refusal") is not None
        else:
            expected = case.get("expect_value")
            answer = result.get("answer")
            ok = (
                answer is not None
                and expected is not None
                and _norm(expected) in _norm(answer).replace("。", "")
            )
        if ok:
            passed += 1
        else:
            failures.append({"question": case["question"], "result": result})
    return {
        "total": len(cases),
        "passed": passed,
        "hit_rate": round(passed / len(cases), 4) if cases else 0,
        "failures": failures[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--question", help="单问")
    group.add_argument("--eval", type=Path, help="评测集路径")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.eval:
        report = run_eval(args.eval)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(
                f"问数评测：{report['passed']}/{report['total']} 通过"
                f"（命中率 {report['hit_rate']:.1%}）"
            )
        return 0
    result = retrieve(args.question)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
