#!/usr/bin/env python3
"""P5 事实库查询 + 指标库 AST 引擎（规格 §5「可查询 / 可使用」的最小可用实现）。

能力：
  1. 事实查询：--company sf_002352 --period 2026Q1 --item is.revenue
  2. 单指标计算：--metric gross_margin --company sf_002352 --period 2026Q1
  3. 覆盖率矩阵（默认）：指标库 v0 全部通用指标 × 全部公司期间快照，
     输出 docs/implementation/p5/metric_coverage_matrix.md（可观测：哪些指标已可算、缺哪些取数）。

引擎语义（指标库 v0 formula AST）：
  - 字符串参数：bs./is./cf. 开头 → 报表项目事实；否则 → 指标编码，递归求值（depends_on 闭合）；
  - avg(bs.x)：流动/期末口径 = (期末 + 期初) / 2；prior(is.x)：上年同期列；prior(bs.x)：期初列；
  - 缺数不编造：抛 Missing 并在矩阵中标注首个缺口。
"""
import argparse
import datetime
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "docs/implementation/p5/statement_facts.yaml"
METRICS_YAML = ROOT / "docs/knowledge-base/02_research/synthesis/指标库初始数据集_v0_草案.yaml"
MATRIX_OUT = ROOT / "docs/implementation/p5/metric_coverage_matrix.md"

UNIT_TO_YI = {"千元": 1e5, "百万元": 1e2}


class Missing(Exception):
    pass


class Engine:
    def __init__(self, facts_doc, metrics_doc):
        self.facts = {}
        self.units = {}
        for f in facts_doc["facts"]:
            key = (f["company"], f["period"], f["item_id"])
            self.facts.setdefault(key, {})[f["role"]] = f["value"]
            self.units[(f["company"], f["period"])] = f["unit"]
        self.metrics = {m["metric_code"]: m for m in metrics_doc["metrics_general"]}
        self.stack = []

    def get_item(self, co, pd_, item_id, role=None):
        roles = self.facts.get((co, pd_, item_id), {})
        if role is None:
            role = "end" if item_id.startswith("bs.") else "cur"
        if role not in roles:
            raise Missing(f"{item_id}({role})")
        return roles[role]

    def ev(self, node, co, pd_):
        if isinstance(node, (int, float)):
            return node
        if isinstance(node, str):
            if node.startswith(("bs.", "is.", "cf.", "mpm.")):
                return self.get_item(co, pd_, node)
            if node in self.metrics:
                return self.ev_metric(node, co, pd_)
            raise Missing(node)
        op, args = node["op"], node["args"]
        if op == "identity":
            return self.ev(args[0], co, pd_)
        if op == "avg":
            x = args[0]
            return (self.get_item(co, pd_, x, "end") + self.get_item(co, pd_, x, "open")) / 2
        if op == "prior":
            x = args[0]
            return self.get_item(co, pd_, x, "open" if x.startswith("bs.") else "prev_yoy")
        vals = [self.ev(a, co, pd_) for a in args]
        if op == "div":
            return vals[0] / vals[1]
        if op == "sub":
            return vals[0] - vals[1]
        if op == "add":
            return sum(vals)
        if op == "mul":
            r = 1
            for v in vals:
                r *= v
            return r
        raise ValueError(f"未知算子: {op}")

    def ev_metric(self, code, co, pd_):
        if code in self.stack:
            raise ValueError(f"指标循环依赖: {' -> '.join(self.stack + [code])}")
        self.stack.append(code)
        try:
            return self.ev(self.metrics[code]["formula"], co, pd_)
        finally:
            self.stack.pop()


def fmt_value(m, v, unit):
    if m["unit"] in ("%", "％"):
        return f"{v * 100:.1f}%"
    if m["unit"] in ("倍", "次") or m["unit"].startswith("倍"):
        return f"{v:.2f}"
    if m["unit"] == "天":
        return f"{v:.0f}"
    return f"{v / UNIT_TO_YI[unit]:,.1f} 亿"  # 绝对额换算为亿元


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company")
    ap.add_argument("--period")
    ap.add_argument("--item")
    ap.add_argument("--metric")
    args = ap.parse_args()

    facts_doc = yaml.safe_load(FACTS.read_text(encoding="utf-8"))
    metrics_doc = yaml.safe_load(METRICS_YAML.read_text(encoding="utf-8"))
    eng = Engine(facts_doc, metrics_doc)
    snapshots = sorted({(f["company"], f["period"]) for f in facts_doc["facts"]})

    if args.item:
        for co, pd_ in snapshots:
            if args.company and co != args.company or args.period and pd_ != args.period:
                continue
            for role, v in sorted(eng.facts.get((co, pd_, args.item), {}).items()):
                print(f"{co} {pd_} {args.item} [{role}] = {v:,} {eng.units[(co, pd_)]}")
        return

    if args.metric:
        m = eng.metrics[args.metric]
        for co, pd_ in snapshots:
            if args.company and co != args.company or args.period and pd_ != args.period:
                continue
            try:
                v = eng.ev_metric(args.metric, co, pd_)
                print(f"{co} {pd_} {args.metric}（{m['name']}）= {fmt_value(m, v, eng.units[(co, pd_)])}")
            except Missing as e:
                print(f"{co} {pd_} {args.metric}: 缺取数 {e}")
        return

    # ---- 覆盖率矩阵 + 一致性自检 ----
    lines = [
        "# P5 指标覆盖率矩阵：指标库 v0 通用指标 × 样本快照",
        "",
        f"- 生成：`scripts/p5_query_facts.py`，{datetime.datetime.now().isoformat(timespec='seconds')}",
        "- 口径注意：avg 为（期末+期初）/2、prior 为上年同期列；单季数据未年化；腾讯一般及行政开支含研发（口径差异已标注）；绝对额指标已换算为亿元。",
        "",
        "| 指标 | 名称 | " + " | ".join(f"{co} {pd_}" for co, pd_ in snapshots) + " |",
        "|---|---|" + "---|" * len(snapshots),
    ]
    computable = {s: 0 for s in snapshots}
    for m in metrics_doc["metrics_general"]:
        cells = []
        for co, pd_ in snapshots:
            try:
                v = eng.ev_metric(m["metric_code"], co, pd_)
                cells.append(fmt_value(m, v, eng.units[(co, pd_)]))
                computable[(co, pd_)] += 1
            except Missing as e:
                cells.append(f"缺 {e}")
        lines.append(f"| {m['metric_code']} | {m['name']} | " + " | ".join(cells) + " |")
    lines += ["", "| **可计算指标数** | | " + " | ".join(f"**{computable[s]}/{len(metrics_doc['metrics_general'])}**" for s in snapshots) + " |", ""]
    MATRIX_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written -> {MATRIX_OUT}")
    for s in snapshots:
        print(f"  {s[0]} {s[1]}: {computable[s]}/{len(metrics_doc['metrics_general'])} 指标可计算")

    # ---- 一致性自检：引擎路径 vs 独立直算路径（防映射错误）----
    st = yaml.safe_load((ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml").read_text())["statements"]
    is_ = {it["item"]: it for it in st["合并利润表"]}
    bs = {it["item"]: it for it in st["合并资产负债表"]}
    direct_gm = (is_["一、营业总收入"]["本期发生额"] - is_["其中：营业成本"]["本期发生额"]) / is_["一、营业总收入"]["本期发生额"]
    eng_gm = eng.ev_metric("gross_margin", "sf_002352", "2026Q1")
    assert abs(direct_gm - eng_gm) < 1e-12, f"毛利率两路径不一致: {direct_gm} vs {eng_gm}"
    direct_da = bs["负债合计"]["期末余额"] / bs["资产总计"]["期末余额"]
    eng_da = eng.ev_metric("debt_asset_ratio", "sf_002352", "2026Q1")
    assert abs(direct_da - eng_da) < 1e-12, "资产负债率两路径不一致"
    # 腾讯毛利率 vs 公告披露约数（披露值从原文现解析）
    import re
    import pdfplumber
    with pdfplumber.open(str(ROOT / "docs/knowledge-base/02_research/original/p5_samples/tencent_0700/Tencent_2026_Q2_results.pdf")) as pdf:
        t5 = pdf.pages[4].extract_text() or ""
    disclosed = int(re.search(r"毛利率 (\d+)%", t5).group(1)) / 100
    eng_gm_t = eng.ev_metric("gross_margin", "tencent_0700", "2Q2026")
    assert abs(eng_gm_t - disclosed) < 0.005, f"腾讯毛利率与披露约数不符: {eng_gm_t:.3f} vs {disclosed}"
    print("自检通过：顺丰毛利率/资产负债率两路径一致；腾讯毛利率与公告披露约数一致")


if __name__ == "__main__":
    main()
