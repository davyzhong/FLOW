#!/usr/bin/env python3
"""京东物流（2618.HK）FY2025 年报三大报表抽取（hk_traditional_text 的 CLI 入口）。

实现已迁入 flow_api.statements.extraction（B02）；输出与历史一致。

用法（在 services/api 目录下）：uv run python ../../scripts/p5_extract_jdl.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from flow_api.statements.extraction import extract_statements

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = (
    REPOSITORY_ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/jd_logistics_2618/"
    / "JDL_FY2025_annual_report.pdf"
)
OUT_PATH = REPOSITORY_ROOT / "docs/implementation/p5/jdl_2025fy_statements.yaml"


def _strip_page(statements: dict) -> dict:
    return {
        key: [{k: v for k, v in item.items() if k != "page"} for item in items]
        for key, items in statements.items()
    }


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = extract_statements(PDF_PATH.read_bytes(), adapter_id="hk_traditional_text")
    statements = _strip_page(result.statements)
    out = {
        "sample": "jdl_2025fy",
        "source_pdf": str(PDF_PATH.relative_to(REPOSITORY_ROOT)),
        "unit": result.unit_note,
        "statements": statements,
    }
    OUT_PATH.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    counts = {k: len(v) for k, v in statements.items()}
    print(f"extracted -> {OUT_PATH.name}  rows={counts}  adapter={result.adapter_id}")

    ok = sum(1 for c in result.checks if c.status == "一致")
    print(f"reconciliation: {ok}/{len(result.checks)} 一致")
    for c in result.checks:
        mark = "✓" if c.status == "一致" else "✗"
        print(f"  {mark} {c.label}: {c.left} vs {c.right} [{c.status}]")
    return 0 if ok == len(result.checks) else 1


if __name__ == "__main__":
    sys.exit(main())
