#!/usr/bin/env python3
"""从 metric_dictionary_v1 派生 v1.1 内部指标库（2026-09-12 用户指令；D047 默认推荐策略）。

增量内容：
1. 全量条目补「常用/专业」分层（tier: core|professional）与「分析维度」
   （analysis_dimensions，受控词表：trend/structure/benchmark/warning/dupont/cash_link/value）；
2. 净新增 9 条：ocf_interest_coverage / ocf_total_debt_ratio / ccc_days / eva / sgr /
   roic / period_expense_ratio / volume_growth / price_change_rate
   （来源：25 指标文借鉴 #18、BP26 借鉴 #15、15 模型借鉴 #13 的 v1.1 候选落地）；
3. 口径变体：total_assets_return 增补 ROA 净利润口径、debt_equity_ratio 增补有息口径；
4. domains 增补 value（价值创造）。

规则：不改写 v1（保持不可变）；新增字段只增不删；EVA/SGR 等带使用警告进 benchmark/note。
权威依据：国资委《中央企业负责人经营业绩考核暂行办法》（EVA 央企口径、资本成本率 5.5%/4.1%、
研发费用加回）、CFA/CFI 现金周转周期标准定义、联合资信评级附件（调研 08 号）、
CAS/IFRS 原文（调研 07/10 号）。

用法：cd services/api && .venv/bin/python ../../scripts/finalize_metric_dictionary_v1_1.py
输入：config/metrics/metric_dictionary_v1.yaml
输出：config/metrics/metric_dictionary_v1_1.yaml
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "config/metrics/metric_dictionary_v1.yaml"
OUT = ROOT / "config/metrics/metric_dictionary_v1_1.yaml"

# 常用层（core）：25 指标文覆盖面 + 物流日常经营核心；其余归专业层（professional）。
TIER_CORE = {
    # 偿债与流动性
    "current_ratio", "quick_ratio", "cash_ratio", "debt_asset_ratio", "interest_coverage",
    # 营运资本
    "ar_turnover", "dso_days", "inventory_turnover", "dio_days", "ap_turnover", "dpo_days",
    "ccc_days",
    # 盈利
    "gross_margin", "operating_margin", "net_margin", "roe", "total_asset_turnover",
    "period_expense_ratio",
    # 增长
    "revenue_growth", "net_profit_growth",
    # 现金
    "ocf_current_liab_ratio", "ocf_net_profit_ratio", "free_cash_flow",
    # 物流日常经营
    "orders", "fulfilled_units", "revenue", "revenue_per_order", "cost_per_order",
    "gross_margin_logistics", "fulfillment_cost_rate", "collection_rate",
    "logistics_dso", "operating_cash_flow",
}

# 分析维度受控词表：
# trend=趋势多期 structure=结构拆解 benchmark=对标（行业/预算/标杆）
# warning=风险预警 dupont=杜邦/因子归因 cash_link=利润-现金勾稽 value=价值评估
DIMENSIONS: dict[str, list[str]] = {}

# 逐条覆盖（未列出的按 domain 默认）
_DIMENSION_DEFAULTS = {
    "solvency": ["trend", "warning", "benchmark"],
    "operation": ["trend", "benchmark"],
    "profitability": ["trend", "structure", "benchmark"],
    "growth": ["trend", "benchmark"],
    "cashflow": ["trend", "cash_link", "warning"],
    "scale": ["trend", "benchmark"],
    "value": ["benchmark", "value"],
}

_DIMENSION_OVERRIDES: dict[str, list[str]] = {
    "equity_multiplier": ["structure", "dupont", "warning"],
    "roe": ["trend", "dupont", "benchmark"],
    "total_asset_turnover": ["trend", "dupont", "benchmark"],
    "net_margin": ["trend", "dupont", "structure"],
    "ocf_net_profit_ratio": ["cash_link", "warning", "trend"],
    "free_cash_flow": ["cash_link", "value"],
    "cash_revenue_ratio": ["cash_link", "benchmark"],
    "debt_ebitda": ["warning", "benchmark"],
    "ebitda_interest_coverage": ["warning", "cash_link"],
    "cash_short_debt_ratio": ["warning", "trend"],
    "gross_margin": ["trend", "structure", "benchmark", "warning"],
    "revenue_growth": ["trend", "benchmark"],
    "net_profit_growth": ["trend", "benchmark", "warning"],
    "total_debt_capitalization": ["structure", "warning"],
    "long_debt_capitalization": ["structure", "warning"],
    # 新增条目
    "ccc_days": ["trend", "benchmark", "warning"],
    "ocf_interest_coverage": ["warning", "cash_link"],
    "ocf_total_debt_ratio": ["warning", "cash_link"],
    "eva": ["value", "benchmark"],
    "sgr": ["trend", "value"],
    "roic": ["value", "benchmark"],
    "period_expense_ratio": ["trend", "structure", "benchmark"],
    "volume_growth": ["trend", "structure"],
    "price_change_rate": ["trend", "structure"],
}

# 新增 9 条（v1.1 净增量）
NEW_METRICS: list[dict] = [
    {
        "metric_code": "ccc_days", "name": "现金周转周期", "domain": "operation",
        "definition": "从付现给供应商到从客户收现的平均天数（净营业周期），衡量营运资金占用时长。",
        "formula_text": "存货周转天数（DIO）+ 应收账款周转天数（DSO）− 应付账款周转天数（DPO）",
        "formula": {"op": "sub", "args": [{"op": "add", "args": ["dio_days", "dso_days"]}, "dpo_days"]},
        "unit": "天", "time_behavior": "period",
        "caliber": "CFA/CFI 标准定义（净营业周期）；与联合资信附件「净营业周期」同族。",
        "source_cas": ["存货", "应收账款", "应付账款", "营业收入", "营业成本"],
        "source_ifrs": "inventories / trade receivables / trade payables (IAS 1)",
        "depends_on": ["dio_days", "dso_days", "dpo_days"],
        "benchmark": "行业差异大；负值表示占用上游资金（强议价）；持续上升提示营运资金占用恶化，需结合业务模式评估。",
        "mpm": False,
        "provenance": "research/2026-09-11-25-indicators-article #20 + 调研 08 §3（联合资信净营业周期）",
    },
    {
        "metric_code": "ocf_interest_coverage", "name": "现金流利息覆盖", "domain": "solvency",
        "definition": "经营活动现金流量净额对利息费用的保障倍数，从收付实现制衡量付息能力。",
        "formula_text": "经营活动产生的现金流量净额 ÷ 利息费用",
        "formula": {"op": "div", "args": ["cf.ocf", "is.interest_exp"]},
        "unit": "倍", "time_behavior": "period",
        "caliber": "收付实现制口径；分母为费用化利息支出。与 interest_coverage（EBIT 权责口径）配对阅读。",
        "source_cas": ["经营活动产生的现金流量净额", "财务费用—利息费用"],
        "source_ifrs": "net cash from operating activities (IAS 7) / finance costs",
        "depends_on": [],
        "benchmark": "显著低于 EBIT 口径利息保障倍数，提示利润未转化为付息现金；两口径长期背离须复核利润质量。",
        "mpm": False,
        "provenance": "research/2026-09-11-25-indicators-article #16",
    },
    {
        "metric_code": "ocf_total_debt_ratio", "name": "现金流总债务比", "domain": "cashflow",
        "definition": "经营活动现金流量净额对全部债务的覆盖程度，衡量以经营现金偿还全部有息债务的能力。",
        "formula_text": "经营活动产生的现金流量净额 ÷（短期有息债务 + 长期有息债务）",
        "formula": {"op": "div", "args": ["cf.ocf", {"op": "sum", "args": ["bs.short_debt", "bs.long_debt"]}]},
        "unit": "倍", "time_behavior": "point_balance",
        "caliber": "分母为有息债务合计；信用分析与杠杆收购语境常用，使用时须结合资本性支出需求。",
        "source_cas": ["经营活动产生的现金流量净额", "短期借款", "长期借款", "应付债券"],
        "source_ifrs": "borrowings (IFRS 7/9)",
        "depends_on": [],
        "benchmark": "与 free_cash_flow 交叉验证（扣除 CAPEX 后的真偿债能力）；持续低于行业均值提示再融资依赖。",
        "mpm": False,
        "provenance": "research/2026-09-11-25-indicators-article #17",
    },
    {
        "metric_code": "roic", "name": "投入资本回报率", "domain": "profitability",
        "definition": "税后净营业利润（NOPAT）对投入资本（有息负债+股东权益）的回报率，与资本成本（WACC）对比判断是否创造价值。",
        "formula_text": "NOPAT ÷（有息负债 + 股东权益）；NOPAT = 净利润 +（利息支出 + 研发费用调整项）×（1 − 所得税率）",
        "formula": {"op": "div", "args": ["nopat", {"op": "sum", "args": ["bs.short_debt", "bs.long_debt", "bs.equity"]}]},
        "unit": "%", "time_behavior": "period",
        "caliber": "NOPAT 口径（税后经营利润，利息加回）。与 roce（联合资信总资本收益率：(净利润+利息支出)÷(权益+全部债务)）为同族不同口径，跨源对比须先对齐。",
        "source_cas": ["净利润", "利息费用", "研发费用", "短期借款", "长期借款", "所有者权益"],
        "source_ifrs": "invested capital = interest-bearing debt + equity",
        "depends_on": [],
        "benchmark": "ROIC > WACC 才创造价值；WACC 估算主观，结论须给出资本成本取值区间。",
        "mpm": False,
        "provenance": "借鉴 #13/#18 v1.1 候选落地（2026-09-12）；NOPAT 调整项按国资委 EVA 口径",
    },
    {
        "metric_code": "eva", "name": "经济增加值", "domain": "value",
        "definition": "税后净营业利润减去全部资本成本后的余额（国资委央企负责人业绩考核核心指标），衡量超过资本成本的价值创造。",
        "formula_text": "EVA = NOPAT − 调整后资本 × 资本成本率；央企口径资本成本率原则上 5.5%（军工等 4.1%；资产负债率超标上浮 0.5 个百分点），研发费用视同利润加回",
        "formula": {"op": "sub", "args": ["nopat", {"op": "mul", "args": ["invested_capital", "wacc"]}]},
        "unit": "元", "time_behavior": "period",
        "caliber": "国资委《中央企业负责人经营业绩考核暂行办法》口径；NOPAT = 净利润 +（利息支出 + 研发费用调整项）×（1 − 所得税率），调整项含非经常性收益与无息流动负债。",
        "source_cas": ["净利润", "利息费用", "研发费用", "所有者权益", "有息债务"],
        "source_ifrs": "residual income (Stern Stewart EVA framework)",
        "depends_on": [],
        "benchmark": "WACC/资本成本率取值主观性强，只作长期价值分析参考，不得仅凭 EVA 单独下创造价值结论（原文与国资委口径一致）。",
        "mpm": False,
        "provenance": "research/2026-09-11-25-indicators-article #24 + 国资委考核办法（2026-09-12 权威口径核查）",
    },
    {
        "metric_code": "sgr", "name": "可持续增长率", "domain": "growth",
        "definition": "不追加外部融资、仅靠留存利润支撑的理论最大销售增长率。",
        "formula_text": "ROE ×（1 − 分红率）",
        "formula": {"op": "mul", "args": ["roe", {"op": "sub", "args": ["identity_1", "payout_ratio"]}]},
        "unit": "%", "time_behavior": "period",
        "caliber": "Higgins 经典口径（期初权益）；实务常用期末权益 ROE 近似，须标注分母口径。",
        "source_cas": ["净利润", "所有者权益", "应付股利"],
        "source_ifrs": "sustainable growth rate (Higgins)",
        "depends_on": ["roe"],
        "benchmark": "理论上限口径，不等于实际增长潜力（企业常通过融资与并购超速增长）；实际增速持续高于 SGR 须提示融资依赖。",
        "mpm": False,
        "provenance": "research/2026-09-11-25-indicators-article #25",
    },
    {
        "metric_code": "period_expense_ratio", "name": "期间费用率", "domain": "profitability",
        "definition": "期间费用（销售+管理+研发+财务）占营业收入的比重，衡量费用管控与经营杠杆。",
        "formula_text": "（销售费用 + 管理费用 + 研发费用 + 财务费用）÷ 营业收入",
        "formula": {"op": "div", "args": [{"op": "sum", "args": ["is.selling_exp", "is.admin_exp", "is.rnd_exp", "is.fin_exp"]}, "is.revenue"]},
        "unit": "%", "time_behavior": "period",
        "caliber": "CAS 期间费用四项合计口径；财务费用含利息净支出，与运营口径费用（BP 管理）区分须标注。",
        "source_cas": ["销售费用", "管理费用", "研发费用", "财务费用", "营业收入"],
        "source_ifrs": "selling / general & administrative / R&D / finance costs",
        "depends_on": [],
        "benchmark": "与 BP26 借鉴 #15 登记 gap 一致；拆分费用明细看结构（sales/admin/R&D 各自占比）更有行动意义。",
        "mpm": False,
        "provenance": "借鉴 #15（BP26）v1.1 gap 落地（2026-09-12）",
    },
    {
        "metric_code": "volume_growth", "name": "销量增长率", "domain": "growth",
        "definition": "本期销量相对上期销量的增长，量价拆解（规模/价格/结构）中的量因子。",
        "formula_text": "（本期销量 − 上期销量）÷ 上期销量",
        "formula": {"op": "div", "args": [{"op": "sub", "args": ["volume_current", "volume_prior"]}, "volume_prior"]},
        "unit": "%", "time_behavior": "period",
        "caliber": "需要分产品量价数据（内部经营事实，L2 过程数据）；财报不可直接取数——绑定按缺失如实标注。",
        "source_cas": [],
        "source_ifrs": "n/a（经营量纲）",
        "depends_on": [],
        "benchmark": "与 price_change_rate 联合拆解收入增长（量·价·结构三因子）；物流行业对应业务量口径（件/单/吨）。",
        "mpm": False,
        "provenance": "借鉴 #15（BP26）v1.1 gap 落地；C08 量价三因子桥（借鉴 #6）配套",
    },
    {
        "metric_code": "price_change_rate", "name": "单价变动率", "domain": "growth",
        "definition": "本期平均单价相对上期的变动，量价拆解中的价因子。",
        "formula_text": "（本期平均单价 − 上期平均单价）÷ 上期平均单价",
        "formula": {"op": "div", "args": [{"op": "sub", "args": ["price_current", "price_prior"]}, "price_prior"]},
        "unit": "%", "time_behavior": "period",
        "caliber": "平均单价 = 收入 ÷ 销量，需分产品量价数据（L2）；财报不可直接取数——绑定按缺失如实标注。",
        "source_cas": [],
        "source_ifrs": "n/a（经营量纲）",
        "depends_on": [],
        "benchmark": "降价促销期与 volume_growth 组合解读收入增长质量；物流行业对应单均收入变动。",
        "mpm": False,
        "provenance": "借鉴 #15（BP26）v1.1 gap 落地；C08 量价三因子桥（借鉴 #6）配套",
    },
]

# 口径变体（既有条目增补 alternative_calibers）
CALIBER_ADDITIONS: dict[str, list[str]] = {
    "total_assets_return": [
        "ROA 净利润口径：净利润 ÷ 总资产（期末或平均分母均有流派；科普与投研常用，与库内联合资信总资产报酬率口径对比时须先对齐分子分母）",
    ],
    "debt_equity_ratio": [
        "有息债务口径：有息负债 ÷ 股东权益（剔除无息经营性负债，更严格反映财务杠杆；与全额负债口径的产权比率差异须标注）",
    ],
}


def main() -> int:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))

    data["decision_ref"] = str(data.get("decision_ref", "")) + "；2026-09-12 用户指令：内部指标库扩充与分层（tier + analysis_dimensions + 9 新增 + 口径变体，D047）"
    data["derived_from"] = list(data.get("derived_from") or []) + ["config/metrics/metric_dictionary_v1.yaml (v1.0)"]
    data["revision"] = "v1.1"
    domains: dict = data.setdefault("domains", {})
    domains.setdefault("value", "价值创造")

    added_dims = 0
    for collection in ("metrics_general", "metrics_logistics"):
        for entry in data[collection]:
            code = entry["metric_code"]
            entry["tier"] = "core" if code in TIER_CORE else "professional"
            dims = DIMENSIONS.get(code) or _DIMENSION_OVERRIDES.get(code) or _DIMENSION_DEFAULTS.get(entry["domain"]) or ["trend"]
            entry["analysis_dimensions"] = dims
            added_dims += 1
            for extra in CALIBER_ADDITIONS.get(code, []):
                entry.setdefault("alternative_calibers", [])
                if extra not in entry["alternative_calibers"]:
                    entry["alternative_calibers"].append(extra)

    existing = {e["metric_code"] for e in data["metrics_general"]}
    for metric in NEW_METRICS:
        if metric["metric_code"] in existing:
            raise SystemExit(f"重复 metric_code: {metric['metric_code']}")
        metric["tier"] = "core" if metric["metric_code"] in TIER_CORE else "professional"
        metric["analysis_dimensions"] = (
            _DIMENSION_OVERRIDES.get(metric["metric_code"])
            or _DIMENSION_DEFAULTS.get(metric["domain"])
            or ["trend"]
        )
        data["metrics_general"].append(metric)

    OUT.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    total = len(data["metrics_general"]) + len(data["metrics_logistics"])
    core = sum(1 for coll in ("metrics_general", "metrics_logistics") for e in data[coll] if e["tier"] == "core")
    print(f"written {OUT.name}: entries={total} (general {len(data['metrics_general'])} + logistics {len(data['metrics_logistics'])}), core={core}, professional={total - core}, dims={added_dims}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
