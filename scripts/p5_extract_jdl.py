#!/usr/bin/env python3
"""P5 反向解析验证：京东物流（2618.HK）FY2025 年报三大报表抽取。

港股 IFRS 披露（繁体、功能法列报、附注号中缀），与 A 股格式不同：
- 报表页固定为年报 p106（损益）/ p108–109（财状）/ p112–113（现金流），
  以页首标题行验证，不盲信页码；
- 行解析：`项目名 [附注号] 本期 上期`，括号为负数、— 为空；
- 输出键名统一为简体标准名（合并资产负债表/合并利润表/合并现金流量表），
  item 保留披露原文（繁体），单位人民币千元；
- 勾稽为 IFRS 等式（见 reconcile_jdl）。

用法：uv run --with pdfplumber python scripts/p5_extract_jdl.py
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
    / "docs/knowledge-base/02_research/original/p5_samples/jd_logistics_2618/"
    / "JDL_FY2025_annual_report.pdf"
)
OUT_PATH = (
    REPOSITORY_ROOT / "docs/implementation/p5/jdl_2025fy_statements.yaml"
)

# 页码（1-based）与标题锚
PAGES = {
    "合并利润表": (106, "合併損益表"),
    "合并资产负债表": (108, "合併財務狀況表"),
    "合并现金流量表": (112, "合併現金流量表"),
}

NUM = r"\(?-?[\d][\d,]*\)?"


def parse_line(line: str):
    """返回 (item_name, 本期, 上期)；非数据行返回 None。"""

    tokens = line.split()
    nums: list[str | None] = []
    while tokens:
        tok = tokens[-1]
        if re.fullmatch(NUM, tok):
            nums.insert(0, tok)
            tokens.pop()
        elif tok == "—" or tok == "-":
            nums.insert(0, None)
            tokens.pop()
        else:
            break
    if not nums or not tokens:
        return None  # 无金额或纯数字行（合计重复行）
    # 附注号识别：剥完金额后，若最前金额是无逗号的 1–3 位数字且仍有项目名，
    # 且金额数超过 2 个，则它是附注号而非金额。
    if (
        len(nums) > 2
        and nums[0] is not None
        and re.fullmatch(r"\d{1,3}", nums[0])
        and "," not in nums[0]
    ):
        nums = nums[1:]
    if len(nums) > 2:
        nums = nums[-2:]
    name = "".join(tokens)
    if not name or re.fullmatch(r"[\d.,()]+", name):
        return None

    def val(tok: str | None):
        if tok is None:
            return None
        negative = tok.startswith("(")
        digits = tok.strip("()").replace(",", "")
        number = float(digits) if "." in digits else int(digits)
        return -number if negative else number

    current = val(nums[-2]) if len(nums) >= 2 else val(nums[-1])
    prior = val(nums[-1]) if len(nums) >= 2 else None
    if current is None and prior is None:
        return None
    return name, current, prior


def extract_statement(pdf, start_page: int, anchor: str, end_page: int | None = None):
    items: list[dict] = []
    stop = end_page or start_page + 4
    active = False
    for pno in range(start_page - 1, stop):
        text = pdf.pages[pno].extract_text() or ""
        lines = text.split("\n")
        if not active:
            if any(anchor in ln for ln in lines[:4]):
                active = True
            else:
                continue
        for line in lines:
            if "年度報告" in line or "人民幣元" in line:
                continue
            parsed = parse_line(line)
            if parsed:
                name, current, prior = parsed
                items.append(
                    {"item": name, "本期发生额": current, "上期发生额": prior}
                )
    return items


def to_balance_columns(items: list[dict]) -> list[dict]:
    """资产负债表披露列语义为年末/年初，映射到统一的期末/期初。"""

    return [
        {"item": it["item"], "期末余额": it["本期发生额"], "期初余额": it["上期发生额"]}
        for it in items
    ]


def find(items, name):
    for it in items:
        if it["item"] == name:
            return it
    return None


def check(diffs, label, left, right):
    if left is None or right is None:
        diffs.append((label, left, right, "披露缺失/未取到"))
    elif left != right:
        diffs.append((label, left, right, "不一致"))
    else:
        diffs.append((label, left, right, "一致"))


def reconcile_jdl(st):
    diffs: list[tuple] = []
    is_ = st["合并利润表"]
    bs = st["合并资产负债表"]
    cf = st["合并现金流量表"]
    for col in ("本期发生额", "上期发生额"):
        g = lambda n: (find(is_, n) or {}).get(col)
        check(diffs, f"毛利=收入-營業成本 [{col}]", g("毛利"),
              (g("收入") or 0) + (g("營業成本") or 0))
        check(diffs, f"除稅前利潤逐項加總 [{col}]", g("除稅前利潤"),
              (g("毛利") or 0) + (g("銷售及市場推廣開支") or 0) + (g("研發開支") or 0)
              + (g("一般及行政開支") or 0) + (g("其他收入、收益╱（虧損）淨額") or 0)
              + (g("出售產業園的收益") or 0) + (g("財務收入") or 0) + (g("財務成本") or 0)
              + (g("金融資產減值損失（包括減值損失轉回）") or 0)
              + (g("應佔聯營企業及合營企業損益") or 0))
        check(diffs, f"年度利潤=除稅前+所得稅 [{col}]", g("年度利潤"),
              (g("除稅前利潤") or 0) + (g("所得稅開支") or 0))
        check(diffs, f"年度利潤=本公司所有者+非控制性權益 [{col}]", g("年度利潤"),
              (g("本公司所有者") or 0) + (g("非控制性權益") or 0))
    for col in ("期末余额", "期初余额"):
        g = lambda n: (find(bs, n) or {}).get(col)
        check(diffs, f"資產總額=非流動+流動 [{col}]", g("資產總額"),
              (g("非流動資產總額") or 0) + (g("流動資產總額") or 0))
        check(diffs, f"負債總額=非流動+流動 [{col}]", g("負債總額"),
              (g("非流動負債總額") or 0) + (g("流動負債總額") or 0))
        check(diffs, f"權益總額=歸母+非控制性 [{col}]", g("權益總額"),
              (g("歸屬於本公司所有者的權益") or 0) + (g("非控制性權益") or 0))
        check(diffs, f"權益及負債總額=權益+負債=資產 [{col}]", g("權益及負債總額"),
              (g("權益總額") or 0) + (g("負債總額") or 0))
        check(diffs, f"資產總額=權益及負債總額 [{col}]", g("資產總額"),
              g("權益及負債總額"))
    for col in ("本期发生额", "上期发生额"):
        g = lambda n: (find(cf, n) or {}).get(col)
        check(diffs, f"現金淨變動=經營+投資+融資 [{col}]",
              g("現金及現金等價物（減少）╱增加淨額"),
              (g("經營活動所得現金淨額") or 0) + (g("投資活動所用現金淨額") or 0)
              + (g("融資活動所用現金淨額") or 0))
        check(diffs, f"年末現金=年初+淨變動+外匯 [{col}]", g("年末現金及現金等價物"),
              (g("年初現金及現金等價物") or 0)
              + (g("現金及現金等價物（減少）╱增加淨額") or 0)
              + (g("外匯匯率變動對現金及現金等價物的影響") or 0))
        check(diffs, f"財狀表現金=現金流量表年末 [{col}]",
              (find(bs, "現金及現金等價物") or {}).get("期末余额" if col == "本期发生额" else "期初余额"),
              g("年末現金及現金等價物"))
    return diffs


def main() -> int:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pdfplumber.open(str(PDF_PATH)) as pdf:
        # end_page 为最后扫描 PDF 页 + 1（range 右开）：损益表 106–107（含综合收益延续）；
        # 财状表 108–109；现金流 112–113。
        statements = {
            "合并利润表": extract_statement(
                pdf, *PAGES["合并利润表"], end_page=107
            ),
            "合并资产负债表": to_balance_columns(
                extract_statement(pdf, *PAGES["合并资产负债表"], end_page=110)
            ),
            "合并现金流量表": extract_statement(
                pdf, *PAGES["合并现金流量表"], end_page=114
            ),
        }
    out = {
        "sample": "jdl_2025fy",
        "source_pdf": str(PDF_PATH.relative_to(REPOSITORY_ROOT)),
        "unit": "人民币千元（每股收益为元）",
        "statements": statements,
    }
    OUT_PATH.write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    counts = {k: len(v) for k, v in statements.items()}
    print(f"extracted -> {OUT_PATH.name}  rows={counts}")

    diffs = reconcile_jdl(statements)
    ok = sum(1 for d in diffs if d[3] == "一致")
    print(f"reconciliation: {ok}/{len(diffs)} 一致")
    for label, left, right, status in diffs:
        mark = "✓" if status == "一致" else "✗"
        print(f"  {mark} {label}: {left} vs {right} [{status}]")
    return 0 if ok == len(diffs) else 1


if __name__ == "__main__":
    sys.exit(main())
