#!/usr/bin/env python3
"""为库内全部财报生成客观分析 PDF（格式评审交付物）。

流程：alembic 升级 → 种子 P5 报告（幂等）→ 逐份 归一化 → 客观分析 →
HTML 渲染 → 固定 Chromium 打印 PDF。

用法（仓库根）：
    uv run python scripts/generate_objective_report_pdfs.py \
        [--out-dir work/objective_reports_pdf] [--company 数据熊]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "services" / "api" / "src"))

os_environ_defaults = {
    "DATABASE_URL": "postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow",
    "REDIS_URL": "redis://127.0.0.1:6379/0",
    "S3_ENDPOINT_URL": "http://127.0.0.1:9000",
    "S3_BUCKET": "flow",
    "S3_ACCESS_KEY": "flow",
    "S3_SECRET_KEY": "flow_dev_only",
}

P5_REPORTS = [
    {
        "yaml": "docs/implementation/p5/sf_2026q1_statements.yaml",
        "company": "顺丰控股",
        "stock_code": "002352.SZ",
        "report_kind": "一季报",
        "period_label": "2026Q1",
    },
    {
        "yaml": "docs/implementation/p5/tencent_2026q2_statements.yaml",
        "company": "腾讯控股",
        "stock_code": "0700.HK",
        "report_kind": "业绩公告",
        "period_label": "2026Q2",
    },
    {
        "yaml": "docs/implementation/p5/jdl_2025fy_statements.yaml",
        "company": "京东物流",
        "stock_code": "2618.HK",
        "report_kind": "年报",
        "period_label": "FY2025",
    },
]

CST = timezone(timedelta(hours=8))


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(str(REPOSITORY_ROOT / "services/api/alembic.ini")), "head")


def seed_reports() -> None:
    """进程内幂等导入 P5 抽取报告（等价于 seed_statement_reports.py）。"""
    import hashlib

    import yaml as yaml_lib

    from flow_api.infrastructure.db import get_session_factory
    from flow_api.statements.importer import import_statement_report

    factory = get_session_factory()
    for spec in P5_REPORTS:
            yaml_path = REPOSITORY_ROOT / spec["yaml"]
            payload = yaml_lib.safe_load(yaml_path.read_text(encoding="utf-8"))
            source_ref = str(payload.get("source_pdf") or yaml_path.name)
            source_file = REPOSITORY_ROOT / source_ref
            source_sha256 = (
                hashlib.sha256(source_file.read_bytes()).hexdigest()
                if source_file.is_file()
                else None
            )
            with factory() as write_session:
                report = import_statement_report(
                    write_session,
                    company_name=spec["company"],
                    stock_code=spec["stock_code"],
                    report_kind=spec["report_kind"],
                    period_label=spec["period_label"],
                    payload=payload,
                    source_ref=source_ref,
                    source_sha256=source_sha256,
                )
                write_session.commit()
                print(
                    f"  seed: {report.company_name} {report.period_label}"
                    f"（id={report.id}，行项目 {len(report.items)}）"
                )
    print("  种子导入完成。")


def generate(out_dir: Path, company_filter: str | None) -> list[Path]:
    from flow_api.analysis.objective import ObjectiveAnalysisService
    from flow_api.infrastructure.db import get_engine, get_session_factory
    from flow_api.infrastructure.models.statement import (
        StatementNormalizedItem,
        StatementReport,
    )
    from flow_api.statements.normalization import load_alias_map, normalize_report
    from flow_api.statements.objective_report_html import render_objective_report_v2
    from flow_api.statements.objective_report_pdf import print_pdf
    from sqlalchemy import delete, func, select
    from sqlalchemy.orm import Session

    run_migrations()

    generated: list[Path] = []
    failures: list[tuple[str, str]] = []
    engine = get_engine()
    with Session(engine, expire_on_commit=False) as session:
        reports = session.scalars(select(StatementReport)).all()
        for report in reports:
            if company_filter and company_filter not in report.company_name:
                continue
            # normalize 对 draft 报告非幂等：先删同版本归一条目再重建（幂等化）；
            # 含同期对比列的年报会触发 uq_statement_normalized_item 冲突（P01 待修），
            # 单份失败不阻断批次。
            alias_version = str(load_alias_map().get("version", "v0"))
            session.execute(
                delete(StatementNormalizedItem).where(
                    StatementNormalizedItem.report_id == report.id,
                    StatementNormalizedItem.mapping_version == alias_version,
                )
            )
            try:
                normalize_report(session, report)
                session.flush()
            except Exception as error:  # noqa: BLE001 — 单份失败不阻断批次
                session.rollback()
                failures.append((report.company_name, str(error)[:160]))
                print(f"  [跳过] {report.company_name} {report.period_label}：归一化失败")
                continue
            normalized_items = session.scalars(
                select(StatementNormalizedItem).where(
                    StatementNormalizedItem.report_id == report.id,
                    StatementNormalizedItem.mapping_version == alias_version,
                )
            ).all()
            result = ObjectiveAnalysisService(session).analyze(report.id)
            generated_at = datetime.now(CST)
            html = render_objective_report_v2(
                report, result, normalized_items, generated_at=generated_at
            )
            filename = "%s_%s_%s.pdf" % (
                (report.period_label or "").replace("/", "-"),
                (report.company_name or "company").replace("/", "-"),
                generated_at.strftime("%Y%m%d%H%M%S"),
            )
            out_path = out_dir / filename
            print_pdf(html, out_path=out_path)
            computed = sum(
                1 for entry in result.entries if entry.status.value == "computed"
            )
            print(
                f"  [PDF] {out_path.name}（条目 {len(result.entries)}，"
                f"可算 {computed}，大小 {out_path.stat().st_size // 1024} KB）"
            )
            generated.append(out_path)
    for company, message in failures:
        print(f"  [失败] {company}：{message}")
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPOSITORY_ROOT / "work" / "objective_reports_pdf")
    parser.add_argument("--company", default=None, help="仅生成公司名包含该子串的报告")
    parser.add_argument("--skip-seed", action="store_true", help="跳过种子导入（报告已在库）")
    args = parser.parse_args()

    import os

    for key, value in os_environ_defaults.items():
        os.environ.setdefault(key, value)

    run_migrations()

    out_dir: Path = args.out_dir if args.out_dir.is_absolute() else REPOSITORY_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_seed:
        print("== 种子财报导入 ==")
        seed_reports()

    print("== 生成客观分析 PDF ==")
    generated = generate(out_dir, args.company)
    print(f"完成：{len(generated)} 份 PDF → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
