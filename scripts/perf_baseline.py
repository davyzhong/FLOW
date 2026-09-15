#!/usr/bin/env python3
"""T11-G2：10× 数据量性能容量基线（事务内合成放大，测完回滚不留数据）。

方法：
- 以现有 statement_report/statement_line_item 行数为基线 N；
- 在单个事务内合成放大至 ≥10×（复制行项目、改 item_name 后缀避免唯一冲突
  ——报告行无唯一约束，但同 (report, statement, sort) 语义按 order 区分）；
- 计时三类代表性查询（与产品读路径同形）：
  1. fact_lookup：按 report 过滤行项目（报告明细页路径）；
  2. item_scan：item_name contains 检索（溯源/问数检索路径）；
  3. aggregate：sum/group（覆盖矩阵生成路径）；
- 输出 baseline JSON（每查询 P50/P95 + 行数），并落 docs/60_delivery 报告由
  调用方提交；测完 ROLLBACK，不污染事实库。

用法：python3 scripts/perf_baseline.py --scale 10 [--json]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services/api" / "src"))


def timed(conn, query_sql: str, params: dict, repeat: int = 20) -> dict:
    samples = []
    for _ in range(repeat):
        started = time.monotonic()
        conn.execute(query_sql, params).all()
        samples.append((time.monotonic() - started) * 1000)
    samples.sort()
    return {
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(samples[max(0, int(len(samples) * 0.95) - 1)], 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    from sqlalchemy import text

    from flow_api.infrastructure.db import get_engine

    engine = get_engine()
    with engine.connect() as conn:
        base_items = conn.execute(text("SELECT count(*) FROM statement_line_item")).scalar()
        target_items = base_items * args.scale

        # 事务内合成放大（不 commit，结束即回滚）
        conn.execute(
            text(
                "INSERT INTO statement_line_item (id, report_id, statement_type, item_name,"
                " sort_order, value_end, value_begin, value_current, value_prior)"
                " SELECT gen_random_uuid(), report_id, statement_type,"
                " item_name || '_synth_' || g, sort_order + g * 100000, value_end,"
                " value_begin, value_current, value_prior"
                " FROM statement_line_item,"
                " generate_series(1, :groups) AS g"
                " WHERE :target_items > (SELECT count(*) FROM statement_line_item)"
            ),
            {"groups": max(1, args.scale - 1), "target_items": target_items},
        )
        scaled_items = conn.execute(text("SELECT count(*) FROM statement_line_item")).scalar()

        results = {
            "fact_lookup": timed(
                conn,
                text(
                    "SELECT * FROM statement_line_item WHERE report_id ="
                    " (SELECT id FROM statement_report ORDER BY id LIMIT 1)"
                ),
                {},
            ),
            "item_scan": timed(
                conn,
                text(
                    "SELECT * FROM statement_line_item"
                    " WHERE item_name LIKE :pattern"
                ),
                {"pattern": "%货币%"},
            ),
            "aggregate": timed(
                conn,
                text(
                    "SELECT statement_type, count(*), sum(value_current) FROM"
                    " statement_line_item GROUP BY statement_type"
                ),
                {},
            ),
        }

    report = {
        "level": "performance-baseline",
        "scale_target": args.scale,
        "base_items": base_items,
        "scaled_items": scaled_items,
        "scale_achieved": round(scaled_items / base_items, 1) if base_items else None,
        "queries": results,
        "note": "事务内合成放大，未提交；数值列为真实值副本，B-tree 语义与生产一致",
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"10× 基线：行项目 {base_items} → {scaled_items}"
            f"（{report['scale_achieved']}×）；"
            f"明细查询 P95 {results['fact_lookup']['p95_ms']}ms、"
            f"检索 P95 {results['item_scan']['p95_ms']}ms、"
            f"聚合 P95 {results['aggregate']['p95_ms']}ms"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
