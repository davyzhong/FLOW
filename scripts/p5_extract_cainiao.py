#!/usr/bin/env python3
"""菜鸟智慧物流网络（未上市）招股书会计师报告三大报表抽取。

来源：港交所申请版本（2023-09-26 递交，2024-03 撤回；stat times 官方文档镜像），
附录 I 会计师报告（PwC，IFRS，人民币千元）。
覆盖：FY2021 / FY2022 / FY2023（截至 3 月 31 日止年度）+ 两个未经审计 Q1 stub（不导入）。

产出（docs/implementation/p5/）：
  cainiao_2021fy_statements.yaml / cainiao_2022fy_statements.yaml / cainiao_2023fy_statements.yaml
条目名为抽取时翻译的中文规范名，与 item_alias_map_v1.yaml 的 cainiao_private 节一致。

用法（在 services/api 目录下）：.venv/bin/python ../../scripts/p5_extract_cainiao.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = (
    REPOSITORY_ROOT
    / "docs/knowledge-base/02_research/original/p5_samples/cainiao_private/"
    / "Cainiao_application_proof_20230926.pdf"
)
OUT_DIR = REPOSITORY_ROOT / "docs/implementation/p5"

# 报表页（0 起，见脚本验证日志）：损益 463，财状 465-466，现金流量 473-474。
PAGE_PL = 463
PAGE_BS = 465
PAGE_BS_END = 466
PAGE_CF = 473
PAGE_CF_END = 474

# 年度列位置（每行 5 列：FY2021 FY2022 FY2023 Q1FY23stub Q1FY24stub）
YEAR_COLS = {"2021": 0, "2022": 1, "2023": 2}

# 损益表行（英文原文 → 中文规范名，括注符号约定：源值带括号为负，按披露原值入账）
PL_ROWS = [
    ("Revenue", "收入"),
    ("Cost of revenue", "营业成本"),
    ("Gross profit", "毛利"),
    ("Sales and marketing expenses", "销售及市场推广开支"),
    ("General and administrative expenses", "一般及行政开支"),
    ("Product development expenses", "产品开发开支"),
    ("Reversal of/(provision for) impairment losses on financial assets", "金融资产减值(转回)/计提"),
    ("Other income", "其他收入"),
    ("Other gains/(losses) – net", "其他收益/(亏损)净额"),
    ("Operating (loss)/profit", "经营亏损/利润"),
    ("Finance income", "财务收入"),
    ("Finance costs – net", "财务成本净额"),
    ("Finance costs", "财务成本"),
    ("Share of (loss)/profit of associates and joint ventures accounted for using the equity method", "应占联营及合营损益"),
    ("Impairment losses on associates and joint ventures accounted for using the equity method", "联营及合营减值"),
    ("(Loss)/profit before income tax", "除税前亏损/利润"),
    ("Income tax expenses", "所得税开支"),
    ("(Loss)/profit for the year/period", "年度亏损/利润"),
    ("Owners of the Company", "归属公司所有者"),
    ("Non-controlling interests", "非控制性权益"),
]

BS_ROWS = [
    ("Property, plant and equipment", "物业、厂房及设备"),
    ("Investment properties", "投资物业"),
    ("Right-of-use assets (land use rights)", "使用权资产(土地使用权)"),
    ("Other right-of-use assets", "其他使用权资产"),
    ("Intangible assets", "无形资产"),
    ("Goodwill", "商誉"),
    ("Investments accounted for using the equity method", "权益法核算的投资"),
    ("Deferred tax assets", "递延税项资产"),
    ("Financial assets at fair value through profit or loss", "按公允价值计量的金融资产"),
    ("Other receivables and prepayments", "其他应收及预付款(非流动)"),
    ("Inventories", "存货"),
    ("Trade, other receivables and prepayments", "贸易应收及其他预付款(流动)"),
    ("Restricted cash", "受限制现金"),
    ("Cash and cash equivalents", "现金及现金等价物"),
    ("Term deposits", "定期存款"),
    ("Borrowings", "借款"),
    ("Lease liabilities", "租赁负债"),
    ("Financial liabilities designated at fair value through profit or loss", "指定按公允价值计量的金融负债"),
    ("Long-term payables", "长期应付款"),
    ("Other financial liabilities", "其他金融负债"),
    ("Deferred revenue", "递延收入(非流动)"),
    ("Deferred tax liabilities", "递延税项负债"),
    ("Current tax liabilities", "本期税项负债"),
    ("Trade and other payables", "贸易及其他应付款"),
    ("Contract liabilities", "合同负债"),
    ("Share capital", "股本"),
    ("Share premium", "股份溢价"),
    ("Other reserves", "其他储备"),
    ("Accumulated losses", "累计亏损"),
    ("Non-controlling interests", "非控制性权益(权益)"),
]

# 带排序的小计/合计（原文中以独立数字行出现，无行名）
BS_TOTAL_ROWS = [
    ("非流动资产合计", 0), ("流动资产合计", 1), ("资产总计", 2),
    ("归属于公司所有者权益", 3), ("权益总额", 4),
    ("非流动负债合计", 5), ("流动负债合计", 6), ("负债合计", 7),
    ("权益及负债总额", 8),
]

CF_ROWS = [
    ("Cash generated from/(used in) operations", "经营活动产生/(所用)现金"),
    ("Income taxes paid", "已付所得税"),
    ("Net cash flows generated from/(used in) operating activities", "经营活动所得现金净额"),
    ("Payments for business combination, net of cash acquired", "业务合并付款(扣除所得现金)"),
    ("Net cash inflow arising from disposals of investments in subsidiaries", "出售附属公司投资所得现金流入净额"),
    ("Purchase of property, plant and equipment, investment properties, land use rights and intangible assets", "购置物业设备、投资物业、土地使用权及无形资产"),
    ("Government grants received relating to assets", "与资产有关的政府补助"),
    ("Proceeds from disposals of property, plant and equipment and land use rights", "出售物业设备及土地使用权所得"),
    ("Payments for acquisitions of financial assets at fair value through profit or loss", "购入按公允价值计量金融资产"),
    ("Proceeds from disposals of financial assets at fair value through profit or loss", "出售按公允价值计量金融资产所得"),
    ("Dividends and interest income from financial assets at fair value through profit or loss", "金融资产股息及利息收入"),
    ("Placement of term deposits with initial terms of over three months", "存放三个月以上定期存款"),
    ("Withdrawal of term deposits with initial terms of over three months", "提取三个月以上定期存款"),
    ("Interest received from term deposits with initial terms of over three months", "定期存款利息收入"),
    ("Payments for acquisitions of investments in associates and joint ventures", "购入联营及合营投资"),
    ("Dividends received from investments in associates", "联营投资股息"),
    ("Loans to related parties", "贷予关联方款项"),
    ("Repayment of loans to related parties", "关联方还款"),
    ("Interest received from loans to related parties", "关联方贷款利息"),
    ("Repayments of loans from a third party", "第三方借款偿还"),
    ("Net cash flows (used in)/generated from investing activities", "投资活动所用现金净额"),
    ("Capital injections from shareholders", "股东注资"),
    ("Net proceeds from issuance of ordinary shares as a result of exercise of share options and other share movements", "发行股份所得款项净额"),
    ("Payments for acquisitions of non-controlling interests", "收购非控制性权益付款"),
    ("Proceeds from issuance of additional equity of non wholly-owned subsidiaries", "非全资附属公司增资所得"),
    ("Proceeds from partial disposals of equity interests in non wholly-owned subsidiaries", "部分出售非全资附属公司权益所得"),
    ("Distribution of liquidated assets to non-controlling interests upon the liquidation of a subsidiary", "附属公司清算资产分配"),
    ("Proceeds from cash injections by the partner of consolidated", "合并有限合伙伙伴现金注入"),
    ("Cash redemption to the partner of", "合并有限合伙伙伴现金赎回"),
    ("Dividends paid to the partner of", "付合并有限合伙伙伴股息"),
    ("Proceeds from borrowings", "借款所得款项"),
    ("Repayments of borrowings", "借款偿还"),
    ("Interest of borrowings paid", "已付借款利息"),
    ("Loans from related parties", "关联方贷款"),
    ("Payments of lease liabilities", "租赁负债付款"),
    ("Payments of deposits to lessors at the beginning of lease contracts", "租赁开始时付出租方押金"),
    ("Collection of deposits from lessors at the expiry of lease contracts", "租赁到期收出租方押金"),
    ("Release of restricted cash of asset-backed securities (“ABS”) issuance proceeds", "ABS 发行受限现金解除"),
    ("Repayments ofABS", "ABS 偿还"),
    ("Interest ofABS paid", "已付 ABS 利息"),
    ("Payments for settlement of put", "卖出期权负债结算付款"),
    ("Net cash flows (used in)/generated from financing activities", "融资活动(所用)所得现金净额"),
    ("Net (decrease)/increase in cash and cash equivalents", "现金及现金等价物(减少)/增加净额"),
    ("Cash and cash equivalents at the beginning of the year/period", "年初现金及现金等价物"),
    ("Effects of exchange rate changes on cash and cash equivalents", "汇率变动对现金的影响"),
    ("Cash and cash equivalents at the end of the year/period", "年末现金及现金等价物"),
]

_NUM = re.compile(r"\(-?[\d,]+\)|-?\d[\d,]*\d|-?\d")
_TOKEN = re.compile(r"\(-?[\d,]+\)|-?[\d][\d,]*|–|—")
_NOTE = re.compile(r"^\d{1,2}(?:\([a-z]\))?\)?,?$")


def _parse_value(raw: str) -> int | None:
    raw = raw.strip()
    if raw in {"–", "-", "—", ""}:
        return None
    neg = raw.startswith("(") and raw.endswith(")")
    digits = raw.strip("()").replace(",", "")
    value = int(digits)
    return -value if neg else value


def _page_lines(pdf) -> list[str]:
    return (pdf.pages[0].extract_text() or "").split("\n")


def _tail_tokens(tail: str, ncols: int) -> list[int | None]:
    """取行名后第一个数值 token 串（注号已剥），列数不足报错。"""
    toks = _TOKEN.findall(tail[:600])
    while toks and _NOTE.match(toks[0]):
        toks.pop(0)
    if len(toks) < ncols:
        raise SystemExit(f"数值不足（{len(toks)}/{ncols}）: {toks}")
    return [_parse_value(t) for t in toks[:ncols]]


def _extract_rows(pdf, pages: list[int], spec: list[tuple[str, str]], ncols: int = 5) -> dict[str, list[int | None]]:
    """把（可能折行的）行名匹配到 5 列（PL/CF）数值。"""
    text = "\n".join((pdf.pages[p].extract_text() or "") for p in pages)
    lines = [
        ln
        for ln in text.split("\n")
        if not ln.startswith(("THIS DOCUMENT", "READINCONJUNCTION", "APPENDIX"))
        and "DRAFTFORM" not in ln
        and not re.match(r"^– I-\d+ –$", ln.strip())
    ]
    flat = " ".join(ln.strip() for ln in lines)
    # 去空格串用于行名定位；pos_map 把去空格下标映射回原串下标（数值边界依赖空格）
    stripped_chars: list[str] = []
    pos_map: list[int] = []
    for i, ch in enumerate(flat):
        if ch != " ":
            stripped_chars.append(ch)
            pos_map.append(i)
    stripped = "".join(stripped_chars)
    values: dict[str, list[int | None]] = {}
    for en_name, cn_name in spec:
        key = en_name.replace(" ", "")
        idx = stripped.find(key)
        if idx < 0:
            raise SystemExit(f"未找到行: {en_name}")
        orig_end = pos_map[idx + len(key) - 1] + 1
        tail_toks = flat[orig_end:].split()
        if tail_toks and re.fullmatch(r"\d{1,2},?", tail_toks[0]):
            tail_toks = tail_toks[1:]  # 行名后紧贴的注号（≤2 位）
        toks: list[str] = []
        for tok in tail_toks:
            if _NUM.fullmatch(tok) or tok in {"–", "—", "-"}:
                toks.append(tok)
                if len(toks) == ncols:
                    break
            elif toks:
                break  # 数值区结束进入下一行行名
            elif _NOTE.match(tok):
                continue  # 行名后悬挂的注号
        if len(toks) < ncols:
            raise SystemExit(f"数值不足（{len(toks)}/{ncols}）: {en_name} -> {tail_toks[:8]}")
        values[cn_name] = [_parse_value(t) for t in toks]
    return values


def _extract_totals(pdf, pages: list[int]) -> dict[str, list[int | None]]:
    """财状表小计/合计行是纯数字行；按出现顺序取前 9 个（每行 5 列）。"""
    text = "\n".join((pdf.pages[p].extract_text() or "") for p in pages)
    lines = [
        ln.strip()
        for ln in text.split("\n")
        if not ln.startswith(("THIS DOCUMENT", "READINCONJUNCTION", "APPENDIX"))
        and "DRAFTFORM" not in ln
        and not re.match(r"^– I-\d+ –$", ln.strip())
    ]
    totals: dict[str, list[int | None]] = {}
    order = [name for name, _ in BS_TOTAL_ROWS]
    known_labels = ("Total assets", "Total equity and liabilities", "Total equity",
                    "Total liabilities")
    ti = 0
    for ln in lines:
        if ti >= len(order):
            break
        toks = ln.split()
        is_pure = len(toks) == 4 and all(_NUM.fullmatch(t) for t in toks)
        is_labeled = any(ln.startswith(lb) for lb in known_labels) and all(
            _NUM.fullmatch(t) for t in toks if _NUM.fullmatch(t)) and sum(
            1 for t in toks if _NUM.fullmatch(t)) == 4
        if is_pure or is_labeled:
            vals = [t for t in toks if _NUM.fullmatch(t)]
            totals[order[ti]] = [_parse_value(t) for t in vals]
            ti += 1
    if ti < len(order):
        raise SystemExit(f"小计行不足: 仅 {ti}/9")
    return totals


def _check(label: str, got: int | None, expect: int | None) -> bool:
    ok = got is not None and expect is not None and got == expect
    mark = "✓" if ok else "✗"
    print(f"  {mark} {label}: {got} vs {expect}")
    return ok


def _g(row: dict[str, list[int | None]], col: str) -> int | None:
    return row[col]


def main() -> int:
    import pdfplumber

    pdf = pdfplumber.open(PDF_PATH)
    pl = _extract_rows(pdf, [PAGE_PL, PAGE_PL + 1], PL_ROWS)
    # 修复：财务成本在"财务成本净额"之后出现（原文顺序 Finance costs 11 / Finance costs – net 11），
    # 前缀匹配会互相错位，按短名重取。
    bs = _extract_rows(pdf, [PAGE_BS, PAGE_BS + 1], BS_ROWS, ncols=4)
    bs_total = _extract_totals(pdf, [PAGE_BS, PAGE_BS_END])
    cf = _extract_rows(pdf, [PAGE_CF, PAGE_CF_END], CF_ROWS)
    pdf.close()

    # "Financial assets at fair value through profit or loss" 在财状表出现两次（非流动/流动），
    # 前缀匹配取到第一处；流动性小计行已由合计行覆盖，此处仅提示。
    print("损益行:", len(pl), " 财状行:", len(bs) + len(bs_total), " 现金流行:", len(cf))

    all_ok = True
    for year, col in YEAR_COLS.items():
        print(f"== FY{year} 勾稽 ==")
        g = lambda name: _g(pl[name], col)  # noqa: E731
        all_ok &= _check("毛利=收入+营业成本", g("毛利"),
                         (g("收入") or 0) + (g("营业成本") or 0))
        all_ok &= _check("经营亏损/利润=毛利+各项", g("经营亏损/利润"),
                         (g("毛利") or 0) + (g("销售及市场推广开支") or 0)
                         + (g("一般及行政开支") or 0) + (g("产品开发开支") or 0)
                         + (g("金融资产减值(转回)/计提") or 0) + (g("其他收入") or 0)
                         + (g("其他收益/(亏损)净额") or 0))
        all_ok &= _check("财务成本净额=财务收入+财务成本", g("财务成本净额"),
                         (g("财务收入") or 0) + (g("财务成本") or 0))
        all_ok &= _check("除税前=经营+财务净额+联营损益+联营减值", g("除税前亏损/利润"),
                         (g("经营亏损/利润") or 0) + (g("财务成本净额") or 0)
                         + (g("应占联营及合营损益") or 0) + (g("联营及合营减值") or 0))
        all_ok &= _check("年度亏损/利润=除税前+所得税", g("年度亏损/利润"),
                         (g("除税前亏损/利润") or 0) + (g("所得税开支") or 0))
        all_ok &= _check("年度=归属+非控制", g("年度亏损/利润"),
                         (g("归属公司所有者") or 0) + (g("非控制性权益") or 0))
        bscol = {"2021": 0, "2022": 1, "2023": 2}[year]
        bg = lambda name: _g(bs_total[name], bscol)  # noqa: E731
        all_ok &= _check("资产总计=非流动+流动", bg("资产总计"),
                         (bg("非流动资产合计") or 0) + (bg("流动资产合计") or 0))
        all_ok &= _check("负债合计=非流动+流动负债", bg("负债合计"),
                         (bg("非流动负债合计") or 0) + (bg("流动负债合计") or 0))
        all_ok &= _check("权益=归母+非控制", bg("权益总额"),
                         (bg("归属于公司所有者权益") or 0)
                         + _g(bs["非控制性权益(权益)"], bscol))
        all_ok &= _check("权益及负债总额=负债+权益", bg("权益及负债总额"),
                         (bg("负债合计") or 0) + (bg("权益总额") or 0))
        all_ok &= _check("资产总计=权益及负债总额", bg("资产总计"), bg("权益及负债总额"))
        cg = lambda name: _g(cf[name], col)  # noqa: E731
        all_ok &= _check("现金净变动=经营+投资+融资", cg("现金及现金等价物(减少)/增加净额"),
                         (cg("经营活动所得现金净额") or 0) + (cg("投资活动所用现金净额") or 0)
                         + (cg("融资活动(所用)所得现金净额") or 0))
        all_ok &= _check("年末现金=年初+净变动+汇率", cg("年末现金及现金等价物"),
                         (cg("年初现金及现金等价物") or 0)
                         + (cg("现金及现金等价物(减少)/增加净额") or 0)
                         + (cg("汇率变动对现金的影响") or 0))
        all_ok &= _check("财状表现金=现金流量表年末", _g(bs["现金及现金等价物"], bscol),
                         cg("年末现金及现金等价物"))

    for year, col in YEAR_COLS.items():
        prior_col = {"2021": None, "2022": 0, "2023": 1}[year]
        payload = {
            "sample": f"cainiao_{year}fy",
            "source_pdf": str(PDF_PATH.relative_to(REPOSITORY_ROOT)),
            "unit": "人民币千元",
            "statements": {},
        }
        for st_key, rows in (("合并利润表", pl), ("合并资产负债表", {**bs, **bs_total}),
                             ("合并现金流量表", cf)):
            items = []
            for name, vals in rows.items():
                item = {"item": name, "本期发生额": vals[col]}
                if prior_col is not None:
                    item["上期发生额"] = vals[prior_col]
                items.append(item)
            payload["statements"][st_key] = items
        out = OUT_DIR / f"cainiao_{year}fy_statements.yaml"
        out.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        counts = {k: len(v) for k, v in payload["statements"].items()}
        print(f"written {out.name} rows={counts}")
    print("ALL OK" if all_ok else "CHECK FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
