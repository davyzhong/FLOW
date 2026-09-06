#!/usr/bin/env python3
"""腾讯控股（0700.HK）业绩公告抽取（hk_results_announcement 的 CLI 入口）。

实现已迁入 flow_api.statements.extraction（B02）；输出与历史一致。

用法（在 services/api 目录下）：uv run python ../../scripts/p5_extract_tencent.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from flow_api.statements.extraction import extract_statements

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = (
    REPOSITORY_ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/tencent_0700"
    / "Tencent_2026_Q2_results.pdf"
)
OUT_PATH = REPOSITORY_ROOT / "docs/implementation/p5/tencent_2026q2_statements.yaml"


def main() -> int:
    result = extract_statements(PDF_PATH.read_bytes(), adapter_id="hk_results_announcement")
    items = [{k: v for k, v in item.items() if k != "page"} for item in result.statements["合并利润表"]]
    out = {
        "sample": "tencent_2026q2",
        "source_pdf": str(PDF_PATH.relative_to(REPOSITORY_ROOT)),
        "unit": result.unit_note,
        "statements": {"合并利润表": items},
    }
    OUT_PATH.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"extracted -> {OUT_PATH.name} rows={len(items)} 单位={result.unit_note}")
    for c in result.checks:
        mark = "✓" if c.status == "一致" else "✗"
        print(f"  {mark} {c.label}: {c.left} vs {c.right} [{c.status}]")
    ok = all(c.status == "一致" for c in result.checks)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
