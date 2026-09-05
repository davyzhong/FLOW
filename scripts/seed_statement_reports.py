#!/usr/bin/env python3
"""把 P5 抽取的财报 YAML 导入 statement_report（幂等，按唯一身份重建行项目）。

用法示例：
    uv run python scripts/seed_statement_reports.py \
        --yaml docs/implementation/p5/sf_2026q1_statements.yaml \
        --company 顺丰控股 --stock-code 002352.SZ \
        --report-kind 一季报 --period-label 2026Q1
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import yaml

from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport
from flow_api.statements.importer import import_statement_report

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yaml", required=True, help="P5 抽取 YAML 路径")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--stock-code", required=True, help="股票代码")
    parser.add_argument("--report-kind", required=True, help="报告类型（年报/一季报/中报…）")
    parser.add_argument("--period-label", required=True, help="期间标签（如 2026Q1）")
    parser.add_argument(
        "--source-sha256", default=None, help="原文 PDF SHA-256（缺省按 source_ref 计算文件哈希）"
    )
    args = parser.parse_args()

    yaml_path = Path(args.yaml)
    if not yaml_path.is_absolute():
        yaml_path = REPOSITORY_ROOT / yaml_path
    payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    source_ref = str(payload.get("source_pdf") or yaml_path.name)

    source_sha256 = args.source_sha256
    if source_sha256 is None:
        source_file = REPOSITORY_ROOT / source_ref
        if source_file.is_file():
            source_sha256 = hashlib.sha256(source_file.read_bytes()).hexdigest()

    with get_session_factory()() as session:
        report = import_statement_report(
            session,
            company_name=args.company,
            stock_code=args.stock_code,
            report_kind=args.report_kind,
            period_label=args.period_label,
            payload=payload,
            source_ref=source_ref,
            source_sha256=source_sha256,
        )
        session.commit()
        print(
            f"已导入 {report.company_name} {report.period_label} {report.report_kind}"
            f"（id={report.id}，行项目 {len(report.items)} 条，单位 {report.unit_note}）"
        )
        print(f"  source_ref: {report.source_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
