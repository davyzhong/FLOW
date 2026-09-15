#!/usr/bin/env python3
"""T10-B4：重述差异报告——同身份报表相邻版本逐行逐列比对。

重述合同：导入器在内容 hash 变化时新建更高 version 并写 supersedes_id 指向
被取代版本；本脚本对 (stock_code, period_label[, report_kind]) 的最新两版
做行级 diff（item+列 值比对），输出 supersedes 链与新增/删除/变更清单。

用法：
  python3 scripts/statement_restatement_diff.py --stock-code 002352.SZ \\
      --period-label 2026Q1 [--report-kind 一季报] [--json]
退出码：0 = 可比且已输出；2 = 无可比版本。
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services/api" / "src"))

COLUMNS = ("value_end", "value_begin", "value_current", "value_prior")


def load_versions(stock_code: str, period_label: str, report_kind: str | None):
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import (
        StatementLineItem,
        StatementReport,
    )

    conditions = [
        StatementReport.stock_code == stock_code,
        StatementReport.period_label == period_label,
    ]
    if report_kind:
        conditions.append(StatementReport.report_kind == report_kind)
    with get_engine().connect() as conn:
        reports = conn.execute(
            select(StatementReport).where(*conditions).order_by(StatementReport.version)
        ).all()
        if len(reports) < 2:
            return None
        # 裸 Connection 的 entity select 不产生 ORM 对象：显式列查询
        items = conn.execute(
            select(
                StatementLineItem.report_id,
                StatementLineItem.statement_type,
                StatementLineItem.item_name,
                StatementLineItem.sort_order,
                *[
                    getattr(StatementLineItem, column)
                    for column in COLUMNS
                ],
            ).where(StatementLineItem.report_id.in_([r.id for r in reports[-2:]]))
        ).all()
    old_report, new_report = reports[-2], reports[-1]
    rows_by_report: dict[object, dict[tuple[str, str, int], dict[str, Decimal | None]]] = {
        old_report.id: {},
        new_report.id: {},
    }
    for item in items:
        rows_by_report[item.report_id][(item.statement_type, item.item_name, item.sort_order)] = {
            column: getattr(item, column) for column in COLUMNS
        }
    return old_report, new_report, rows_by_report


def flatten(
    rows: dict[tuple[str, str, int], dict[str, Decimal | None]],
) -> dict[tuple[str, str, str, str], Decimal | None]:
    flat: dict[tuple[str, str, str, str], Decimal | None] = {}
    for (statement_type, item_name, sort_order), row_values in rows.items():
        for column in COLUMNS:
            flat[(statement_type, item_name, sort_order, column)] = row_values[column]
    return flat


def compute_diff(stock_code: str, period_label: str, report_kind: str | None = None) -> dict | None:
    """相邻版本差异计算（供 CLI 与测试共用）。无可比版本返回 None。"""
    loaded = load_versions(stock_code, period_label, report_kind)
    if loaded is None:
        return None
    old_report, new_report, values = loaded

    old_flat = flatten(values[old_report.id])
    new_flat = flatten(values[new_report.id])

    changed = []
    removed = []
    added = []
    for key in sorted(set(old_flat) | set(new_flat)):
        old_value = old_flat.get(key)
        new_value = new_flat.get(key)
        if key not in new_flat:
            removed.append(
                {"key": list(key), "old": str(old_value) if old_value is not None else None}
            )
        elif key not in old_flat:
            added.append(
                {"key": list(key), "new": str(new_value) if new_value is not None else None}
            )
        elif old_value != new_value:
            changed.append(
                {
                    "key": list(key),
                    "old": str(old_value) if old_value is not None else None,
                    "new": str(new_value) if new_value is not None else None,
                    "delta": (
                        str(new_value - old_value)
                        if old_value is not None and new_value is not None
                        else None
                    ),
                }
            )

    report = {
        "level": "restatement-diff",
        "supersedes_chain": {
            "superseded_version": old_report.version,
            "superseded_id": str(old_report.id),
            "current_version": new_report.version,
            "current_id": str(new_report.id),
            "supersedes_id_consistent": new_report.supersedes_id == old_report.id,
        },
        "changed_count": len(changed),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed": changed[:50],
        "added": added[:50],
        "removed": removed[:50],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-code", required=True)
    parser.add_argument("--period-label", required=True)
    parser.add_argument("--report-kind", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = compute_diff(args.stock_code, args.period_label, args.report_kind)
    if report is None:
        print("找不到同身份的两个版本（无重述可比）", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        chain = report["supersedes_chain"]
        print(
            f"重述链：v{chain['superseded_version']}({chain['superseded_id'][:8]}…)"
            f" → v{chain['current_version']}({chain['current_id'][:8]}…)"
            f" supersedes_id 一致={chain['supersedes_id_consistent']}"
        )
        print(
            f"变更 {report['changed_count']}，新增 {report['added_count']}，"
            f"删除 {report['removed_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
