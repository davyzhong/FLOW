#!/usr/bin/env python3
"""P5 反向解析验证：腾讯控股（0700.HK）2026 Q2 业绩公告抽取为 statements YAML。

业绩公告为简明报表（无完整财状/现金流），抽取：
- p5 简明综合收益表（列：2Q2026 / 2Q2025 / 1Q2026，单位人民币百万元）；
- p9 IFRS→Non-IFRS 调节表归母行（作为勾稽锚点，不进 statements）。

勾稽：收入分部加总、毛利链、期内盈利归属、调节链闭合（继承
p5_build_report_view.parse_tencent 的已验证断言，锚点缺失即失败）。

用法：uv run --with pdfplumber --with pyyaml python scripts/p5_extract_tencent.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pdfplumber
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = (
    REPOSITORY_ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/tencent_0700"
)
OUT_PATH = REPOSITORY_ROOT / "docs/implementation/p5/tencent_2026q2_statements.yaml"

PARENUM = r"-?[\d,]+(?:\.\d+)?| \([-\d,]+\)"
NUM = r"-?[\d][\d,]*(?:\.\d+)?"


def parse_signed(s: str):
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        return -_num(s.strip("()"))
    return _num(s)


def _num(s: str):
    s = s.replace(",", "")
    return float(s) if "." in s else int(s)


def main() -> int:
    pdf_file = PDF_PATH / "Tencent_2026_Q2_results.pdf"
    assert pdf_file.is_file(), f"样本缺失: {pdf_file}"
    with pdfplumber.open(str(pdf_file)) as pdf:
        is_lines = (pdf.pages[4].extract_text() or "").split("\n")
        rec_text = pdf.pages[8].extract_text() or ""

    def grab3(label: str):
        for ln in is_lines:
            if ln.strip().split(" ")[0] == label:
                m = re.findall(PARENUM, ln)
                if len(m) >= 3:
                    return [parse_signed(x) for x in m[:3]]
        raise AssertionError(f"腾讯锚点未取到: {label}")

    labels = [
        "收入", "增值服务", "营销服务", "金融科技及企业服务", "其他", "收入成本", "毛利",
        "销售及市场推广开支", "一般及行政开支", "其他收益/（亏损）净额", "经营盈利",
        "投资收益/（亏损）净额及其他", "利息收入", "财务成本",
        "分占联营公司及合营公司盈利/（亏损）净额", "除税前盈利", "所得税开支", "期内盈利",
        "本公司权益持有人", "非控制性权益",
    ]
    stmt = {lb: grab3(lb) for lb in labels}

    # 勾稽断言（继承已验证逻辑）
    assert sum(stmt[s][0] for s in ["增值服务", "营销服务", "金融科技及企业服务", "其他"]) == stmt["收入"][0], "收入分部加总不闭合"
    assert stmt["收入"][0] + stmt["收入成本"][0] == stmt["毛利"][0], "毛利链不闭合"
    assert stmt["本公司权益持有人"][0] + stmt["非控制性权益"][0] == stmt["期内盈利"][0], "期内盈利归属不闭合"
    rec_line = next(
        (ln.strip() for ln in rec_text.split("\n") if ln.strip().startswith("本公司权益持有人应占盈利")),
        None,
    )
    assert rec_line, "调节表归母行未取到"
    vals = [parse_signed(x) for x in re.findall(PARENUM, rec_line)]
    assert len(vals) == 9, f"调节表列数异常: {len(vals)}"
    reported, adjs, non_ifrs = vals[0], vals[1:8], vals[8]
    assert reported + sum(adjs) == non_ifrs, "IFRS→Non-IFRS 调节链不闭合"
    assert reported == stmt["本公司权益持有人"][0], "调节表与收益表归母不一致"

    items = [
        {
            "item": label,
            "本期发生额": vals3[0],   # 2Q2026
            "上期发生额": vals3[1],   # 2Q2025
        }
        for label, vals3 in stmt.items()
    ]
    out = {
        "sample": "tencent_2026q2",
        "source_pdf": str(pdf_file.relative_to(REPOSITORY_ROOT)),
        "unit": "人民币百万元",
        "statements": {"合并利润表": items},
    }
    OUT_PATH.write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(f"extracted -> {OUT_PATH.name} rows={len(items)} 单位=人民币百万元")
    print("勾稽: 收入分部加总 ✓ 毛利链 ✓ 期内盈利归属 ✓ IFRS→Non-IFRS 调节链 ✓")
    print(f"  2Q2026 收入 {stmt['收入'][0]:,} 百万 / 归母 {reported:,} / Non-IFRS 归母 {non_ifrs:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
