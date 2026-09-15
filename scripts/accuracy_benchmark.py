#!/usr/bin/env python3
"""T09 数字级准确率基准（C 级出口 B2）L0 层：入库保真基准。

两级基准合同（docs/50_plans/work_items/PUBLIC--c-level-exit-protocol.md）：
- L0（本脚本，当前可执行）：事实库 statement_line_item 与「已验证抽取 YAML」
  （docs/implementation/p5/*.yaml，P5 期完成来源核验）逐行逐值比对——
  证明入库/归一化管线不丢数、不改数、不换符号；
- L1（C 级出口执行期填 answer_set 的 source_truth 列）：与 PDF 页级 ground
  truth 比对，度量抽取本身。L1 未到料前不得宣称准确率。

用法：
  python3 scripts/accuracy_benchmark.py --level L0            # 全量比对
  python3 scripts/accuracy_benchmark.py --level L0 --json     # 机器可读
退出码：0 = 全对；1 = 存在差异；2 = 配置/环境错误。
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO / "services/api" / "src"))

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_ENV_ERROR = 2


def load_yaml(path: Path):
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


# 与 statements/importer.py COLUMN_ALIASES 同源的列名规范化（基准侧独立复制，
# 避免被测管线自带答案；两表漂移时本脚本 Step 层会暴露差异）
COLUMN_ALIASES = {
    "期末余额": "value_end",
    "期初余额": "value_begin",
    "本期发生额": "value_current",
    "上期发生额": "value_prior",
    "本期金额": "value_current",
    "上期金额": "value_prior",
}


def collect_expected() -> dict:
    """期望值：(source_pdf, statement, item, column) -> Decimal|null。

    以 source_pdf（抽取 YAML 顶部字段）为报告身份——事实库 source_ref 登记
    同一路径（seed 时传入），不受 sample 代号与 stock_code/period_label 命名
    差异影响。
    """
    expected: dict[tuple[str, str, str, str], Decimal | None] = {}
    sources = sorted(glob.glob(str(REPO / "docs/implementation/p5" / "*_statements.yaml")))
    if not sources:
        raise RuntimeError("未找到抽取 YAML（docs/implementation/p5/*_statements.yaml）")
    for source in sources:
        payload = load_yaml(Path(source))
        source_pdf = payload["source_pdf"]
        for statement, rows in payload["statements"].items():
            for row in rows:
                item = row["item"]
                for column, value in row.items():
                    if column == "item":
                        continue
                    normalized = COLUMN_ALIASES.get(column, column)
                    key = (source_pdf, statement, item, normalized)
                    if value is None:
                        expected.setdefault(key, None)
                    else:
                        expected[key] = Decimal(str(value))
    return expected


def collect_actual() -> dict:
    """实际值：事实库 statement_line_item 按 (sample, statement, item, column)。"""
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport

    actual: dict[tuple[str, str, str, str], Decimal | None] = {}
    with get_engine().connect() as conn:
        reports = conn.execute(
            select(StatementReport.id, StatementReport.source_ref)
        ).all()
        id_source = {r[0]: r[1] for r in reports}
        rows = conn.execute(
            select(
                StatementLineItem.report_id,
                StatementLineItem.statement_type,
                StatementLineItem.item_name,
                StatementLineItem.value_end,
                StatementLineItem.value_begin,
                StatementLineItem.value_current,
                StatementLineItem.value_prior,
            ).order_by(StatementLineItem.report_id, StatementLineItem.sort_order)
        ).all()
    column_keys = ("value_end", "value_begin", "value_current", "value_prior")
    for report_id, statement_type, item_name, *values in rows:
        source_ref = id_source.get(report_id)
        if source_ref is None:
            continue
        for column, value in zip(column_keys, values, strict=True):
            key = (source_ref, statement_type, item_name, column)
            if value is None:
                actual.setdefault(key, None)
            else:
                actual[key] = Decimal(str(value))
    return actual


def _display_column(report_kind: str, column: str, sort_order: int) -> str:
    # 直接以 DB 数值列族对齐（value_end/value_begin/value_current/value_prior）；
    # report_kind 不改变列族。
    return column


def compare(expected: dict, actual: dict) -> dict:
    mismatches = []
    only_expected = []
    only_actual = []
    value_checked = 0
    for key, want in expected.items():
        got = actual.get(key)
        if got is None and key not in actual:
            # 期望有、实际完全缺失
            only_expected.append(
                {"key": list(key), "expected": str(want) if want is not None else None}
            )
            continue
        if got != want:
            mismatches.append(
                {
                    "key": list(key),
                    "expected": str(want) if want is not None else None,
                    "actual": str(got) if got is not None else None,
                }
            )
            continue
        value_checked += 1
    for key, value in actual.items():
        if key not in expected and value is not None:
            # 实际侧存在、期望侧无列且值非空 = 真实多出数据；
            # DB 四列族的结构性 NULL 不算多出。
            only_actual.append({"key": list(key), "actual": str(value)})
    total = value_checked + len(mismatches) + len(only_expected)
    return {
        "level": "L0",
        "total_compared": total,
        "value_checked": value_checked,
        "mismatch_count": len(mismatches),
        "missing_count": len(only_expected),
        "extra_count": len(only_actual),
        "mismatches": mismatches[:50],
        "missing": only_expected[:50],
        "extra": only_actual[:50],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", choices=("L0",), default="L0")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.level != "L0":
        print("L1 需要 PDF 页级 ground truth（C 级出口执行期提供）", file=sys.stderr)
        return EXIT_ENV_ERROR
    try:
        expected = collect_expected()
        actual = collect_actual()
    except Exception as error:  # noqa: BLE001
        print(f"env error: {error}", file=sys.stderr)
        return EXIT_ENV_ERROR
    report = compare(expected, actual)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"L0 入库保真基准：比对 {report['total_compared']} 值，"
            f"一致 {report['value_checked']}，"
            f"不一致 {report['mismatch_count']}，"
            f"缺失 {report['missing_count']}，"
            f"多出 {report['extra_count']}"
        )
    clean = report["mismatch_count"] == 0 and report["missing_count"] == 0
    return EXIT_OK if clean else EXIT_MISMATCH


if __name__ == "__main__":
    raise SystemExit(main())
