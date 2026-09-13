#!/usr/bin/env python3
"""P5 事实库构建：把三家样本公司的抽取/解析值经别名映射落到标准报表项目（规格 §3.6 StatementLineItem）。

输入：
  - 顺丰：docs/implementation/p5/sf_2026q1_statements.yaml（P5 抽取产物，163 行）
  - 腾讯：Tencent_2026_Q2_results.pdf（构建期现解析，复用 p5_build_report_view.parse_tencent）
  - 京东物流：Q1 财务资料 + FY2025 业绩公告（复用 parse_jdl）
  - 别名映射：docs/implementation/p5/item_alias_map_v0.yaml

输出：docs/implementation/p5/statement_facts.yaml（事实库，含未映射清单）
校验：生成期闭合断言（资产=负债+权益、调节链、分部加总），失败即构建失败。
"""
import datetime
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from p5_build_report_view import parse_jdl, parse_tencent  # noqa: E402

SF_YAML = ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"
ALIAS_V0 = ROOT / "docs/implementation/p5/item_alias_map_v0.yaml"
ALIAS = ROOT / "docs/implementation/p5/item_alias_map_v1.yaml"
OUT = ROOT / "docs/implementation/p5/statement_facts.yaml"

SOURCES = {
    "sf_002352": "p5_samples/sf_002352/SF_2026_Q1_report.pdf（巨潮披露原文）",
    "tencent_0700": "p5_samples/tencent_0700/Tencent_2026_Q2_results.pdf（腾讯官网业绩公告）",
    "jd_logistics_2618": "p5_samples/jd_logistics_2618/JDL_2026_Q1_financial_info.pdf + JDL_FY2025_annual_results_announcement.pdf",
    "alibaba_9988": "p5_samples/alibaba_9988/BABA_FY{yy}_annual_results.pdf（阿里巴巴投资者关系）",
    "cainiao": "p5_samples/cainiao_private/Cainiao_application_proof_20230926.pdf（招股书申报稿）",
    "jd_logistics_2618_full": "p5_samples/jd_logistics_2618/JDL_FY2025_annual_report.pdf（年报全文三表）",
}


def load_alias():
    """v1 别名表为全量（含 v0 全部公司定义），v0 仅作历史草案保留。"""
    v0 = yaml.safe_load(ALIAS_V0.read_text(encoding="utf-8"))
    v1 = yaml.safe_load(ALIAS.read_text(encoding="utf-8"))
    merged = dict(v0)
    merged["companies"] = {**v0["companies"], **v1["companies"]}
    return merged


def _find_row(items, name):
    """按行名取行；支持「名称#n」取第 n 次出现（1 起），处理重名行。"""
    if "#" in name:
        base, _, nth = name.rpartition("#")
        matches = [it for it in items if it["item"] == base]
        return matches[int(nth) - 1] if len(matches) >= int(nth) else None
    for it in items:
        if it["item"] == name:
            return it
    return None


def build_from_yaml(company, period, yaml_name, source, unit, alias, spec_key=None):
    """通用构建：按别名表把一份抽取 YAML 映射为标准事实；缺行/缺列即跳过，不编造。"""
    st = yaml.safe_load((ROOT / f"docs/implementation/p5/{yaml_name}").read_text(encoding="utf-8"))["statements"]
    facts, unmapped = [], []
    spec = alias["companies"][spec_key or company]["statements"]
    emitted = set()  # (stmt, item_id, role)：同角色多列回退时先取优先列，不重复入库
    for stmt_name, s in spec.items():
        items = st.get(stmt_name, [])
        mapped_names = set()
        for key, target in s["map"].items():
            cols = s["roles"]
            if key.startswith("_"):  # 组合映射：{sum: [...]}
                item_id = key[1:]
                names = target["sum"]
                mapped_names.update(n.split("#")[0] for n in names)
                for col, role in cols.items():
                    if (stmt_name, item_id, role) in emitted:
                        continue
                    vals = []
                    for n in names:
                        row = _find_row(items, n)
                        vals.append(None if row is None else row.get(col))
                    if any(v is None for v in vals):
                        continue
                    emitted.add((stmt_name, item_id, role))
                    facts.append({"company": company, "period": period, "statement": stmt_name,
                                  "item_id": item_id, "role": role, "value": sum(vals), "unit": unit,
                                  "source": source, "mapping": f"sum({'+'.join(names)})"})
                continue
            base_name = key.split("#")[0]
            mapped_names.add(base_name)
            item_id = target if isinstance(target, str) else target["item"]
            use_abs = isinstance(target, dict) and target.get("abs")
            row = _find_row(items, key)
            assert row is not None, f"{company} {period} 行名未取到: {key}"
            for col, role in cols.items():
                if (stmt_name, item_id, role) in emitted:
                    continue
                v = row.get(col)
                if v is None:
                    continue
                emitted.add((stmt_name, item_id, role))
                facts.append({"company": company, "period": period, "statement": stmt_name,
                              "item_id": item_id, "role": role,
                              "value": abs(v) if use_abs else v, "unit": unit,
                              "source": source, "mapping": key})
        for it in items:
            nm = it["item"]
            if nm not in mapped_names and not nm.endswith("：") and any(it.get(c) not in (None, 0) for c in s["roles"]):
                unmapped.append({"company": company, "statement": stmt_name, "item": nm,
                                 "reason": "无映射（v1 别名表未覆盖，待评审是否入库）"})
    return facts, unmapped


def build_alibaba(alias):
    facts, unmapped = [], []
    for yy in range(2019, 2027):
        src = SOURCES["alibaba_9988"].format(yy=yy)
        f, u = build_from_yaml("alibaba_9988", f"FY{yy}", f"alibaba_{yy}fy_statements.yaml",
                               src, "百万元", alias)
        facts += f
        unmapped += u
    return facts, unmapped


def build_cainiao(alias):
    facts, unmapped = [], []
    for yy in (2021, 2022, 2023):
        f, u = build_from_yaml("cainiao", f"FY{yy}", f"cainiao_{yy}fy_statements.yaml",
                               SOURCES["cainiao"], "千元", alias)
        facts += f
        unmapped += u
    return facts, unmapped


def build_jdl_full(alias):
    return build_from_yaml("jd_logistics_2618", "FY2025", "jdl_2025fy_statements.yaml",
                           SOURCES["jd_logistics_2618_full"], "千元", alias,
                           spec_key="jd_logistics_2618_full")


def build_sf(alias):
    st = yaml.safe_load(SF_YAML.read_text(encoding="utf-8"))["statements"]
    facts, unmapped = [], []
    spec = alias["companies"]["sf_002352"]["statements"]
    for stmt_name, s in spec.items():
        items = st[stmt_name]
        by_name = {it["item"]: it for it in items}
        mapped_names = set()
        for key, target in s["map"].items():
            cols = s["roles"]
            if key.startswith("_"):  # 组合映射：{sum: [...]}
                item_id = key[1:]
                names = target["sum"]
                mapped_names.update(names)
                for col, role in cols.items():
                    vals = [by_name[n].get(col) for n in names]
                    if any(v is None for v in vals):
                        continue
                    facts.append({"company": "sf_002352", "period": "2026Q1", "statement": stmt_name,
                                  "item_id": item_id, "role": role, "value": sum(vals), "unit": "千元",
                                  "source": SOURCES["sf_002352"], "mapping": f"sum({'+'.join(names)})"})
                continue
            mapped_names.add(key)
            item_id = target if isinstance(target, str) else target["item"]
            row = by_name.get(key)
            assert row is not None, f"顺丰行名未取到: {key}"
            for col, role in cols.items():
                v = row.get(col)
                if v is None:
                    continue
                facts.append({"company": "sf_002352", "period": "2026Q1", "statement": stmt_name,
                              "item_id": item_id, "role": role, "value": v, "unit": "千元",
                              "source": SOURCES["sf_002352"], "mapping": key})
        for it in items:
            nm = it["item"]
            if nm not in mapped_names and not nm.endswith("：") and any(it.get(c) not in (None, 0) for c in s["roles"]):
                unmapped.append({"company": "sf_002352", "statement": stmt_name, "item": nm,
                                 "reason": "无映射（v0 别名表未覆盖，待评审是否入库）"})
    return facts, unmapped


def build_tencent(alias):
    stmt, reported, adjs, non_ifrs = parse_tencent()  # 内部已做调节链闭合 + 交叉勾稽 + 分部加总断言
    spec = alias["companies"]["tencent_0700"]["statements"]["简明综合收益表"]
    col_roles = [spec["roles"]["col0"], spec["roles"]["col1"], spec["roles"]["col2"]]
    facts = []
    for label, target in spec["map"].items():
        item_id = target if isinstance(target, str) else target["item"]
        use_abs = isinstance(target, dict) and target.get("abs")
        for role, v in zip(col_roles, stmt[label]):
            facts.append({"company": "tencent_0700", "period": "2Q2026", "statement": "简明综合收益表",
                          "item_id": item_id, "role": role, "value": abs(v) if use_abs else v, "unit": "百万元",
                          "source": SOURCES["tencent_0700"], "mapping": label})
    return facts, []


def build_jdl(alias):
    q1, fy = parse_jdl()  # 内部已做锚点断言
    spec = alias["companies"]["jd_logistics_2618"]["statements"]["业绩摘要"]["map"]
    facts = []
    for period, data in [("2026Q1", q1), ("FY2025", fy)]:
        for key, item_id in spec.items():
            if key in data:
                facts.append({"company": "jd_logistics_2618", "period": period, "statement": "业绩摘要",
                              "item_id": item_id, "role": "cur", "value": data[key], "unit": "千元",
                              "source": SOURCES["jd_logistics_2618"], "mapping": key})
    return facts, []


def main():
    alias = load_alias()
    facts, unmapped = [], []
    for builder in (build_sf, build_tencent, build_jdl, build_alibaba, build_cainiao, build_jdl_full):
        f, u = builder(alias)
        facts += f
        unmapped += u

    idx = {}
    for f in facts:
        key = (f["company"], f["period"], f["item_id"], f["role"])
        if key in idx:
            # 同一事实的跨文档重复（业绩摘要 vs 年报三表）：值必须一致，否则即解析误差
            assert idx[key] == f["value"], (
                f"跨文档事实冲突 {key}: {idx[key]} vs {f['value']}（{f['mapping']}）"
            )
            continue
        idx[key] = f["value"]
    # 生成期闭合断言：资产 = 负债 + 权益（期末与期初两列）
    for role in ("end", "open"):
        ta = idx[("sf_002352", "2026Q1", "bs.total_assets", role)]
        tl = idx[("sf_002352", "2026Q1", "bs.total_liab", role)]
        eq = idx[("sf_002352", "2026Q1", "bs.equity", role)]
        assert ta == tl + eq, f"会计恒等式不成立（{role}）: {ta} != {tl}+{eq}"
    # 菜鸟/京东物流（全表）：资产总计 = 负债合计 + 权益总额（各期间期末）
    for co, periods in [("cainiao", ("FY2021", "FY2022", "FY2023")),
                        ("jd_logistics_2618", ("FY2025",))]:
        for pd_ in periods:
            ta = idx[(co, pd_, "bs.total_assets", "end")]
            tl = idx[(co, pd_, "bs.total_liab", "end")]
            eq = idx[(co, pd_, "bs.equity", "end")]
            assert ta == tl + eq, f"{co} {pd_} 会计恒等式不成立: {ta} != {tl}+{eq}"
    # 阿里巴巴：资产总额 = 负债 + 夹层权益 + 权益（夹层权益未入库，断言不小于号方向）
    for yy in range(2019, 2027):
        pd_ = f"FY{yy}"
        ta = idx[("alibaba_9988", pd_, "bs.total_assets", "end")]
        tl = idx[("alibaba_9988", pd_, "bs.total_liab", "end")]
        eq = idx[("alibaba_9988", pd_, "bs.equity", "end")]
        assert ta >= tl + eq and ta - (tl + eq) < ta * 0.05, (
            f"alibaba {pd_} 资产-负债-权益差异常: {ta} vs {tl}+{eq}"
        )
    # 收入 > 毛利 > 0（有毛利事实的快照）
    for co, pd_ in [("sf_002352", "2026Q1"), ("tencent_0700", "2Q2026"), ("jd_logistics_2618", "2026Q1")]:
        rev = idx[(co, pd_, "is.revenue", "cur")]
        gp_key = (co, pd_, "is.gross_profit", "cur")
        if gp_key in idx:
            assert rev > idx[gp_key] > 0, f"{co} 收入/毛利异常"

    doc = {
        "meta": {
            "generator": "scripts/p5_build_fact_store.py",
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "version": "v1",
            "alias_map": "docs/implementation/p5/item_alias_map_v1.yaml",
            "fact_count": len(facts),
            "unmapped_count": len(unmapped),
            "note": "事实 = (公司, 期间, 标准报表项目 item_id, 角色, 值)；角色：end/open（期末/期初）、cur/prev_yoy/prev_qoq（本期/上年同期/上季度）。",
        },
        "facts": facts,
        "unmapped": unmapped,
    }
    OUT.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"written -> {OUT}")
    print(f"facts: {len(facts)}  unmapped: {len(unmapped)}")
    by_co = {}
    for f in facts:
        by_co.setdefault(f'{f["company"]} {f["period"]}', 0)
        by_co[f'{f["company"]} {f["period"]}'] += 1
    for k, v in by_co.items():
        print(f"  {k}: {v} 项")


if __name__ == "__main__":
    main()
