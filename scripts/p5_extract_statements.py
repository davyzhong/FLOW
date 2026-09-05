#!/usr/bin/env python3
"""P5 反向解析验证：从上市公司定期报告 PDF 抽取三大报表为结构化行项目。

首个样本：顺丰控股 2026 年第一季度报告（17 页，巨潮披露，合并口径）。
报表页码通过「表头特征行」自动定位，不硬编码页码，以便复用于其它 A 股季报。

输出：
- <out_dir>/<sample>_statements.yaml  结构化行项目（项目名、期末/本期、期初/上期，单位：人民币千元）
- 控制台打印勾稽校验结果（供证据报告引用）

用法：python3 scripts/p5_extract_statements.py <pdf> <out_dir> <sample_id>
"""
import sys
import re
from pathlib import Path

import pdfplumber
import yaml

HEADER_KEYS = ("项目", "期末余额", "期初余额", "本期发生额", "上期发生额")


def norm_item(name: str) -> str:
    """去掉 PDF 换行造成的断行，统一项目名。"""
    return re.sub(r"\s+", "", name or "")


def parse_num(cell: str):
    """把 '74,142,121' / '-' / '' / None 解析为 int 或 None。"""
    if cell is None:
        return None
    s = cell.strip().replace(",", "")
    if s in ("", "-", "—"):
        return None
    m = re.fullmatch(r"-?\d+(\.\d+)?", s)
    if not m:
        return None
    return float(s) if "." in s else int(s)


def extract(pdf_path: Path):
    statements = []  # list of {"header": [...], "rows": [...]}
    current = None
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table:
                    continue
                header = [norm_item(c) for c in table[0]]
                is_header = any(k in header for k in ("期末余额", "本期发生额")) and "项目" in header[0]
                if is_header:
                    if current:
                        statements.append(current)
                    current = {"header": header, "rows": []}
                    body = table[1:]
                elif current is not None and len(table[0]) == len(current["header"]):
                    body = table  # 续页无表头
                else:
                    continue
                for row in body:
                    if row and row[0] and norm_item(row[0]):
                        current["rows"].append(row)
    if current:
        statements.append(current)
    return statements


def to_dict(statements):
    out = {}
    for st in statements:
        header = st["header"]
        if "期末余额" in header:
            key, cols = "合并资产负债表", ("期末余额", "期初余额")
        elif "本期发生额" in header and "一、营业总收入" in [norm_item(r[0]) for r in st["rows"][:3]]:
            key, cols = "合并利润表", ("本期发生额", "上期发生额")
        else:
            key, cols = "合并现金流量表", ("本期发生额", "上期发生额")
        items = []
        for row in st["rows"]:
            items.append({
                "item": norm_item(row[0]),
                cols[0]: parse_num(row[1] if len(row) > 1 else None),
                cols[1]: parse_num(row[2] if len(row) > 2 else None),
            })
        out[key] = items
    return out


def find(items, name):
    for it in items:
        if it["item"] == name:
            return it
    return None


def check(label, left, right, diffs):
    if left is None or right is None:
        diffs.append((label, left, right, "披露缺失/未取到"))
    elif left != right:
        diffs.append((label, left, right, "不一致"))
    else:
        diffs.append((label, left, right, "一致"))


def reconcile(st):
    """勾稽校验：报表内部等式（期末与上期两列都验）。"""
    diffs = []
    bs = st["合并资产负债表"]
    for col in ("期末余额", "期初余额"):
        g = lambda n: (find(bs, n) or {}).get(col)
        check(f"资产总计=流动资产合计+非流动资产合计 [{col}]",
              g("资产总计"), (g("流动资产合计") or 0) + (g("非流动资产合计") or 0), diffs)
        check(f"负债合计=流动负债合计+非流动负债合计 [{col}]",
              g("负债合计"), (g("流动负债合计") or 0) + (g("非流动负债合计") or 0), diffs)
        check(f"资产总计=负债合计+所有者权益合计 [{col}]",
              g("资产总计"), (g("负债合计") or 0) + (g("所有者权益合计") or 0), diffs)
        check(f"负债和所有者权益总计=资产总计 [{col}]",
              g("负债和所有者权益总计"), g("资产总计"), diffs)
        check(f"所有者权益合计=归母+少数股东 [{col}]",
              g("所有者权益合计"), (g("归属于母公司所有者权益合计") or 0) + (g("少数股东权益") or 0), diffs)

    is_ = st["合并利润表"]
    for col in ("本期发生额", "上期发生额"):
        g = lambda n: (find(is_, n) or {}).get(col)
        check(f"净利润=归母+少数股东损益 [{col}]",
              g("五、净利润（净亏损以“－”号填列）"), (g("1.归属于母公司所有者的净利润") or 0) + (g("2.少数股东损益") or 0), diffs)
        check(f"利润总额=营业利润+营业外收入-营业外支出 [{col}]",
              g("四、利润总额（亏损总额以“－”号填列）"),
              (g("三、营业利润（亏损以“－”号填列）") or 0) + (g("加：营业外收入") or 0) - (g("减：营业外支出") or 0), diffs)

    cf = st["合并现金流量表"]
    for col in ("本期发生额", "上期发生额"):
        g = lambda n: (find(cf, n) or {}).get(col)
        check(f"经营净额=流入小计-流出小计 [{col}]",
              g("经营活动产生的现金流量净额"), (g("经营活动现金流入小计") or 0) - (g("经营活动现金流出小计") or 0), diffs)
        check(f"现金净增加额=经营+投资+筹资+汇率影响 [{col}]",
              g("五、现金及现金等价物净增加额"),
              (g("经营活动产生的现金流量净额") or 0) + (g("投资活动产生的现金流量净额") or 0)
              + (g("筹资活动产生的现金流量净额") or 0) + (g("四、汇率变动对现金及现金等价物的影响") or 0), diffs)
        check(f"期末现金=期初+净增加额 [{col}]",
              g("六、期末现金及现金等价物余额"),
              (g("加：期初现金及现金等价物余额") or 0) + (g("五、现金及现金等价物净增加额") or 0), diffs)
    return diffs


def main():
    pdf_path, out_dir, sample = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    out_dir.mkdir(parents=True, exist_ok=True)
    st = to_dict(extract(pdf_path))
    out = {
        "sample": sample,
        "source_pdf": str(pdf_path),
        "unit": "人民币千元（每股收益为元）",
        "statements": st,
    }
    out_file = out_dir / f"{sample}_statements.yaml"
    out_file.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    counts = {k: len(v) for k, v in st.items()}
    print(f"extracted -> {out_file}  rows={counts}")

    diffs = reconcile(st)
    ok = sum(1 for d in diffs if d[3] == "一致")
    print(f"reconciliation: {ok}/{len(diffs)} 一致")
    for label, l, r, status in diffs:
        mark = "✓" if status == "一致" else "✗"
        print(f"  {mark} {label}: {l} vs {r} [{status}]")


if __name__ == "__main__":
    main()
