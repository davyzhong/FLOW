#!/usr/bin/env python3
"""从 metric_dictionary_v1 派生 v1.1/v1.2 内部指标库（2026-09-12 用户指令；D047 默认推荐策略）。

增量内容：
1. 全量条目补「常用/专业」分层（tier: core|professional）与「分析维度」
   （analysis_dimensions，受控词表：trend/structure/benchmark/warning/dupont/cash_link/value）；
2. 净新增 9 条：ocf_interest_coverage / ocf_total_debt_ratio / ccc_days / eva / sgr /
   roic / period_expense_ratio / volume_growth / price_change_rate
   （来源：25 指标文借鉴 #18、BP26 借鉴 #15、15 模型借鉴 #13 的 v1.1 候选落地）；
3. 口径变体：total_assets_return 增补 ROA 净利润口径、debt_equity_ratio 增补有息口径；
4. domains 增补 value（价值创造）。

v1.2 增量（2026-09-17 借鉴 #21 行业参考包扩展）：
5. 净新增 1 条：current_asset_ratio（流动资产率，木木自由行业结构比率）；
6. 基准增强：ocf_current_liab_ratio（≥1 参考）、debt_equity_ratio（保守 100%/我国 200%）；
7. 新增顶层 industry_reference_packs：16 个行业参考包（15 行业经营指标目录来自数据熊
   15 行业 225 指标文 + 本地生活口径实例来自美团商家版；财务侧基准差异来自木木自由
   15 行业财务参考值文），YAML 权威零迁移（与 relations 同模式，DB 无列透传）。

规则：不改写 v1（保持不可变）；新增字段只增不删；EVA/SGR 等带使用警告进 benchmark/note。
决策注记与 derived_from 追加均已幂等化（重复运行不二次追加）。
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
    # v1.2 新增条目
    "current_asset_ratio": ["structure", "benchmark"],
}

# v1.2 基准增强（借鉴 #21：木木自由 15 行业财务参考值文中的通用阈值）
BENCHMARK_UPDATES: dict[str, str] = {
    "ocf_current_liab_ratio": "经验参考 ≥ 1（经营现金流全额覆盖流动负债）；低于 1 须结合现金流稳定性判断。",
    "debt_equity_ratio": "保守参考约 100%，我国实务中约 200% 亦常见；须结合行业资本结构判断。",
}

# v1.2 通用基准差异标注：行业结构比率（木木自由 2025-03-21 图 11）
DATABEAR_PROVENANCE = (
    "ObsidianWiki processed/微信知识库/数据熊/04_经营分析/"
    "2025-02-01 15个行业225个关键分析指标.md（借鉴 #21）"
)

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
    # v1.2 净新增（借鉴 #21：木木自由 2025-03-21《财务指标体系》行业结构比率）
    {
        "metric_code": "current_asset_ratio", "name": "流动资产率", "domain": "operation",
        "definition": "流动资产占资产总额的比例，反映资产流动性与行业资产结构特征。",
        "formula_text": "流动资产 ÷ 资产总计",
        "formula": {"op": "div", "args": ["bs.current_assets", "bs.total_assets"]},
        "unit": "%", "time_behavior": "point_balance",
        "caliber": "结构比率：行业差异极大（重资产与贸易型结构不可互比），须与同行业对比，不作绝对优劣判断。",
        "source_cas": ["流动资产合计", "资产总计"],
        "source_ifrs": "total current assets / total assets (IAS 1)",
        "depends_on": [],
        "benchmark": "纺织、冶金行业常规 30%–60%；商业批发企业可达 90% 以上；动态研判须与营业利润联动——比率与利润同升为经营好转信号，比率升而利润未升提示产品销售不畅。",
        "mpm": False,
        "provenance": "借鉴 #21（木木自由 2025-03-21《财务指标体系》行业结构比率；vault 原文回溯）",
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

# v1.2 行业参考包（借鉴 #21）：ops_indicators 为经营指标参考目录——暂无财报取数源，
# 仅作「该行业看什么」对标参考与行业包 v2 提升候选（数据到料后建 operating.* 事实）；
# financial_reference 只登记素材真实支持的口径/参考值，不虚构数值。
MUMU_PROVENANCE = (
    "ObsidianWiki processed/微信知识库/木木自由/01_数据分析必备/"
    "2025-03-21 《财务指标体系》：重要财务指标、财务报表指标体系、"
    "15个行业财务指标参考值、财务公式大全···.md（借鉴 #21）"
)
MEITUAN_PROVENANCE = (
    "ObsidianWiki processed/微信知识库/木木自由/01_数据分析必备/"
    "2024-07-30 大厂实操 美团数据指标体系搭建实例（附资相关材料下载）.md（借鉴 #21）"
)
STRUTURE_SOURCE = f"{DATABEAR_PROVENANCE}；木木自由 2025-03-21《财务指标体系》图 11 行业结构基准（借鉴 #21）"

INDUSTRY_PACKS: list[dict] = [
    {
        "industry_id": "ecommerce", "name": "电商",
        "note": "流量变现型行业，盯紧转化与留存。",
        "financial_reference": {
            "gross_margin": "自营与平台型口径差异大，不作统一经验值；对比须先对齐收入口径。",
        },
        "ops_indicators": [
            {"code": "conversion_rate", "name": "转化率", "meaning": "访问者中实际下单的比例，营销成效的第一道检验。"},
            {"code": "aov", "name": "客单价", "meaning": "订单总额 ÷ 订单数量，反映顾客平均消费能力。"},
            {"code": "repeat_purchase_rate", "name": "复购率", "meaning": "老顾客再次购买的频率，体现平台忠诚度与口碑。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "saas", "name": "SaaS",
        "note": "订阅收入模式，财务预测与客户粘性优先。",
        "financial_reference": {
            "revenue_growth": "订阅模式下与 NDR/流失率联动解读，单期增速不构成充分判断。",
        },
        "ops_indicators": [
            {"code": "mrr", "name": "月度持续收入（MRR）", "meaning": "订阅模式下的月度持续收入，用于财务预测和资源规划。"},
            {"code": "customer_retention_rate", "name": "客户留存率", "meaning": "老客户续订或持续使用的比例，高留存代表产品粘性强。"},
            {"code": "churn_rate", "name": "流失率", "meaning": "一定周期内终止服务的客户占比，经营健康度的重要警示灯。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "retail", "name": "零售（含商业批发）",
        "note": "实体运营型行业，死磕效率与周转。",
        "financial_reference": {
            "current_asset_ratio": "商业批发企业的流动资产率可达 90% 以上（轻存货周转、重流动资产结构）。",
        },
        "ops_indicators": [
            {"code": "same_store_sales_growth", "name": "同店销售增长率", "meaning": "排除新店因素后比较销售额增减，直观判断老店活力。"},
            {"code": "foot_traffic", "name": "客流量", "meaning": "进店顾客数变化，反映市场推广效果与门店吸引力。"},
            {"code": "inventory_turnover", "name": "库存周转率", "meaning": "销售成本对比平均库存，体现货品周转效率和资金使用状况。"},
        ],
        "provenance": STRUTURE_SOURCE,
    },
    {
        "industry_id": "manufacturing", "name": "制造",
        "note": "生产履约型行业，严控质量与交付。",
        "financial_reference": {
            "current_asset_ratio": "纺织、冶金行业流动资产率常规区间 30%–60%。",
        },
        "ops_indicators": [
            {"code": "production_efficiency", "name": "生产效率", "meaning": "实际产量与理论产能对比，衡量产线资源利用。"},
            {"code": "quality_yield", "name": "良品率", "meaning": "合格产品占总产量比例，凸显质量管控水平。"},
            {"code": "on_time_delivery", "name": "订单准时交付率", "meaning": "按时完成交付的订单比例，直接影响客户满意度和信誉。"},
        ],
        "provenance": STRUTURE_SOURCE,
    },
    {
        "industry_id": "finance", "name": "金融",
        "note": "专业壁垒型行业，守住风控与效能。",
        "financial_reference": {
            "debt_asset_ratio": "银行业高杠杆为经营常态，工业企业的 40%–60% 经验区间不适用。",
        },
        "ops_indicators": [
            {"code": "npl_ratio", "name": "不良贷款率（NPL）", "meaning": "不良贷款占整体贷款比重，信贷资产质量的核心指标。"},
            {"code": "nim", "name": "净息差（NIM）", "meaning": "（利息收入 − 利息支出）÷ 生息资产，银行主要盈利能力。"},
            {"code": "car", "name": "资本充足率（CAR）", "meaning": "资本总额对风险资产的覆盖程度，保障金融机构稳健运营。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "catering", "name": "餐饮",
        "note": "实体运营型行业，翻台效率与成本结构并重。",
        "financial_reference": {
            "gross_margin": "菜品成本率（原材料成本 ÷ 菜品售价）为行业主口径，与工业企业毛利口径不可互比。",
        },
        "ops_indicators": [
            {"code": "table_turnover_rate", "name": "翻台率", "meaning": "一定时段内同一张桌子被重复使用的次数，直接关系营收效率。"},
            {"code": "average_check", "name": "客单价", "meaning": "营业额 ÷ 顾客数量，反映人均消费水平和菜品定价策略。"},
            {"code": "food_cost_percentage", "name": "菜品成本率", "meaning": "原材料成本占菜品售价比例，影响毛利与定价策略。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "hotel", "name": "酒店",
        "note": "实体运营型行业，入住率与房价双轮驱动。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "occupancy_rate", "name": "客房入住率", "meaning": "已售客房数 ÷ 可售客房数，衡量客源吸引力的基础指标。"},
            {"code": "revpar", "name": "每可售房收入（RevPAR）", "meaning": "综合入住率和平均房价，体现酒店整体营收能力。"},
            {"code": "adr", "name": "平均房价（ADR）", "meaning": "客房收入 ÷ 已售客房数，评估定价水平和市场定位。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "education", "name": "教育培训",
        "note": "专业壁垒型行业，交付质量决定续班与生源。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "course_completion_rate", "name": "完课率", "meaning": "报名与完成学习的对比，课程设计与教学质量的晴雨表。"},
            {"code": "renewal_rate", "name": "续班率", "meaning": "老学员继续报名后续课程的比例，关系培训机构的长期生源。"},
            {"code": "teacher_satisfaction", "name": "师资满意度", "meaning": "基于学员评价或打分，洞察教学效果与教师水平。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "healthcare", "name": "医疗",
        "note": "专业壁垒型行业，运转效率与诊疗质量并重。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "bed_occupancy_rate", "name": "床位使用率", "meaning": "实际占用床日数 ÷（床位总数 × 天数），医院运转度的重要体现。"},
            {"code": "alos", "name": "平均住院日（ALOS）", "meaning": "住院总床日 ÷ 出院人数，住院管理与诊疗效率的核心指标。"},
            {"code": "readmission_rate", "name": "再入院率", "meaning": "出院后再次入院的比例，评估诊疗效果及康复质量。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "agriculture", "name": "农业",
        "note": "生产履约型行业，单产与转化效率优先。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "yield_per_area", "name": "亩产量", "meaning": "作物总产量 ÷ 种植面积，衡量种植效率和品种优劣。"},
            {"code": "survival_rate", "name": "成活率", "meaning": "从播种或投放到收获过程的成活比例，反映生产环境与技术水平。"},
            {"code": "fcr", "name": "饲料转化率（FCR）", "meaning": "饲料消耗与体重增量之比，越低说明饲料利用率越高。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "logistics", "name": "物流",
        "note": "生产履约型行业，履约时效与破损控制优先；FLOW 物流专用集（metrics_logistics）已覆盖其财务侧。",
        "financial_reference": {
            "debt_asset_ratio": "物流央企口径约 47%–57%（中国物流集团，见 debt_asset_ratio 基准）。",
            "interest_coverage": "物流央企实例 5.45–9.31 倍（见 interest_coverage 基准）。",
        },
        "ops_indicators": [
            {"code": "on_time_delivery_rate", "name": "准时交付率", "meaning": "物流履约时效的关键评估标准，影响客户信赖。"},
            {"code": "average_delivery_time", "name": "平均交付时间", "meaning": "从出库到签收的平均时长，体现运作效率。"},
            {"code": "damage_rate", "name": "破损率", "meaning": "运输过程中包裹或货物的损坏比例，直接影响企业形象与赔付成本。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "real_estate", "name": "房地产",
        "note": "周期型行业，去化速度与出租水平定生死。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "sell_through_rate", "name": "销售去化率", "meaning": "一定周期内销售房源的速度与数量，判断项目热度。"},
            {"code": "average_selling_price", "name": "平均单价", "meaning": "成交房源总价 ÷ 总面积或套数，市场定位参考。"},
            {"code": "lease_occupancy_rate", "name": "出租率（租赁）", "meaning": "已出租面积占可出租面积比重，商业地产盈利水平的写照。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "media", "name": "媒体",
        "note": "流量变现型行业，内容质量决定用户粘性。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "ctr", "name": "点击率（CTR）", "meaning": "广告点击次数 ÷ 展示次数，衡量广告素材对受众的吸引力。"},
            {"code": "completion_rate", "name": "完播率（视频）", "meaning": "完整观看数占总播放数之比，体现内容质量与用户粘性。"},
            {"code": "user_retention", "name": "用户留存率", "meaning": "用户持续在平台活跃的比例，媒体长期发展的基石。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "it_services", "name": "IT 服务",
        "note": "专业壁垒型行业，响应速度与系统可用性即产品。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "mttr_respond", "name": "平均响应时间", "meaning": "从工单提交到开始处理的速度，影响客户满意度。"},
            {"code": "mttr_repair", "name": "平均修复时间", "meaning": "从故障发生到彻底解决的平均耗时，体现技术支持能力。"},
            {"code": "service_availability", "name": "服务可用性", "meaning": "正常运行时间占比，系统或网站稳定性的重要保证。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "gaming", "name": "游戏",
        "note": "流量变现型行业，活跃与付费结构决定生命周期。",
        "financial_reference": {},
        "ops_indicators": [
            {"code": "dau", "name": "日活跃用户（DAU）", "meaning": "每日登录且有有效行为的玩家数，评估游戏热度的核心指标。"},
            {"code": "paying_user_ratio", "name": "付费用户占比", "meaning": "有付费行为的玩家占总玩家比例，决定营收潜力。"},
            {"code": "retention_rate", "name": "留存率", "meaning": "从注册至后续多日的持续登录状况，关系游戏生命周期长短。"},
        ],
        "provenance": DATABEAR_PROVENANCE,
    },
    {
        "industry_id": "local_services", "name": "本地生活（外卖零售）",
        "note": "大厂实证：美团商家版以「统一口径」为地基，总览/营业/流量/顾客/商品/营销六板块逐层下钻；此处登记其口径定义实例。",
        "financial_reference": {
            "revenue": "美团口径实例——营业额 = 商品原价 + 包装费 + 配送费，与「预计收入（含所有费用的实际收入）」为两个口径，发布前须显式选定；有效订单 = 已接单且未取消（区别于下单口径）。",
        },
        "ops_indicators": [
            {"code": "shop_entry_conversion", "name": "入店转化率", "meaning": "入店人数 ÷ 曝光人数（流量漏斗第一层）。"},
            {"code": "order_conversion", "name": "下单转化率", "meaning": "下单人数 ÷ 入店人数（流量漏斗第二层）。"},
            {"code": "customer_lifecycle_layering", "name": "顾客生命周期分层", "meaning": "活跃 = 近 30 天成交；沉默 = 30–60 天；流失 = 60–90 天（顾客留存状态口径实例）。"},
        ],
        "provenance": MEITUAN_PROVENANCE,
    },
]


DECISION_NOTES = [
    "；2026-09-12 用户指令：内部指标库扩充与分层（tier + analysis_dimensions + 9 新增 + 口径变体，D047）",
    "；2026-09-17 借鉴 #21 行业参考包扩展 v1.2（16 行业参考目录 + 流动资产率 + 基准增强）",
]


def main() -> int:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))

    # 决策注记幂等追加（重复运行不二次拼接）
    decision_ref = str(data.get("decision_ref", ""))
    for note in DECISION_NOTES:
        if note not in decision_ref:
            decision_ref += note
    data["decision_ref"] = decision_ref
    # derived_from 追加幂等 + 修复字符串被 list() 炸成单字符的缺陷
    raw_derived = data.get("derived_from")
    derived = raw_derived if isinstance(raw_derived, list) else ([raw_derived] if raw_derived else [])
    derived_entry = "config/metrics/metric_dictionary_v1.yaml (v1.0)"
    if derived_entry not in derived:
        derived.append(derived_entry)
    data["derived_from"] = derived
    data["revision"] = "v1.2"
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
            if code in BENCHMARK_UPDATES:
                entry["benchmark"] = BENCHMARK_UPDATES[code]

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

    data["industry_reference_packs"] = INDUSTRY_PACKS

    OUT.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    total = len(data["metrics_general"]) + len(data["metrics_logistics"])
    core = sum(1 for coll in ("metrics_general", "metrics_logistics") for e in data[coll] if e["tier"] == "core")
    print(
        f"written {OUT.name}: entries={total} (general {len(data['metrics_general'])} + "
        f"logistics {len(data['metrics_logistics'])}), core={core}, professional={total - core}, "
        f"dims={added_dims}, industry_packs={len(data['industry_reference_packs'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
