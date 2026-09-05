#!/usr/bin/env python3
"""P5 可视化报告生成器：把抽取的结构化报表渲染成自包含 HTML 分析视图。

特性：无 CDN、无外部资源，图表全部为内联 SVG（JS 由嵌入数据绘制）。
数据全部来自 P5 抽取产物（YAML）+ 年报分季度表（构建时从原始 PDF 现解析，不硬编码数字）。

用法：python3 scripts/p5_build_report_view.py
输出：docs/implementation/p5/sf_2026q1_report_view.html
"""
import datetime
import json
import re
import sys
from pathlib import Path

import pdfplumber
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from p5_cross_validate_sf import parse_annual, AR_PDF  # noqa: E402

YAML_PATH = ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"
OUT = ROOT / "docs/implementation/p5/sf_2026q1_report_view.html"

JDL_DIR = ROOT / "docs/knowledge-base/02_research/original/p5_samples/jd_logistics_2618"
JDL_Q1_PDF = JDL_DIR / "JDL_2026_Q1_financial_info.pdf"
JDL_ANN_PDF = JDL_DIR / "JDL_FY2025_annual_results_announcement.pdf"

YI = 100_000  # 千元 -> 亿元
NUM = r"-?\d{1,3}(?:,\d{3})+"


def yi(v):
    return None if v is None else round(v / YI, 2)


def find(items, name):
    for it in items:
        if it["item"] == name:
            return it
    return {}


def parse_jdl():
    """京东物流同业数据：2026Q1 财务资料（p3 摘要表、 p7 Non-IFRS 归母）
    + FY2025 年度业绩公告（p2 全年摘要表、p20 年度利润归属、p25 Non-IFRS 归母）。
    全部为构建期现解析；锚点取不到直接断言失败，不出错图。"""

    def grab(lines, label):
        for ln in lines:
            if ln.strip().startswith(label):
                m = re.findall(NUM, ln)
                if m:
                    return int(m[0].replace(",", ""))
        raise AssertionError(f"JDL 锚点未取到: {label}")

    with pdfplumber.open(str(JDL_Q1_PDF)) as pdf:
        q1_sum = (pdf.pages[2].extract_text() or "").split("\n")   # p3 摘要表
        q1_nif = (pdf.pages[6].extract_text() or "").split("\n")   # p7 Non-IFRS 归母
    q1 = {
        "revenue": grab(q1_sum, "收入"),
        "gross": grab(q1_sum, "毛利"),
        "attr_np": grab(q1_sum, "本公司所有者"),
        "non_ifrs_attr": grab(q1_nif, "本公司所有者"),
    }
    with pdfplumber.open(str(JDL_ANN_PDF)) as pdf:
        fy_sum = (pdf.pages[1].extract_text() or "").split("\n")    # p2 全年摘要表（p1 为 Q4 单季，勿用）
        fy_attr = (pdf.pages[19].extract_text() or "").split("\n")  # p20 年度利润归属
        fy_nif = (pdf.pages[24].extract_text() or "").split("\n")   # p25 Non-IFRS 归母
    fy = {
        "revenue": grab(fy_sum, "收入"),
        "gross": grab(fy_sum, "毛利"),
        "profit": grab(fy_sum, "年度利潤"),
        "attr_np": grab(fy_attr, "本公司所有者"),
        "non_ifrs_attr": grab(fy_nif, "本公司所有者"),
    }
    return q1, fy


TENCENT_DIR = ROOT / "docs/knowledge-base/02_research/original/p5_samples/tencent_0700"
TENCENT_Q2_PDF = TENCENT_DIR / "Tencent_2026_Q2_results.pdf"
TENCENT_OUT = ROOT / "docs/implementation/p5/tencent_2026q2_report_view.html"

PARENUM = r"\(\d{1,3}(?:,\d{3})*\)|\d{1,3}(?:,\d{3})*"  # 腾讯公告含无千分位的 3 位数（如 (480)、861）


def parse_signed(s):
    neg = s.startswith("(")
    return -int(s.strip("()").replace(",", "")) if neg else int(s.replace(",", ""))


def parse_tencent():
    """腾讯 2Q2026 业绩公告：p5 简明综合收益表（三列：2Q2026/2Q2025/1Q2026）
    + p9 IFRS→Non-IFRS 调节表（首个『本公司权益持有人应占盈利』行即 2Q2026）。
    单位：人民币百万元。锚点取不到即断言失败。"""

    def grab3(lines, label):
        for ln in lines:
            t = ln.strip()
            if t.split(" ")[0] == label:
                m = re.findall(PARENUM, t)
                if len(m) >= 3:
                    return [parse_signed(x) for x in m[:3]]
        raise AssertionError(f"腾讯锚点未取到: {label}")

    with pdfplumber.open(str(TENCENT_Q2_PDF)) as pdf:
        is_lines = (pdf.pages[4].extract_text() or "").split("\n")   # p5 收益表
        rec_text = pdf.pages[8].extract_text() or ""                 # p9 调节表

    labels = ["收入", "增值服务", "营销服务", "金融科技及企业服务", "其他", "收入成本", "毛利",
              "销售及市场推广开支", "一般及行政开支", "其他收益/（亏损）净额", "经营盈利",
              "投资收益/（亏损）净额及其他", "利息收入", "财务成本",
              "分占联营公司及合营公司盈利/（亏损）净额", "除税前盈利", "所得税开支", "期内盈利",
              "本公司权益持有人", "非控制性权益",
              "非国际财务报告准则经营盈利", "本公司权益持有人应占盈利"]
    stmt = {lb: grab3(is_lines, lb) for lb in labels}

    rec_line = None
    for ln in rec_text.split("\n"):
        if ln.strip().startswith("本公司权益持有人应占盈利"):
            rec_line = ln.strip()
            break
    assert rec_line, "调节表归母行未取到"
    vals = [parse_signed(x) for x in re.findall(PARENUM, rec_line)]
    assert len(vals) == 9, f"调节表列数异常: {len(vals)}"
    reported, adjs, non_ifrs = vals[0], vals[1:8], vals[8]
    assert reported + sum(adjs) == non_ifrs, "IFRS→Non-IFRS 调节链不闭合"
    # 与收益表交叉勾稽：已报告列 = IFRS 归母，调节结果 = Non-IFRS 归母
    assert reported == stmt["本公司权益持有人"][0] and non_ifrs == stmt["本公司权益持有人应占盈利"][0]
    assert sum(stmt[s][0] for s in ["增值服务", "营销服务", "金融科技及企业服务", "其他"]) == stmt["收入"][0], "收入分部加总不闭合"
    return stmt, reported, adjs, non_ifrs


def build_tencent():
    """生成腾讯 2Q2026 IFRS→Non-IFRS 调节分析页（与顺丰页同一生成器、同一无 CDN 约束）。"""
    stmt, reported, adjs, non_ifrs = parse_tencent()
    yib = lambda v: round(v / 100, 2)  # 百万元 -> 亿元

    adj_labels = ["股份酬金", "来自投资公司的（收益）/亏损净额", "无形资产摊销（收购产生）",
                  "减值拨备/（拨回）", "SSV及CPP及其他捐款", "其他（合规/诉讼等）", "所得税影响"]
    adj_notes_text = ["授予雇员（含投资公司雇员）的股份奖励及认沽期权等非现金薪酬",
                      "视同处置/处置投资公司、投资公司公允价值变动等非经营项",
                      "收购产生的无形资产摊销（非现金）",
                      "联营/合营公司、商誉及收购无形资产的减值拨回净额（负值=拨回冲减调整）",
                      "可持续社会价值及共同富裕计划项目的捐款及开支",
                      "非经常性合规相关成本及若干诉讼和解费用",
                      "上述 Non-IFRS 调整的所得税影响"]
    recon = [{"label": "IFRS 归母盈利", "value": yib(reported), "type": "total"}]
    recon += [{"label": lb, "value": yib(v), "type": "delta"} for lb, v in zip(adj_labels, adjs)]
    recon.append({"label": "Non-IFRS 归母盈利", "value": yib(non_ifrs), "type": "total"})
    run = recon[0]["value"]
    for w in recon[1:]:
        if w["type"] == "delta":
            run = round(run + w["value"], 2)
        else:
            assert abs(run - w["value"]) < 0.05, f"调节瀑布链断裂于 {w['label']}"

    def yoy(a, b):
        return round((a - b) / abs(b) * 100, 1)
    rev, gross = stmt["收入"], stmt["毛利"]
    ifrs_np, nifrs_np = stmt["本公司权益持有人"], stmt["本公司权益持有人应占盈利"]
    data = {
        "company": "腾讯控股有限公司", "code": "0700.HK / 80700.HK",
        "period": "2026 年第二季度（2026-04-01 至 2026-06-30），未经审核",
        "source": "腾讯官网业绩公告原文 PDF（tencent_0700/Tencent_2026_Q2_results.pdf）",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "unit_note": "图表单位：人民币亿元（原始披露为百万元，已换算）",
        "kpis": [
            {"name": "营业收入", "cur": yib(rev[0]), "yoy": yoy(rev[0], rev[1])},
            {"name": "毛利", "cur": yib(gross[0]), "yoy": yoy(gross[0], gross[1])},
            {"name": "IFRS 归母盈利", "cur": yib(ifrs_np[0]), "yoy": yoy(ifrs_np[0], ifrs_np[1])},
            {"name": "Non-IFRS 归母盈利", "cur": yib(non_ifrs), "yoy": yoy(nifrs_np[0], nifrs_np[1])},
        ],
        "metrics": [
            {"name": "毛利率", "value": f"{gross[0] / rev[0] * 100:.1f}%", "formula": "毛利÷收入（公告披露 58%）"},
            {"name": "IFRS 归母净利率", "value": f"{ifrs_np[0] / rev[0] * 100:.1f}%", "formula": "IFRS 归母盈利÷收入"},
            {"name": "Non-IFRS 归母净利率", "value": f"{nifrs_np[0] / rev[0] * 100:.1f}%", "formula": "Non-IFRS 归母盈利÷收入"},
            {"name": "调节幅度", "value": f"{(non_ifrs - reported) / reported * 100:.1f}%", "formula": "（Non-IFRS−IFRS）归母盈利÷IFRS 归母盈利"},
            {"name": "经营盈利率（IFRS）", "value": f"{stmt['经营盈利'][0] / rev[0] * 100:.1f}%", "formula": "经营盈利÷收入（公告披露 33%）"},
            {"name": "Non-IFRS 经营盈利率", "value": f"{stmt['非国际财务报告准则经营盈利'][0] / rev[0] * 100:.1f}%", "formula": "Non-IFRS 经营盈利÷收入（公告披露 37%）"},
        ],
        "trend3": {
            "labels": ["2Q2025", "1Q2026", "2Q2026"],
            "revenue": [yib(rev[1]), yib(rev[2]), yib(rev[0])],
            "ifrs_np": [yib(ifrs_np[1]), yib(ifrs_np[2]), yib(ifrs_np[0])],
            "nifrs_np": [yib(nifrs_np[1]), yib(nifrs_np[2]), yib(nifrs_np[0])],
        },
        "recon": recon,
        "segments": [{"label": s, "value": yib(stmt[s][0])} for s in ["增值服务", "营销服务", "金融科技及企业服务", "其他"]],
        "rev_total": yib(rev[0]),
        "stmt_rows": [{"label": lb, "vals": stmt[lb]} for lb in
                      ["收入", "增值服务", "营销服务", "金融科技及企业服务", "其他", "收入成本", "毛利",
                       "销售及市场推广开支", "一般及行政开支", "其他收益/（亏损）净额", "经营盈利",
                       "投资收益/（亏损）净额及其他", "利息收入", "财务成本",
                       "分占联营公司及合营公司盈利/（亏损）净额", "除税前盈利", "所得税开支", "期内盈利",
                       "本公司权益持有人", "非控制性权益",
                       "非国际财务报告准则经营盈利", "本公司权益持有人应占盈利"]],
        "adj_notes": [[lb, f"{'+' if v >= 0 else '−'}{abs(v) / 100:.2f}", note]
                      for lb, v, note in zip(adj_labels, adjs, adj_notes_text)],
    }
    html = TENCENT_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    TENCENT_OUT.write_text(html, encoding="utf-8")
    print(f"written -> {TENCENT_OUT} ({len(html)} bytes)")


def main():
    st = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))["statements"]
    bs, is_, cf = st["合并资产负债表"], st["合并利润表"], st["合并现金流量表"]

    # ---- 趋势：年报分季度（2025Q1-Q4）+ 2026Q1（本期）----
    parse_annual(AR_PDF)  # 触发解析，季度数在下方另行解析
    with pdfplumber.open(str(AR_PDF)) as pdf:
        text15 = pdf.pages[14].extract_text() or ""
        t14 = pdf.pages[13].extract_tables()
    quarterly = {}
    for m in re.finditer(r"(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s*\n([^\n]+)", text15):
        quarterly[m.group(5).strip()] = [int(m.group(i).replace(",", "")) for i in range(1, 5)]
    q_rev = quarterly["营业收入"] + [find(is_, "一、营业总收入")["本期发生额"]]
    q_np = quarterly["归属于上市公司股东的净利润"] + [find(is_, "1.归属于母公司所有者的净利润")["本期发生额"]]
    q_cf = quarterly["经营活动产生的现金流量净额"] + [find(cf, "经营活动产生的现金流量净额")["本期发生额"]]
    trend = {
        "labels": ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1"],
        "revenue": [yi(v) for v in q_rev],
        "net_profit": [yi(v) for v in q_np],
        "ocf": [yi(v) for v in q_cf],
    }

    # ---- 利润瀑布（本期）----
    g = lambda n: (find(is_, n).get("本期发生额") or 0)
    waterfall = [
        {"label": "营业总收入", "value": yi(g("一、营业总收入")), "type": "total"},
        {"label": "营业总成本", "value": yi(-g("二、营业总成本")), "type": "delta"},
        {"label": "其他收益/投资/公允价值", "value": yi(g("加：其他收益") + g("投资收益（损失以“－”号填列）") + g("公允价值变动收益（损失以“－”号填列）")), "type": "delta"},
        {"label": "减值与处置", "value": yi(g("信用减值损失（损失以“-”号填列）") + g("资产减值损失（损失以“-”号填列）") + g("资产处置收益（损失以“-”号填列）")), "type": "delta"},
        {"label": "营业利润", "value": yi(g("三、营业利润（亏损以“－”号填列）")), "type": "total"},
        {"label": "营业外收支", "value": yi(g("加：营业外收入") - g("减：营业外支出")), "type": "delta"},
        {"label": "利润总额", "value": yi(g("四、利润总额（亏损总额以“－”号填列）")), "type": "total"},
        {"label": "所得税", "value": yi(-g("减：所得税费用")), "type": "delta"},
        {"label": "净利润", "value": yi(g("五、净利润（净亏损以“－”号填列）")), "type": "total"},
    ]
    # 瀑布链校验：各 delta 加总必须等于相邻 total 之差（否则生成期就失败，不出错图）
    run = waterfall[0]["value"]
    for w in waterfall[1:]:
        if w["type"] == "delta":
            run = round(run + w["value"], 2)
        else:
            assert abs(run - w["value"]) < 0.02, f"瀑布链断裂于 {w['label']}: {run} vs {w['value']}"

    # ---- 资产负债结构（top N + 其他，期末与期初两列）----
    def seg_items(items, start_after, stop_at, skip, col):
        seg, started = [], False
        for it in items:
            nm = it["item"]
            if nm == start_after:
                started = True
                continue
            if nm == stop_at:
                break
            if not started or nm in skip or nm.endswith(("合计", "总计", "：")):
                continue
            v = it.get(col)
            if v in (None, 0):
                continue
            seg.append({"label": nm, "value": yi(v)})
        return seg

    skip = {"其中：应收利息", "应收股利"}
    seg_all = seg_items(bs, "流动资产：", "非流动资产：", skip, "期末余额") + seg_items(bs, "非流动资产：", "资产总计", skip, "期末余额")
    seg_all.sort(key=lambda x: -x["value"])
    assets = seg_all[:6]
    if len(seg_all) > 6:
        assets.append({"label": "其他", "value": round(sum(x["value"] for x in seg_all[6:]), 2)})
    total_assets = yi(find(bs, "资产总计")["期末余额"])
    assert abs(sum(x["value"] for x in assets) - total_assets) < 0.05, "资产构成合计与资产总计不闭合"
    liab_eq = [
        {"label": "流动负债", "value": yi(find(bs, "流动负债合计")["期末余额"])},
        {"label": "非流动负债", "value": yi(find(bs, "非流动负债合计")["期末余额"])},
        {"label": "归母所有者权益", "value": yi(find(bs, "归属于母公司所有者权益合计")["期末余额"])},
        {"label": "少数股东权益", "value": yi(find(bs, "少数股东权益")["期末余额"])},
    ]
    total_le = yi(find(bs, "负债和所有者权益总计")["期末余额"])
    assert abs(sum(x["value"] for x in liab_eq) - total_le) < 0.05, "负债与权益构成合计不闭合"

    # ---- 现金流三活动（本期 vs 上期）----
    cf_bars = {
        "labels": ["经营活动", "投资活动", "筹资活动"],
        "cur": [yi(find(cf, "经营活动产生的现金流量净额")["本期发生额"]),
                yi(find(cf, "投资活动产生的现金流量净额")["本期发生额"]),
                yi(find(cf, "筹资活动产生的现金流量净额")["本期发生额"])],
        "prev": [yi(find(cf, "经营活动产生的现金流量净额")["上期发生额"]),
                 yi(find(cf, "投资活动产生的现金流量净额")["上期发生额"]),
                 yi(find(cf, "筹资活动产生的现金流量净额")["上期发生额"])],
    }

    # ---- KPI 与指标 ----
    rev_c, rev_p = g2 = find(is_, "一、营业总收入")["本期发生额"], find(is_, "一、营业总收入")["上期发生额"]
    np_c, np_p = find(is_, "1.归属于母公司所有者的净利润")["本期发生额"], find(is_, "1.归属于母公司所有者的净利润")["上期发生额"]
    ocf_c, ocf_p = find(cf, "经营活动产生的现金流量净额")["本期发生额"], find(cf, "经营活动产生的现金流量净额")["上期发生额"]
    ta_c, ta_p = find(bs, "资产总计")["期末余额"], find(bs, "资产总计")["期初余额"]
    def yoy(c, p):
        return round((c - p) / abs(p) * 100, 2) if p else None
    cost = find(is_, "其中：营业成本")["本期发生额"]
    metrics = [
        {"name": "毛利率", "value": f"{(rev_c - cost) / rev_c * 100:.1f}%", "formula": "（营业收入−营业成本）÷营业收入"},
        {"name": "归母净利率", "value": f"{np_c / rev_c * 100:.1f}%", "formula": "归母净利润÷营业收入"},
        {"name": "资产负债率", "value": f"{find(bs, '负债合计')['期末余额'] / ta_c * 100:.1f}%", "formula": "负债合计÷资产总计（期末）"},
        {"name": "ROE（单季，未年化）", "value": f"{np_c / find(bs, '归属于母公司所有者权益合计')['期末余额'] * 100:.2f}%", "formula": "归母净利润÷期末归母净资产"},
        {"name": "盈利现金含量", "value": f"{ocf_c / g('五、净利润（净亏损以“－”号填列）'):.2f}x", "formula": "经营现金流净额÷净利润"},
        {"name": "收入同比", "value": f"+{yoy(rev_c, rev_p)}%", "formula": "本期÷上年同期−1"},
    ]
    kpis = [
        {"name": "营业收入", "cur": yi(rev_c), "prev": yi(rev_p), "yoy": yoy(rev_c, rev_p)},
        {"name": "归母净利润", "cur": yi(np_c), "prev": yi(np_p), "yoy": yoy(np_c, np_p)},
        {"name": "经营现金流净额", "cur": yi(ocf_c), "prev": yi(ocf_p), "yoy": yoy(ocf_c, ocf_p)},
        {"name": "总资产", "cur": yi(ta_c), "prev": yi(ta_p), "yoy": yoy(ta_c, ta_p)},
    ]

    # ---- 杜邦树（单季，未年化，期末口径）----
    eq_c = find(bs, "归属于母公司所有者权益合计")["期末余额"]
    roe, npm, ato, em = np_c / eq_c, np_c / rev_c, rev_c / ta_c, ta_c / eq_c
    assert abs(npm * ato * em - roe) < 1e-9, "杜邦三因子乘积与 ROE 不闭合"
    period_exp = sum(find(is_, n)["本期发生额"] for n in ["销售费用", "管理费用", "研发费用", "财务费用"])
    gm, pe = (rev_c - cost) / rev_c, period_exp / rev_c
    dupont = {
        "roe": roe * 100, "npm": npm * 100, "ato": ato, "em": em,
        "np_yi": yi(np_c), "rev_yi": yi(rev_c), "ta_yi": yi(ta_c), "eq_yi": yi(eq_c),
        "gross_margin": gm * 100, "period_exp_ratio": pe * 100,
        "tax_other": (gm - pe - npm) * 100,
    }
    assert abs(dupont["gross_margin"] - dupont["period_exp_ratio"] - dupont["tax_other"] - dupont["npm"]) < 0.01, "净利率下钻不闭合"

    # ---- 结构堆叠①：营业总成本构成（本期 vs 上期）----
    cost_names = ["其中：营业成本", "税金及附加", "销售费用", "管理费用", "研发费用", "财务费用"]
    def cost_row(col):
        segs = [{"label": n.replace("其中：", ""), "value": yi(find(is_, n)[col])} for n in cost_names]
        total = yi(find(is_, "二、营业总成本")[col])
        assert abs(sum(s["value"] for s in segs) - total) < 0.05, f"营业总成本构成不闭合（{col}）"
        return {"segs": segs, "total": total}
    cost_stack = [dict(label="本期 2026Q1", **cost_row("本期发生额")),
                  dict(label="上期 2025Q1", **cost_row("上期发生额"))]

    # ---- 结构堆叠②：资产构成（期末 vs 期初，同一 Top 项口径）----
    seg_prev = seg_items(bs, "流动资产：", "非流动资产：", skip, "期初余额") + seg_items(bs, "非流动资产：", "资产总计", skip, "期初余额")
    prev_map = {x["label"]: x["value"] for x in seg_prev}
    total_assets_prev = yi(find(bs, "资产总计")["期初余额"])
    top_labels = [x["label"] for x in assets]  # 与环形图同一 Top 项 + 「其他」
    cur_map = {x["label"]: x["value"] for x in assets}
    prev_vals = [round(prev_map.get(lb, 0), 2) for lb in top_labels]
    if "其他" in top_labels:
        prev_vals[-1] = round(total_assets_prev - sum(prev_vals[:-1]), 2)
    assert abs(sum(prev_vals) - total_assets_prev) < 0.05, "资产构成期初列不闭合"
    asset_stack = [
        {"label": "期末 2026-03-31", "segs": [{"label": lb, "value": cur_map[lb]} for lb in top_labels], "total": total_assets},
        {"label": "期初 2025-12-31", "segs": [{"label": lb, "value": v} for lb, v in zip(top_labels, prev_vals)], "total": total_assets_prev},
    ]

    # ---- 同业对比：顺丰 vs 京东物流（数字全部构建期从双方公告 PDF 现解析）----
    jdl_q1, jdl_fy = parse_jdl()
    sf_fy_rev = sum(quarterly["营业收入"])
    sf_fy_np = sum(quarterly["归属于上市公司股东的净利润"])
    nums14 = {int(c.replace(",", "")) for t in t14 for row in t for c in row if c and re.fullmatch(NUM, c.strip())}
    assert sf_fy_rev in nums14 and sf_fy_np in nums14, "分季度加总与年报主要会计数据不闭合"
    peer = {
        "names": ["顺丰控股", "京东物流"],
        "stds": ["CAS · A股季报未经审计", "IFRS · 港股未经审计"],
        "q1": {
            "rev": [yi(rev_c), yi(jdl_q1["revenue"])],
            "attr_np": [yi(np_c), yi(jdl_q1["attr_np"])],
            "gross_margin": [round((rev_c - cost) / rev_c * 100, 1), round(jdl_q1["gross"] / jdl_q1["revenue"] * 100, 1)],
            "attr_margin": [round(np_c / rev_c * 100, 1), round(jdl_q1["attr_np"] / jdl_q1["revenue"] * 100, 1)],
            "non_ifrs_attr": [None, yi(jdl_q1["non_ifrs_attr"])],
        },
        "fy": {
            "rev": [yi(sf_fy_rev), yi(jdl_fy["revenue"])],
            "attr_np": [yi(sf_fy_np), yi(jdl_fy["attr_np"])],
            "non_ifrs_attr": [None, yi(jdl_fy["non_ifrs_attr"])],
        },
    }

    data = {
        "company": "顺丰控股股份有限公司", "code": "002352.SZ / 6936.HK",
        "period": "2026 年第一季度（2026-01-01 至 2026-03-31）",
        "source": "巨潮资讯披露原文 PDF（SHA-256 前16位 72a07309388abcdc）",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "verify": "报表内勾稽 20/20 一致 · 跨文档比对 12/12 一致",
        "unit_note": "图表单位：人民币亿元（原始披露为千元，已换算）",
        "kpis": kpis, "metrics": metrics, "trend": trend,
        "waterfall": waterfall, "assets": assets, "liab_eq": liab_eq, "cf_bars": cf_bars,
        "dupont": dupont, "cost_stack": cost_stack, "asset_stack": asset_stack, "peer": peer,
        "statements": st,
    }
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    OUT.write_text(html, encoding="utf-8")
    print(f"written -> {OUT} ({len(html)} bytes)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>P5 反向解析 · 顺丰控股 2026Q1 四表可视化分析</title>
<style>
:root{--bg:#0b1020;--card:#141b31;--line:#24304f;--txt:#e8ecf6;--sub:#93a0bd;--acc:#4c8dff;--up:#e5534b;--down:#3fb68b;--gold:#e8b34b;--teal:#3fb68b;--purple:#9d7bea}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:28px;max-width:1280px;margin:0 auto}
h1{font-size:22px}h2{font-size:16px;margin:34px 0 14px;padding-left:10px;border-left:3px solid var(--acc)}
.meta{color:var(--sub);font-size:12px;margin-top:6px;line-height:1.7}
.badge{display:inline-block;background:#16324f;color:#7db4ff;border:1px solid #2a4a73;border-radius:20px;padding:3px 12px;font-size:12px;margin:10px 6px 0 0}
.badge.ok{background:#12362c;color:#5ed3a5;border-color:#1f5c46}
.grid{display:grid;gap:14px}
.g4{grid-template-columns:repeat(4,1fr)}.g3{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.kpi .v{font-size:26px;font-weight:700;margin:4px 0}.kpi .u{font-size:12px;color:var(--sub)}
.yoy{font-size:12px;font-weight:600}.yoy.up{color:var(--up)}.yoy.down{color:var(--down)}
.metric .v{font-size:20px;font-weight:700;color:var(--gold)}.metric .f{font-size:11px;color:var(--sub);margin-top:6px}
.lbl{font-size:13px;color:var(--sub)}
svg{width:100%;height:auto;display:block}
.legend{display:flex;gap:16px;font-size:12px;color:var(--sub);margin-top:8px;flex-wrap:wrap}
.dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-top:10px}
summary{cursor:pointer;font-weight:600;font-size:14px}
table{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px}
th,td{padding:5px 8px;text-align:right;border-bottom:1px solid #1c2540}
th:first-child,td:first-child{text-align:left}
th{color:var(--sub);font-weight:500}
tr.sec td{color:var(--gold);font-weight:600}
tr.tot td{font-weight:700;background:#182139}
.note{font-size:11px;color:var(--sub);margin-top:8px}
@media(max-width:900px){.g4{grid-template-columns:repeat(2,1fr)}.g3,.g2{grid-template-columns:1fr}}
</style>
</head>
<body>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const C = {acc:'#4c8dff',up:'#e5534b',down:'#3fb68b',gold:'#e8b34b',teal:'#3fb68b',purple:'#9d7bea',sub:'#93a0bd',line:'#24304f',txt:'#e8ecf6'};
const PAL = ['#4c8dff','#3fb68b','#e8b34b','#9d7bea','#e5534b','#54c8e8','#8a97b8','#d17db8'];
const fmt = v => v==null?'—':v.toLocaleString('zh-CN',{maximumFractionDigits:2});

function axis(maxV, minV, w, h, pad){
  const span = maxV - minV || 1;
  const y = v => pad.t + (maxV - v)/span*(h-pad.t-pad.b);
  let s = '';
  const steps = 4;
  for(let i=0;i<=steps;i++){
    const v = minV + span*i/steps, yy = y(v);
    s += `<line x1="${pad.l}" y1="${yy}" x2="${w-pad.r}" y2="${yy}" stroke="${C.line}" stroke-width="1"/>`;
    s += `<text x="${pad.l-8}" y="${yy+4}" fill="${C.sub}" font-size="10" text-anchor="end">${fmt(Math.round(v*10)/10)}</text>`;
  }
  return {s, y};
}

function trendChart(t){
  const w=760,h=300,pad={l:52,r:16,t:16,b:34};
  const vals=[...t.revenue,...t.net_profit,...t.ocf];
  const maxV=Math.max(...vals)*1.1, minV=Math.min(0,...vals);
  const {s,y}=axis(maxV,minV,w,h,pad);
  const bw=(w-pad.l-pad.r)/t.labels.length;
  let out=`<svg viewBox="0 0 ${w} ${h}">`+s;
  const pts=[];
  t.labels.forEach((lb,i)=>{
    const x=pad.l+i*bw+bw/2;
    out+=`<rect x="${x-14}" y="${y(t.revenue[i])}" width="28" height="${y(0)-y(t.revenue[i])}" rx="3" fill="${C.acc}" opacity=".85"/>`;
    out+=`<text x="${x}" y="${y(t.revenue[i])-6}" fill="${C.txt}" font-size="10" text-anchor="middle">${fmt(t.revenue[i])}</text>`;
    out+=`<text x="${x}" y="${h-12}" fill="${C.sub}" font-size="11" text-anchor="middle">${lb}</text>`;
    pts.push([x,y(t.net_profit[i])]);
  });
  out+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${C.gold}" stroke-width="2.5"/>`;
  pts.forEach((p,i)=>{out+=`<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${C.gold}"/>`;
    out+=`<text x="${p[0]}" y="${p[1]-9}" fill="${C.gold}" font-size="10" text-anchor="middle">${fmt(t.net_profit[i])}</text>`;});
  return out+'</svg>';
}

function waterfallChart(wf){
  const w=760,h=320,pad={l:52,r:16,t:16,b:64};
  let run=0; const bars=wf.map(d=>{
    if(d.type==='total'){const b={...d,from:0,to:d.value};run=d.value;return b;}
    const from=run; run=Math.round((run+d.value)*100)/100; return {...d,from,to:run};
  });
  const maxV=Math.max(...bars.map(b=>Math.max(b.from,b.to)))*1.08, minV=0;
  const {s,y}=axis(maxV,minV,w,h,pad);
  const bw=(w-pad.l-pad.r)/bars.length;
  let out=`<svg viewBox="0 0 ${w} ${h}">`+s, prevX=null,prevY=null;
  bars.forEach((b,i)=>{
    const x=pad.l+i*bw+bw*0.18, wd=bw*0.64;
    const y1=y(Math.max(b.from,b.to)), y2=y(Math.min(b.from,b.to));
    const col=b.type==='total'?C.acc:(b.value>=0?C.down:C.up);
    if(prevX!==null) out+=`<line x1="${prevX}" y1="${prevY}" x2="${x}" y2="${prevY}" stroke="${C.sub}" stroke-dasharray="3,3" stroke-width="1"/>`;
    out+=`<rect x="${x}" y="${y1}" width="${wd}" height="${Math.max(y2-y1,2)}" rx="3" fill="${col}" opacity=".9"/>`;
    out+=`<text x="${x+wd/2}" y="${y1-6}" fill="${C.txt}" font-size="10" text-anchor="middle">${b.value>0&&b.type==='delta'?'+':''}${fmt(b.value)}</text>`;
    out+=`<text x="${x+wd/2}" y="${h-46}" fill="${C.sub}" font-size="10" text-anchor="middle" transform="rotate(-28 ${x+wd/2} ${h-46})">${b.label}</text>`;
    prevX=x+wd; prevY=y(b.to);
  });
  return out+'</svg>';
}

function donut(items, title){
  const total=items.reduce((a,b)=>a+b.value,0);
  const cx=150,cy=130,r=95,ir=55;
  let ang=-Math.PI/2, arcs='';
  items.forEach((d,i)=>{
    const a2=ang+d.value/total*Math.PI*2;
    const large=(a2-ang)>Math.PI?1:0;
    const p=(a,rr)=>[cx+rr*Math.cos(a),cy+rr*Math.sin(a)];
    const [x1,y1]=p(ang,r),[x2,y2]=p(a2,r),[x3,y3]=p(a2,ir),[x4,y4]=p(ang,ir);
    arcs+=`<path d="M${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} L${x3} ${y3} A${ir} ${ir} 0 ${large} 0 ${x4} ${y4} Z" fill="${PAL[i%PAL.length]}" opacity=".92"/>`;
    ang=a2;
  });
  let legend=`<div class="legend" style="flex-direction:column;gap:6px;align-items:flex-start">`;
  items.forEach((d,i)=>{legend+=`<span><span class="dot" style="background:${PAL[i%PAL.length]}"></span>${d.label} · ${fmt(d.value)} 亿（${(d.value/total*100).toFixed(1)}%）</span>`;});
  legend+='</div>';
  return `<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><svg viewBox="0 0 300 260" style="max-width:300px">${arcs}<text x="${cx}" y="${cy-4}" fill="${C.sub}" font-size="11" text-anchor="middle">${title}</text><text x="${cx}" y="${cy+16}" fill="${C.txt}" font-size="16" font-weight="700" text-anchor="middle">${fmt(total)} 亿</text></svg>${legend}</div>`;
}

function cfBars(cf){
  const w=760,h=280,pad={l:52,r:16,t:16,b:34};
  const vals=[...cf.cur,...cf.prev];
  const maxV=Math.max(...vals,0)*1.15, minV=Math.min(...vals,0)*1.15;
  const {s,y}=axis(maxV,minV,w,h,pad);
  const bw=(w-pad.l-pad.r)/cf.labels.length;
  let out=`<svg viewBox="0 0 ${w} ${h}">`+s;
  out+=`<line x1="${pad.l}" y1="${y(0)}" x2="${w-pad.r}" y2="${y(0)}" stroke="${C.sub}" stroke-width="1.2"/>`;
  cf.labels.forEach((lb,i)=>{
    const gx=pad.l+i*bw+bw/2;
    [['cur',C.acc,'本期',-26],['prev','#5a6a90','上年同期',6]].forEach(([key,col,nm,off])=>{
      const v=cf[key][i];
      const y1=y(Math.max(0,v)), y2=y(Math.min(0,v));
      out+=`<rect x="${gx+off-10}" y="${y1}" width="20" height="${Math.max(y2-y1,2)}" rx="3" fill="${col}"/>`;
      out+=`<text x="${gx+off}" y="${v>=0?y1-6:y2+14}" fill="${C.txt}" font-size="10" text-anchor="middle">${v>0?'+':''}${fmt(v)}</text>`;
    });
    out+=`<text x="${gx}" y="${h-12}" fill="${C.sub}" font-size="11" text-anchor="middle">${lb}</text>`;
  });
  return out+'</svg>';
}

function dupontTree(dp){
  const W=760,H=440;
  const box=(x,y,w,h,title,value,sub,col)=>
    `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" fill="#18213a" stroke="${col}" stroke-width="1.4"/>`+
    `<text x="${x+w/2}" y="${y+18}" fill="${C.sub}" font-size="11" text-anchor="middle">${title}</text>`+
    `<text x="${x+w/2}" y="${y+39}" fill="${col}" font-size="17" font-weight="700" text-anchor="middle">${value}</text>`+
    (sub?`<text x="${x+w/2}" y="${y+53}" fill="${C.sub}" font-size="9.5" text-anchor="middle">${sub}</text>`:'');
  const lk=(x1,y1,x2,y2)=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${C.line}" stroke-width="1.6"/>`;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  // 根 → 三因子
  s+=lk(380,76,150,128)+lk(380,76,380,128)+lk(380,76,610,128);
  // 因子 → 叶子（收入/总资产为共享叶子）
  s+=lk(150,192,90,248)+lk(150,192,260,248);   // 净利率 ← 归母净利润、营业收入
  s+=lk(380,192,260,248)+lk(380,192,430,248);  // 周转率 ← 营业收入、资产总计
  s+=lk(610,192,430,248)+lk(610,192,600,248);  // 权益乘数 ← 资产总计、归母净资产
  // 净利率 → 下钻层
  s+=lk(150,192,150,310);
  s+=box(280,14,200,62,'ROE（单季，未年化）',dp.roe.toFixed(2)+'%','归母净利润 ÷ 期末归母净资产',C.gold);
  s+=box(65,130,170,62,'归母净利率',dp.npm.toFixed(2)+'%','归母净利润 ÷ 营业收入',C.acc);
  s+=box(295,130,170,62,'总资产周转率',dp.ato.toFixed(2)+' 次','营业收入 ÷ 资产总计（期末口径）',C.acc);
  s+=box(525,130,170,62,'权益乘数',dp.em.toFixed(2),'资产总计 ÷ 归母净资产',C.acc);
  s+=`<text x="252" y="168" fill="${C.sub}" font-size="16" text-anchor="middle">×</text><text x="482" y="168" fill="${C.sub}" font-size="16" text-anchor="middle">×</text>`;
  s+=box(15,250,150,58,'归母净利润',fmt(dp.np_yi)+' 亿','',C.teal);
  s+=box(185,250,150,58,'营业收入',fmt(dp.rev_yi)+' 亿','',C.teal);
  s+=box(355,250,150,58,'资产总计（期末）',fmt(dp.ta_yi)+' 亿','',C.teal);
  s+=box(525,250,150,58,'归母净资产（期末）',fmt(dp.eq_yi)+' 亿','',C.teal);
  // 下钻层：净利率 = 毛利率 − 期间费用率 − 税金及其他
  s+=`<text x="15" y="332" fill="${C.sub}" font-size="11">归母净利率下钻（百分点，pp）：</text>`;
  s+=box(15,344,200,62,'毛利率',dp.gross_margin.toFixed(1)+'%','（营业收入−营业成本）÷营业收入',C.teal);
  s+=`<text x="228" y="382" fill="${C.up}" font-size="18" font-weight="700" text-anchor="middle">−</text>`;
  s+=box(242,344,200,62,'期间费用率',dp.period_exp_ratio.toFixed(1)+'%','销售+管理+研发+财务 ÷ 营业收入',C.up);
  s+=`<text x="455" y="382" fill="${C.up}" font-size="18" font-weight="700" text-anchor="middle">−</text>`;
  s+=box(469,344,220,62,'税金·其他损益·所得税等',dp.tax_other.toFixed(1)+' pp','残差项：税金及附加/其他收益/减值/营业外/所得税',C.purple);
  return s+'</svg>';
}

function stackBars(rows){
  const W=760,rowH=46,H=10+rows.length*rowH+4,L=150,R=70;
  const bw=W-L-R;
  let out=`<svg viewBox="0 0 ${W} ${H}" class="stackbar">`;
  rows.forEach((r,ri)=>{
    const y=8+ri*rowH;
    out+=`<text x="0" y="${y+20}" fill="${C.sub}" font-size="12">${r.label}</text>`;
    let x=L;
    r.segs.forEach((sg,i)=>{
      const w=Math.max(sg.value/r.total*bw,0.4);
      out+=`<rect x="${x}" y="${y}" width="${w}" height="30" fill="${PAL[i%PAL.length]}" opacity=".92"/>`;
      const pct=sg.value/r.total*100;
      if(pct>6.5) out+=`<text x="${x+w/2}" y="${y+20}" fill="#0b1020" font-size="11" font-weight="600" text-anchor="middle">${pct.toFixed(1)}%</text>`;
      x+=w;
    });
    out+=`<text x="${W-2}" y="${y+20}" fill="${C.txt}" font-size="11" text-anchor="end">${fmt(r.total)} 亿</text>`;
  });
  out+='</svg>';
  let legend='<div class="legend">';
  rows[0].segs.forEach((sg,i)=>{
    const vals=rows.map(r=>fmt(r.segs[i].value)).join(' / ');
    legend+=`<span><span class="dot" style="background:${PAL[i%PAL.length]}"></span>${sg.label}（${vals} 亿）</span>`;
  });
  return out+legend+'</div>';
}

function peerBars(peer){
  const groups=[
    {t1:'2026Q1',t2:'营业收入（亿）',vals:peer.q1.rev},
    {t1:'2026Q1',t2:'归母利润（亿）',vals:peer.q1.attr_np},
    {t1:'FY2025',t2:'营业收入（亿）',vals:peer.fy.rev},
    {t1:'FY2025',t2:'归母利润（亿）',vals:peer.fy.attr_np},
  ];
  const w=760,h=300,pad={l:52,r:16,t:16,b:52};
  const maxV=Math.max(...groups.flatMap(g=>g.vals))*1.12;
  const {s,y}=axis(maxV,0,w,h,pad);
  const bw=(w-pad.l-pad.r)/groups.length;
  let out=`<svg viewBox="0 0 ${w} ${h}">`+s;
  groups.forEach((g,i)=>{
    const gx=pad.l+i*bw+bw/2;
    g.vals.forEach((v,j)=>{
      out+=`<rect x="${gx+(j===0?-33:3)}" y="${y(v)}" width="30" height="${Math.max(y(0)-y(v),2)}" rx="3" fill="${j===0?C.acc:C.teal}" opacity=".9"/>`;
      out+=`<text x="${gx+(j===0?-18:18)}" y="${y(v)-6}" fill="${C.txt}" font-size="10" text-anchor="middle">${fmt(v)}</text>`;
    });
    out+=`<text x="${gx}" y="${h-30}" fill="${C.txt}" font-size="11" font-weight="600" text-anchor="middle">${g.t1}</text>`;
    out+=`<text x="${gx}" y="${h-14}" fill="${C.sub}" font-size="11" text-anchor="middle">${g.t2}</text>`;
  });
  return out+'</svg>';
}

function stmtTable(items, c1, c2){
  let rows='';
  items.forEach(it=>{
    const isSec=/：$/.test(it.item)||/^[一二三四五六七八]、.*：$/.test(it.item);
    const isTot=/合计|总计|净额|净利润|营业利润|利润总额|小计/.test(it.item);
    const cls=isSec?'sec':(isTot?'tot':'');
    const f=v=>v==null?'':v.toLocaleString('zh-CN');
    rows+=`<tr class="${cls}"><td>${it.item}</td><td>${f(it[c1])}</td><td>${f(it[c2])}</td></tr>`;
  });
  return `<table><tr><th>项目</th><th>${c1}</th><th>${c2}</th></tr>${rows}</table>`;
}

const kpiHtml = D.kpis.map(k=>{
  const dir=k.yoy==null?'':(k.yoy>=0?'up':'down');
  const arrow=k.yoy==null?'':(k.yoy>=0?'▲':'▼');
  return `<div class="card kpi"><div class="lbl">${k.name}</div><div class="v">${fmt(k.cur)}<span class="u"> 亿元</span></div><div class="yoy ${dir}">${arrow} ${k.yoy==null?'—':Math.abs(k.yoy)+'%'} <span style="color:${C.sub};font-weight:400">同比/较期初</span></div></div>`;
}).join('');
const metricHtml = D.metrics.map(m=>`<div class="card metric"><div class="lbl">${m.name}</div><div class="v">${m.value}</div><div class="f">口径：${m.formula}</div></div>`).join('');

const peerTbl = `<table><tr><th>指标</th><th>${D.peer.names[0]}</th><th>${D.peer.names[1]}</th><th>口径说明</th></tr>
<tr><td>2026Q1 毛利率</td><td>${D.peer.q1.gross_margin[0].toFixed(1)}%</td><td>${D.peer.q1.gross_margin[1].toFixed(1)}%</td><td>毛利 ÷ 收入</td></tr>
<tr><td>2026Q1 归母净利率</td><td>${D.peer.q1.attr_margin[0].toFixed(1)}%</td><td>${D.peer.q1.attr_margin[1].toFixed(1)}%</td><td>归母利润 ÷ 收入</td></tr>
<tr><td>2026Q1 Non-IFRS 归母利润（亿）</td><td>披露缺失</td><td>${fmt(D.peer.q1.non_ifrs_attr[1])}</td><td>顺丰无对应披露 → §10.2「披露缺失」</td></tr>
<tr><td>FY2025 Non-IFRS 归母利润（亿）</td><td>披露缺失</td><td>${fmt(D.peer.fy.non_ifrs_attr[1])}</td><td>同上；京东物流为 IFRS 口径</td></tr></table>`;

document.body.innerHTML = `
<h1>P5 反向解析验证 · ${D.company}（${D.code}）</h1>
<div class="meta">报告期：${D.period} ｜ 数据来源：${D.source} ｜ 生成时间：${D.generated_at}<br>${D.unit_note} ｜ 原始披露单位：人民币千元</div>
<div><span class="badge ok">✓ ${D.verify}</span><span class="badge">P5 管道自动抽取 · 未经手工调整</span></div>

<h2>① 核心指标（KPI）</h2>
<div class="grid g4">${kpiHtml}</div>

<h2>② 五个季度趋势：收入（柱）与归母净利润（线，亿元）</h2>
<div class="card">${trendChart(D.trend)}<div class="legend"><span><span class="dot" style="background:${C.acc}"></span>营业收入</span><span><span class="dot" style="background:${C.gold}"></span>归母净利润</span></div><div class="note">2025Q1–Q4 取自 FY2025 年报「分季度主要财务指标」，2026Q1 取自 2026 一季报；均为管道自动解析值。</div></div>

<h2>③ 利润形成瀑布（本期，亿元）：从收入到净利润</h2>
<div class="card">${waterfallChart(D.waterfall)}<div class="note">瀑布链在生成期已做闭合校验（各增减项加总 = 下一小计），链断裂则构建直接失败，不会产出错图。</div></div>

<h2>④ 财务分析指标（由抽取值按指标库口径计算）</h2>
<div class="grid g3">${metricHtml}</div>

<h2>⑤ 杜邦分析树（2026Q1 单季，未年化，期末口径）</h2>
<div class="card" id="sec-dupont">${dupontTree(D.dupont)}<div class="note">三因子乘积 = ROE 已在生成期断言闭合；净利率下钻三项（毛利率 − 期间费用率 − 税金及其他）同样闭合校验。周转率采用期末口径、单季未年化，与一季报正文披露的「加权平均净资产收益率 2.52%」口径不同，不可直接互比。</div></div>

<h2>⑥ 结构堆叠：营业总成本与资产构成（亿元，占总计 100%）</h2>
<div class="grid g2">
<div class="card"><div class="lbl" style="margin-bottom:8px">营业总成本构成：本期 vs 上期</div>${stackBars(D.cost_stack)}<div class="note">各分项加总 = 营业总成本，两列均在生成期闭合校验；「利息费用/利息收入」为财务费用的其中项，不重复计入。</div></div>
<div class="card"><div class="lbl" style="margin-bottom:8px">资产构成：期末 vs 期初（同一 Top 项口径）</div>${stackBars(D.asset_stack)}<div class="note">与 ⑧ 资产环形同一 Top 项口径，两列分别闭合到资产总计。</div></div>
</div>

<h2>⑦ 同业对比：顺丰控股 vs 京东物流</h2>
<div class="card" id="sec-peer">${peerBars(D.peer)}
<div class="legend"><span><span class="dot" style="background:${C.acc}"></span>${D.peer.names[0]}（${D.peer.stds[0]}）</span><span><span class="dot" style="background:${C.teal}"></span>${D.peer.names[1]}（${D.peer.stds[1]}）</span></div>
${peerTbl}
<div class="note">双方数字均于构建期从各自公告 PDF 现解析：顺丰取一季报与 FY2025 年报（全年 = 分季度加总，已与年报「主要会计数据」表闭合校验）；京东物流取 2026Q1 财务资料 p3/p7 与 FY2025 年度业绩公告 p2/p20/p25。京东物流利润口径为「本公司所有者应占」，与顺丰「归母净利润」可比但准则不同（IFRS vs CAS），属 §10.2「口径差异」层级，解读时注意。</div></div>

<h2>⑧ 资产结构与资本结构（期末，亿元）</h2>
<div class="grid g2">
<div class="card"><div class="lbl" style="margin-bottom:8px">资产构成（Top 项 + 其他）</div>${donut(D.assets,'资产总计')}</div>
<div class="card"><div class="lbl" style="margin-bottom:8px">负债与权益构成</div>${donut(D.liab_eq,'负债和权益')}</div>
</div>

<h2>⑨ 现金流三活动：本期 vs 上年同期（亿元）</h2>
<div class="card">${cfBars(D.cf_bars)}<div class="legend"><span><span class="dot" style="background:${C.acc}"></span>本期（2026Q1）</span><span><span class="dot" style="background:#5a6a90"></span>上年同期（2025Q1）</span></div></div>

<h2>⑩ 四表原文（抽取值全量，单位：人民币千元）</h2>
<details><summary>合并资产负债表（${D.statements['合并资产负债表'].length} 行）</summary>${stmtTable(D.statements['合并资产负债表'],'期末余额','期初余额')}</details>
<details><summary>合并利润表（${D.statements['合并利润表'].length} 行）</summary>${stmtTable(D.statements['合并利润表'],'本期发生额','上期发生额')}</details>
<details><summary>合并现金流量表（${D.statements['合并现金流量表'].length} 行）</summary>${stmtTable(D.statements['合并现金流量表'],'本期发生额','上期发生额')}</details>
<details><summary>所有者权益变动表与附注</summary><div class="note" style="padding:8px 0">A 股季报不披露所有者权益变动表与附注，属于「披露缺失」层级（规格 §10.2 差异分级）；将在顺丰 FY2025 年报样本中补全——年报含完整四表一注。</div></details>
<div class="note" style="margin-top:18px">本页由 scripts/p5_build_report_view.py 自 P5 抽取产物机械生成，数字零手工调整；生成链路：原始 PDF → 行项目抽取 → 勾稽校验（20/20）→ 跨文档比对（12/12）→ 本视图。</div>
`;
</script>
</body>
</html>
"""


TENCENT_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>P5 反向解析 · 腾讯控股 2Q2026 IFRS→Non-IFRS 调节分析</title>
<style>
:root{--bg:#0b1020;--card:#141b31;--line:#24304f;--txt:#e8ecf6;--sub:#93a0bd;--acc:#4c8dff;--up:#e5534b;--down:#3fb68b;--gold:#e8b34b;--teal:#3fb68b;--purple:#9d7bea}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;padding:28px;max-width:1280px;margin:0 auto}
h1{font-size:22px}h2{font-size:16px;margin:34px 0 14px;padding-left:10px;border-left:3px solid var(--acc)}
.meta{color:var(--sub);font-size:12px;margin-top:6px;line-height:1.7}
.badge{display:inline-block;background:#16324f;color:#7db4ff;border:1px solid #2a4a73;border-radius:20px;padding:3px 12px;font-size:12px;margin:10px 6px 0 0}
.badge.ok{background:#12362c;color:#5ed3a5;border-color:#1f5c46}
.grid{display:grid;gap:14px}
.g4{grid-template-columns:repeat(4,1fr)}.g3{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:repeat(2,1fr)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.kpi .v{font-size:26px;font-weight:700;margin:4px 0}.kpi .u{font-size:12px;color:var(--sub)}
.yoy{font-size:12px;font-weight:600}.yoy.up{color:var(--up)}.yoy.down{color:var(--down)}
.metric .v{font-size:20px;font-weight:700;color:var(--gold)}.metric .f{font-size:11px;color:var(--sub);margin-top:6px}
.lbl{font-size:13px;color:var(--sub)}
svg{width:100%;height:auto;display:block}
.legend{display:flex;gap:16px;font-size:12px;color:var(--sub);margin-top:8px;flex-wrap:wrap}
.dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-top:10px}
summary{cursor:pointer;font-weight:600;font-size:14px}
table{width:100%;border-collapse:collapse;font-size:12px;margin-top:10px}
th,td{padding:5px 8px;text-align:right;border-bottom:1px solid #1c2540}
th:first-child,td:first-child{text-align:left}
th{color:var(--sub);font-weight:500}
tr.tot td{font-weight:700;background:#182139}
.note{font-size:11px;color:var(--sub);margin-top:8px}
@media(max-width:900px){.g4{grid-template-columns:repeat(2,1fr)}.g3,.g2{grid-template-columns:1fr}}
</style>
</head>
<body>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const C = {acc:'#4c8dff',up:'#e5534b',down:'#3fb68b',gold:'#e8b34b',teal:'#3fb68b',purple:'#9d7bea',sub:'#93a0bd',line:'#24304f',txt:'#e8ecf6'};
const PAL = ['#4c8dff','#3fb68b','#e8b34b','#9d7bea','#e5534b','#54c8e8','#8a97b8','#d17db8'];
const fmt = v => v==null?'—':v.toLocaleString('zh-CN',{maximumFractionDigits:2});

function axis(maxV, minV, w, h, pad){
  const span = maxV - minV || 1;
  const y = v => pad.t + (maxV - v)/span*(h-pad.t-pad.b);
  let s = '';
  for(let i=0;i<=4;i++){
    const v = minV + (maxV-minV)*i/4, yy = y(v);
    s += `<line x1="${pad.l}" y1="${yy}" x2="${w-pad.r}" y2="${yy}" stroke="${C.line}" stroke-width="1"/>`;
    s += `<text x="${pad.l-8}" y="${yy+4}" fill="${C.sub}" font-size="10" text-anchor="end">${fmt(Math.round(v*10)/10)}</text>`;
  }
  return {s, y};
}

function trend3Chart(t){
  const w=760,h=300,pad={l:56,r:16,t:16,b:34};
  const maxV=Math.max(...t.revenue,...t.ifrs_np,...t.nifrs_np)*1.12;
  const {s,y}=axis(maxV,0,w,h,pad);
  const bw=(w-pad.l-pad.r)/t.labels.length;
  let out=`<svg viewBox="0 0 ${w} ${h}">`+s;
  const series=[['revenue',C.acc,'营业收入',-56],['ifrs_np',C.gold,'IFRS 归母盈利',-14],['nifrs_np',C.teal,'Non-IFRS 归母盈利',28]];
  t.labels.forEach((lb,i)=>{
    const gx=pad.l+i*bw+bw/2;
    series.forEach(([key,col,nm,off])=>{
      const v=t[key][i];
      out+=`<rect x="${gx+off-13}" y="${y(v)}" width="26" height="${y(0)-y(v)}" rx="3" fill="${col}" opacity=".88"/>`;
      out+=`<text x="${gx+off}" y="${y(v)-6}" fill="${C.txt}" font-size="10" text-anchor="middle">${fmt(v)}</text>`;
    });
    out+=`<text x="${gx}" y="${h-12}" fill="${C.sub}" font-size="12" text-anchor="middle">${lb}</text>`;
  });
  return out+'</svg>';
}

function waterfallChart(wf){
  const w=760,h=340,pad={l:56,r:16,t:16,b:78};
  let run=0; const bars=wf.map(d=>{
    if(d.type==='total'){const b={...d,from:0,to:d.value};run=d.value;return b;}
    const from=run; run=Math.round((run+d.value)*100)/100; return {...d,from,to:run};
  });
  const maxV=Math.max(...bars.map(b=>Math.max(b.from,b.to)))*1.08, minV=0;
  const {s,y}=axis(maxV,minV,w,h,pad);
  const bw=(w-pad.l-pad.r)/bars.length;
  let out=`<svg viewBox="0 0 ${w} ${h}">`+s, prevX=null,prevY=null;
  bars.forEach((b,i)=>{
    const x=pad.l+i*bw+bw*0.14, wd=bw*0.72;
    const y1=y(Math.max(b.from,b.to)), y2=y(Math.min(b.from,b.to));
    const col=b.type==='total'?(i===0?C.acc:C.gold):(b.value>=0?C.down:C.up);
    if(prevX!==null) out+=`<line x1="${prevX}" y1="${prevY}" x2="${x}" y2="${prevY}" stroke="${C.sub}" stroke-dasharray="3,3" stroke-width="1"/>`;
    out+=`<rect x="${x}" y="${y1}" width="${wd}" height="${Math.max(y2-y1,2)}" rx="3" fill="${col}" opacity=".9"/>`;
    out+=`<text x="${x+wd/2}" y="${y1-6}" fill="${C.txt}" font-size="10" text-anchor="middle">${b.value>0&&b.type==='delta'?'+':''}${fmt(b.value)}</text>`;
    out+=`<text x="${x+wd/2}" y="${h-58}" fill="${C.sub}" font-size="10" text-anchor="middle" transform="rotate(-30 ${x+wd/2} ${h-58})">${b.label}</text>`;
    prevX=x+wd; prevY=y(b.to);
  });
  return out+'</svg>';
}

function donut(items, title){
  const total=items.reduce((a,b)=>a+b.value,0);
  const cx=150,cy=130,r=95,ir=55;
  let ang=-Math.PI/2, arcs='';
  items.forEach((d,i)=>{
    const a2=ang+d.value/total*Math.PI*2;
    const large=(a2-ang)>Math.PI?1:0;
    const p=(a,rr)=>[cx+rr*Math.cos(a),cy+rr*Math.sin(a)];
    const [x1,y1]=p(ang,r),[x2,y2]=p(a2,r),[x3,y3]=p(a2,ir),[x4,y4]=p(ang,ir);
    arcs+=`<path d="M${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2} L${x3} ${y3} A${ir} ${ir} 0 ${large} 0 ${x4} ${y4} Z" fill="${PAL[i%PAL.length]}" opacity=".92"/>`;
    ang=a2;
  });
  let legend=`<div class="legend" style="flex-direction:column;gap:6px;align-items:flex-start">`;
  items.forEach((d,i)=>{legend+=`<span><span class="dot" style="background:${PAL[i%PAL.length]}"></span>${d.label} · ${fmt(d.value)} 亿（${(d.value/total*100).toFixed(1)}%）</span>`;});
  legend+='</div>';
  return `<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><svg viewBox="0 0 300 260" style="max-width:300px">${arcs}<text x="${cx}" y="${cy-4}" fill="${C.sub}" font-size="11" text-anchor="middle">${title}</text><text x="${cx}" y="${cy+16}" fill="${C.txt}" font-size="16" font-weight="700" text-anchor="middle">${fmt(total)} 亿</text></svg>${legend}</div>`;
}

const kpiHtml = D.kpis.map(k=>{
  const dir=k.yoy>=0?'up':'down';
  return `<div class="card kpi"><div class="lbl">${k.name}</div><div class="v">${fmt(k.cur)}<span class="u"> 亿元</span></div><div class="yoy ${dir}">${k.yoy>=0?'▲':'▼'} ${Math.abs(k.yoy)}% <span style="color:${C.sub};font-weight:400">同比</span></div></div>`;
}).join('');
const metricHtml = D.metrics.map(m=>`<div class="card metric"><div class="lbl">${m.name}</div><div class="v">${m.value}</div><div class="f">口径：${m.formula}</div></div>`).join('');

const f3=v=>(v<0?'(':'')+Math.abs(v).toLocaleString('zh-CN')+(v<0?')':'');
const totRows=new Set(['收入','毛利','经营盈利','除税前盈利','期内盈利','非国际财务报告准则经营盈利','本公司权益持有人应占盈利']);
const stmtHtml = `<table><tr><th>项目</th><th>2Q2026</th><th>2Q2025</th><th>1Q2026</th></tr>`+
  D.stmt_rows.map(r=>`<tr class="${totRows.has(r.label)?'tot':''}"><td>${r.label}</td>${r.vals.map(v=>`<td>${f3(v)}</td>`).join('')}</tr>`).join('')+`</table>`;
const reconTbl = `<table><tr><th>调整项（公告附注 a–g）</th><th>金额（亿元）</th><th>性质说明</th></tr>`+
  D.adj_notes.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td style="text-align:left;color:${C.sub}">${r[2]}</td></tr>`).join('')+
  `<tr class="tot"><td>合计调整</td><td>${(D.recon[D.recon.length-1].value-D.recon[0].value).toFixed(2)}</td><td style="text-align:left;color:${C.sub}">${D.recon[0].label} ${D.recon[0].value} → ${D.recon[D.recon.length-1].label} ${D.recon[D.recon.length-1].value}（亿元，链已闭合校验）</td></tr></table>`;

document.body.innerHTML = `
<h1>P5 反向解析验证 · ${D.company}（${D.code}）</h1>
<div class="meta">报告期：${D.period} ｜ 数据来源：${D.source} ｜ 生成时间：${D.generated_at}<br>${D.unit_note} ｜ 原始披露单位：人民币百万元</div>
<div><span class="badge ok">✓ IFRS→Non-IFRS 调节链闭合校验通过</span><span class="badge ok">✓ 调节表与收益表交叉勾稽一致</span><span class="badge">P5 管道自动解析 · 未经手工调整</span></div>

<h2>① 核心指标（KPI）</h2>
<div class="grid g4">${kpiHtml}</div>

<h2>② 三期对比：2Q2025 / 1Q2026 / 2Q2026（亿元）</h2>
<div class="card">${trend3Chart(D.trend3)}<div class="legend"><span><span class="dot" style="background:${C.acc}"></span>营业收入</span><span><span class="dot" style="background:${C.gold}"></span>IFRS 归母盈利</span><span><span class="dot" style="background:${C.teal}"></span>Non-IFRS 归母盈利</span></div></div>

<h2>③ IFRS → Non-IFRS 调节瀑布（2Q2026 归母盈利口径，亿元）</h2>
<div class="card" id="sec-recon">${waterfallChart(D.recon)}<div class="note">调节链在生成期断言闭合：IFRS 归母 + 七项调整 = Non-IFRS 归母，且与收益表 IFRS/Non-IFRS 归母行交叉勾稽一致，任一环节断裂则构建失败。负向调整（减值拨回、所得税影响）会拉低 Non-IFRS 值，方向已如实绘制。</div>${reconTbl}</div>

<h2>④ 盈利率指标（按公告披露口径复核）</h2>
<div class="grid g3">${metricHtml}</div>

<h2>⑤ 收入结构（2Q2026，亿元）</h2>
<div class="card">${donut(D.segments,'营业收入')}<div class="note">四个分部加总 = 营业收入，已在生成期闭合校验。</div></div>

<h2>⑥ 简明综合收益表全量（单位：人民币百万元，括号 = 负数）</h2>
<details open><summary>三列对照：2Q2026 / 2Q2025 / 1Q2026（未经审核）</summary>${stmtHtml}</details>
<div class="note" style="margin-top:18px">本页由 scripts/p5_build_report_view.py 自腾讯 2Q2026 业绩公告 PDF 机械生成，数字零手工调整；用途：验证指标库 MPM（IFRS→Non-IFRS 调节）链路的可解析性与可校验性。</div>
`;
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
    build_tencent()
