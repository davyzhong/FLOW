#!/usr/bin/env python3
"""阿里巴巴集團（9988.HK，US GAAP）年度業績公告三大表 + 菜鳥分部序列抽取。

来源：港交所披露易官方公告 PDF（FY2020/2021/2022/2024/2025/2026 六份，各含本期+上期年度列）。
每份公告列结构：[季度上期RMB, 季度本期RMB, 季度本期USD, 年度上期RMB, 年度本期RMB, 年度本期USD]，
取年度两列人民币值（百万）。财状表 3 列 [上期, 本期, 本期USD]。

产出（docs/implementation/p5/）：
  alibaba_{FY}fy_statements.yaml ×8（FY2019–FY2026）
  cainiao_segment_series.yaml（菜鸟分部收入 FY2019–FY2025 + 经调整 EBITA FY2023–FY2025）
条目名为统一规范名（公告原文行名变体在脚本内做别名归一）。

用法（在 services/api 目录下）：.venv/bin/python ../../scripts/p5_extract_alibaba.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = REPOSITORY_ROOT / "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988"
OUT_DIR = REPOSITORY_ROOT / "docs/implementation/p5"

NUM = re.compile(r"\(-?[\d,]+\)|-?\d[\d,]*\d|-?\d")
PCT = re.compile(r"\(-?[\d,]+\)%|-?\d[\d,]*\d%|-?\d%")
FOOTNOTE = re.compile(r"^\(\d\)$")  # 仅 (1)-(9) 单数字脚注标记；多位如 (569) 是负数

# 每份公告：文件、财年（本期）、损益/财状/现金流起始页（0 起）、年度分部收入表页与列位
# FY2020-22 及 FY2024-25 公告的「其他淨收支」列于经营利润之下（不进经营链）；FY2026 列于其上
OTHER_IN_OP = {2020: False, 2021: False, 2022: False, 2024: False, 2025: False, 2026: True}

DOCS = {
    2020: dict(file="BABA_FY2020_annual_results.pdf", pages=dict(IS=37, BS=40, CF=42),
               seg=dict(page=24, prior=0, cur=2, label="菜鳥物流服務")),
    2021: dict(file="BABA_FY2021_annual_results.pdf", pages=dict(IS=34, BS=37, CF=39),
               seg=dict(page=22, prior=0, cur=2, label="菜鳥物流服務")),
    2022: dict(file="BABA_FY2022_annual_results.pdf", pages=dict(IS=38, BS=42, CF=44),
               seg=dict(page=26, prior=0, cur=2, label="菜鳥")),
    2024: dict(file="BABA_FY2024_annual_results.pdf", pages=dict(IS=32, BS=33, CF=35),
               seg=dict(page=19, prior=0, cur=1, label="菜鳥集團", ncols=4),
               seg_ebita=dict(page=20, prior=0, cur=1, ncols=4)),
    2025: dict(file="BABA_FY2025_annual_results.pdf", pages=dict(IS=30, BS=32, CF=34),
               seg=dict(page=17, prior=0, cur=1, label="菜鳥集團", ncols=4),
               seg_ebita=dict(page=18, prior=0, cur=1, ncols=4)),
    2026: dict(file="BABA_FY2026_annual_results.pdf", pages=dict(IS=30, BS=32, CF=34),
               seg=None,  # FY2026 起菜鸟并入「所有其他」，无单独分部行
               ),
}

# 损益表统一行（canonical ← 原文行名别名前缀，命中即用）
PL_SPEC = [
    ("收入", ["收入"]),
    ("營業成本", ["營業成本"]),
    ("產品開發費用", ["產品開發費用"]),
    ("銷售和市場費用", ["銷售和市場費用"]),
    ("一般及行政費用", ["一般及行政費用"]),
    ("無形資產攤銷及減值", ["無形資產攤銷及減值", "無形資產攤銷和減值", "無形資產攤銷"]),
    ("商譽減值", ["商譽減值"]),
    ("其他淨（損失）收益", ["其他淨（損失）收益"], "opt"),
    ("其他淨收支", ["其他淨收支", "其他淨收入", "其他淨收益"]),
    ("經營利潤（虧損）", ["經營利潤（虧損）", "經營利潤(虧損)", "經營(虧損)利潤", "經營利潤"]),
    ("利息收入和投資淨收益", ["利息收入和投資淨收益"]),
    ("利息費用", ["利息費用"]),
    ("扣除所得稅及權益法核算的投資損益前的利潤",
     ["扣除所得稅及權益法核算的投資損益前的利潤", "扣除所得稅及權益法核算的投資損益前的(虧損)利潤"]),
    ("所得稅費用", ["所得稅費用"]),
    ("權益法核算的投資損益", ["權益法核算的投資損益"]),
    ("淨利潤", ["淨利潤", "淨(虧損)利潤"]),
    ("歸屬於非控制性權益損益", ["歸屬於非控制性權益的淨損失", "歸屬於非控制性權益的淨虧損"], "flip"),
    ("歸屬於阿里巴巴集團股東的淨利潤", ["歸屬於阿里巴巴集團股東的淨利潤", "歸屬於阿里巴巴集團股東的淨（虧損）利潤", "歸屬於阿里巴巴集團股東的淨(虧損)利潤"]),
]

BS_SPEC = [
    ("現金及現金等價物", ["現金及現金等價物"]),
    ("短期投資", ["短期投資"]),
    ("受限制現金及應收託管資金", ["受限制現金及應收託管資金"]),
    ("股權證券及其他投資", ["股權證券及其他投資", "證券投資"]),
    ("權益法核算的投資", ["權益法核算的投資", "股權投資"]),
    ("物業及設備（淨值）", ["物業及設備（淨值）"]),
    ("無形資產（淨值）", ["無形資產（淨值）"]),
    ("商譽", ["商譽"]),
    ("流動資產總額", ["流動資產總額"]),
    ("資產總額", ["資產總額"]),
    ("短期銀行借款", ["短期銀行借款"]),
    ("應付所得稅", ["應付所得稅"]),
    ("預提費用、應付款項及其他負債", ["預提費用、應付款項及其他負債"]),
    ("商家保證金", ["商家保證金"]),
    ("遞延收入和客戶預付款", ["遞延收入和客戶預付款", "遞延收入及客戶預付款"]),
    ("流動負債總額", ["流動負債總額"]),
    ("負債總額", ["負債總額"]),
    ("夾層權益", ["夾層權益"]),
    ("普通股", ["普通股"]),
    ("資本公積", ["資本公積"]),
    ("庫存股（按成本計）", ["庫存股（按成本計）"]),
    ("法定儲備", ["法定儲備"]),
    ("累計其他綜合收益（損失）", ["累計其他綜合收益（損失）", "累計其他綜合損失", "累計其他綜合（損失）收益", "累計其他綜合收益"]),
    ("未分配利潤", ["未分配利潤"]),
    ("股東權益總額", ["股東權益總額"]),
    ("非控制性權益", ["非控制性權益"]),
    ("權益總額", ["權益總額"]),
    ("負債、夾層權益及權益總額", ["負債、夾層權益及權益總額"]),
]

CF_SPEC = [
    ("經營活動產生的現金流量淨額", ["經營活動產生的現金流量淨額", "經營活動產生（所用）的現金流量淨額"]),
    ("投資活動所用現金流量淨額", ["投資活動所用的現金流量淨額", "投資活動（所用）產生的現金流量淨額", "投資活動產生（所用）的現金流量淨額"]),
    ("融資活動所用現金流量淨額",
     ["融資活動所用的現金流量淨額", "融資活動產生的現金流量淨額",
      "融資活動產生（所用）產生的現金流量淨額", "融資活動產生（所用）的現金流量淨額"]),
    ("匯率變動對現金的影響", ["匯率變動對現金及現金等價物"]),
    ("現金淨（減少）增加", ["現金及現金等價物、受限制現金及應收託管資金的（減少）增加",
                     "現金及現金等價物、受限制現金及應收託管資金的增加（減少）",
                     "現金及現金等價物、受限制現金及應收託管資金的增加（減少）".replace("的增", "的增加")]),
    ("期初現金及現金等價物", ["期初現金及現金等價物"]),
    ("期末現金及現金等價物", ["期末現金及現金等價物"]),
]


def _build_index(text: str) -> tuple[str, list[int]]:
    stripped_chars, pos_map = [], []
    for i, ch in enumerate(text):
        if not ch.isspace():
            stripped_chars.append(ch)
            pos_map.append(i)
    return "".join(stripped_chars), pos_map


def _find_key(text: str, pos_map: list[int], stripped: str, key: str, base: int = 0) -> int:
    """find 且要求命中在原文中位于行首（标签都从行首起），避免命中行内子串。"""
    start = base
    while True:
        idx = stripped.find(key, start)
        if idx < 0:
            return -1
        if idx == 0 or text[pos_map[idx] - 1].isspace():
            return idx
        start = idx + 1


def _collect(text: str, stripped: str, pos_map: list[int], key: str, ncols: int) -> list[int | None]:
    idx = _find_key(text, pos_map, stripped, key)
    if idx < 0:
        return []
    orig_end = pos_map[idx + len(key) - 1] + 1
    toks: list[str] = []
    for tok in text[orig_end:].split():
        if PCT.fullmatch(tok):
            tok = tok[:-1]  # 分部表百分比列：剥 % 后当数值占位收集（只按列位取人民币列）
        if not toks and FOOTNOTE.match(tok):
            continue  # 行名与数值之间的脚注标记（如「淨額(1)」的 (1)）
        if NUM.fullmatch(tok) or tok in {"—", "–", "-", "不適用", "不适用"}:
            toks.append(tok)
            if len(toks) == ncols:
                break
        elif toks:
            break
    if len(toks) < ncols:
        return []
    vals: list[int | None] = []
    for t in toks:
        if t in {"—", "–", "-", "不適用", "不适用"}:
            vals.append(None)
        else:
            neg = t.startswith("(") and t.endswith(")")
            v = int(t.strip("()").replace(",", ""))
            vals.append(-v if neg else v)
    return vals


def _extract_table(pdf, pages: list[int], spec: list[tuple], ncols: int,
                   after_key: str | None = None) -> dict[str, list[int | None]]:
    text = "\n".join((pdf.pages[p].extract_text() or "") for p in pages)
    stripped, pos_map = _build_index(text)
    base = 0
    if after_key:
        base = _find_key(text, pos_map, stripped, after_key.replace(" ", ""))
        if base < 0:
            raise SystemExit(f"锚点未找到: {after_key}")
    out: dict[str, list[int | None]] = {}
    for entry in spec:
        canonical, aliases = entry[0], entry[1]
        flag = entry[2] if len(entry) > 2 else None
        for key in aliases:
            idx = _find_key(text, pos_map, stripped, key.replace(" ", ""), base)
            if idx >= 0:
                vals = _collect(text, stripped, pos_map, key.replace(" ", ""), ncols)
                if vals:
                    if flag == "flip":
                        vals = [None if v is None else -v for v in vals]
                    out[canonical] = vals
                    break
        else:
            if flag != "opt":
                print(f"  [warn] 未找到: {canonical}")
    return out


def _check(ok_all: list[bool], label: str, got: int | None, expect: int | None) -> None:
    ok = got is not None and expect is not None and got == expect
    ok_all.append(ok)
    mark = "✓" if ok else "✗"
    print(f"  {mark} {label}: {got} vs {expect}")


def _g(row: dict[str, list[int | None]], col: int) -> int | None:
    vals = row.get(row and next(iter(row)))  # placeholder, unused
    return None


def main() -> int:
    import pdfplumber

    all_ok: list[bool] = []
    segment_series: dict[str, dict[str, int | None]] = {}
    segment_sources: dict[str, str] = {}

    for fy, cfg in sorted(DOCS.items()):
        print(f"===== 阿里巴巴 FY{fy} 公告 =====")
        pdf = pdfplumber.open(SAMPLES / cfg["file"])
        pages = cfg["pages"]
        pl = _extract_table(pdf, [pages["IS"]], PL_SPEC, ncols=6)
        bs = _extract_table(pdf, [pages["BS"], pages["BS"] + 1], BS_SPEC, ncols=3,
                            after_key=None)
        # 非流动「遞延收入」与流动「遞延收入和客戶預付款」前缀冲突：不抽单独遞延收入行
        cf = _extract_table(pdf, [pages["CF"]], CF_SPEC, ncols=6)
        pdf.close()

        for col, year in ((3, fy - 1), (4, fy)):
            print(f"-- FY{year} 年度列勾稽 --")
            pg = lambda name: (pl.get(name) or [None] * 6)[col]  # noqa: E731
            bg = lambda name: (bs.get(name) or [None] * 3)[col - 3]  # noqa: E731
            cg = lambda name: (cf.get(name) or [None] * 6)[col]  # noqa: E731
            _check(all_ok, "經營利潤=收入+各項",
                   pg("經營利潤（虧損）"),
                   (pg("收入") or 0) + (pg("營業成本") or 0) + (pg("產品開發費用") or 0)
                   + (pg("銷售和市場費用") or 0) + (pg("一般及行政費用") or 0)
                   + (pg("無形資產攤銷及減值") or 0) + (pg("商譽減值") or 0)
                   + (pg("其他淨（損失）收益") or 0))
            _check(all_ok, "扣除前=經營+利息投資+利息費用+其他",
                   pg("扣除所得稅及權益法核算的投資損益前的利潤"),
                   (pg("經營利潤（虧損）") or 0) + (pg("利息收入和投資淨收益") or 0)
                   + (pg("利息費用") or 0) + (pg("其他淨收支") or 0))
            _check(all_ok, "淨利潤=扣除前+所得稅+權益法",
                   pg("淨利潤"),
                   (pg("扣除所得稅及權益法核算的投資損益前的利潤") or 0)
                   + (pg("所得稅費用") or 0) + (pg("權益法核算的投資損益") or 0))
            _check(all_ok, "淨利潤=歸屬阿里+非控制",
                   pg("淨利潤"),
                   (pg("歸屬於阿里巴巴集團股東的淨利潤") or 0)
                   + (pg("歸屬於非控制性權益損益") or 0))
            _check(all_ok, "資產總額=負債+夾層+權益",
                   bg("資產總額"),
                   (bg("負債總額") or 0) + (bg("夾層權益") or 0) + (bg("權益總額") or 0))
            _check(all_ok, "權益總額=股東權益+非控制",
                   bg("權益總額"),
                   (bg("股東權益總額") or 0) + (bg("非控制性權益") or 0))
            _check(all_ok, "負債夾層權益總額=資產總額",
                   bg("負債、夾層權益及權益總額"), bg("資產總額"))
            _check(all_ok, "期末現金=期初+三活動+匯率",
                   cg("期末現金及現金等價物"),
                   (cg("期初現金及現金等價物") or 0) + (cg("經營活動產生的現金流量淨額") or 0)
                   + (cg("投資活動所用現金流量淨額") or 0)
                   + (cg("融資活動所用現金流量淨額") or 0)
                   + (cg("匯率變動對現金的影響") or 0))
            bs_cash = (bg("現金及現金等價物") or 0) + (bg("受限制現金及應收託管資金") or 0)
            _check(all_ok, "財狀現金合計=現金流量表期末", bs_cash, cg("期末現金及現金等價物"))

            # 落 YAML：cur 列为 year；上一年若没有自己的公告（如 FY2023）则由本公告上期列补一份
            if year == fy - 1 and (year in DOCS or year < min(DOCS)):
                continue
            prior_col = col - 1 if year == fy else None
            payload = {
                "sample": f"alibaba_{year}fy",
                "source_pdf": f"docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/{cfg['file']}",
                "unit": "人民币百万元（每股数据除外）",
                "statements": {},
            }
            for st_key, rows in (("合并利润表", pl), ("合并资产负债表", bs), ("合并现金流量表", cf)):
                cur_i, prior_i = (col, col - 1) if rows is not bs else (col - 3, col - 4)
                items = []
                for name, vals in rows.items():
                    if len(vals) <= cur_i:
                        print(f"  [warn] 跳过短行: {st_key}/{name} vals={vals}")
                        continue
                    item = {"item": name, "本期发生额": vals[cur_i]}
                    if prior_i is not None and prior_i >= 0:
                        item["上期发生额"] = vals[prior_i]
                    items.append(item)
                payload["statements"][st_key] = items
            out = OUT_DIR / f"alibaba_{year}fy_statements.yaml"
            out.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                           encoding="utf-8")
            counts = {k: len(v) for k, v in payload["statements"].items()}
            print(f"  written {out.name} rows={counts}")

        # 菜鸟分部行
        seg = cfg.get("seg")
        if seg:
            pdf = pdfplumber.open(SAMPLES / cfg["file"])
            text = pdf.pages[seg["page"]].extract_text() or ""
            pdf.close()
            stripped, pos_map = _build_index(text)
            vals = _collect(text, stripped, pos_map, seg["label"], seg.get("ncols", 6))
            if not vals:
                raise SystemExit(f"FY{fy} 菜鸟分部行未取到")
            segment_series[f"FY{fy - 1}"] = {"segment_revenue": vals[seg["prior"]]}
            segment_series[f"FY{fy}"] = {"segment_revenue": vals[seg["cur"]]}
            segment_sources[f"FY{fy - 1}"] = segment_sources.get(f"FY{fy - 1}") or cfg["file"]
            segment_sources[f"FY{fy}"] = cfg["file"]
        seg_ebita = cfg.get("seg_ebita")
        if seg_ebita:
            pdf = pdfplumber.open(SAMPLES / cfg["file"])
            text = pdf.pages[seg_ebita["page"]].extract_text() or ""
            pdf.close()
            stripped, pos_map = _build_index(text)
            vals = _collect(text, stripped, pos_map, "菜鳥集團", seg_ebita.get("ncols", 6))
            if not vals:
                raise SystemExit(f"FY{fy} 菜鸟 EBITA 行未取到")
            segment_series.setdefault(f"FY{fy - 1}",
             {})["adjusted_ebita"] = vals[seg_ebita["prior"]]
            segment_series.setdefault(f"FY{fy}", {})["adjusted_ebita"] = vals[seg_ebita["cur"]]
            segment_sources.setdefault(f"FY{fy - 1}", cfg["file"])
            segment_sources[f"FY{fy}"] = cfg["file"]

    seg_payload = {
        "sample": "cainiao_segment_series",
        "company": "菜鸟智慧物流网络（阿里巴巴集团分部披露口径）",
        "unit": "人民币百万元",
        "note": "FY2026 起阿里巴巴将菜鸟重分类至「所有其他」分部，单独分部数据止于 FY2025；"
                "FY2019-FY2022 经调整 EBITA 未在公告分部表中单列，如实缺省。",
        "sources": segment_sources,
        "series": {k: segment_series[k] for k in sorted(segment_series)},
    }
    seg_out = OUT_DIR / "cainiao_segment_series.yaml"
    seg_out.write_text(yaml.safe_dump(seg_payload, allow_unicode=True, sort_keys=False),
                       encoding="utf-8")
    print("segment series ->", seg_out.name)
    for k, v in seg_payload["series"].items():
        print(" ", k, v)

    ok = sum(1 for x in all_ok if x)
    print(f"reconciliation: {ok}/{len(all_ok)}")
    return 0 if ok == len(all_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
