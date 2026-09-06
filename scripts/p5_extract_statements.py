#!/usr/bin/env python3
"""A 股定期报告三大报表抽取（统一适配接口 cn_ashare_table 的 CLI 入口）。

实现已迁入 flow_api.statements.extraction（B02）；本脚本只负责 IO 与打印，
输出 YAML 格式与历史一致（行项目不含内部页定位字段）。

用法（在 services/api 目录下）：
    uv run python ../../scripts/p5_extract_statements.py <pdf> <out_dir> <sample_id>
"""
import sys
from pathlib import Path

import yaml

from flow_api.statements.extraction import extract_statements


def _strip_page(statements: dict) -> dict:
    return {
        key: [{k: v for k, v in item.items() if k != "page"} for item in items]
        for key, items in statements.items()
    }


def main() -> int:
    pdf_path, out_dir, sample = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    result = extract_statements(pdf_path.read_bytes(), adapter_id="cn_ashare_table")
    statements = _strip_page(result.statements)
    out = {
        "sample": sample,
        "source_pdf": str(pdf_path),
        "unit": result.unit_note,
        "statements": statements,
    }
    out_file = out_dir / f"{sample}_statements.yaml"
    out_file.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    counts = {k: len(v) for k, v in statements.items()}
    print(f"extracted -> {out_file}  rows={counts}  adapter={result.adapter_id}")

    ok = sum(1 for c in result.checks if c.status == "一致")
    print(f"reconciliation: {ok}/{len(result.checks)} 一致")
    for c in result.checks:
        mark = "✓" if c.status == "一致" else "✗"
        print(f"  {mark} {c.label}: {c.left} vs {c.right} [{c.status}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
