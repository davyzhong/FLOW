#!/usr/bin/env python3
"""从 metric_dictionary_v0 派生 v1.0 定稿（D047 默认推荐策略）。

规则：不改写 v0；对口径分歧项补结构化 default_caliber / alternative_calibers；
default_basis 一律指向行业标准/准则依据（国资委细则、CPA 教材、联合资信附件、
CAS/IFRS 原文），符合 D047「行业标准为默认口径，备选并存记录」。

用法：uv run --project services/api python scripts/finalize_metric_dictionary.py
输入：config/metrics/metric_dictionary_v0.yaml
输出：config/metrics/metric_dictionary_v1.yaml
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "config/metrics/metric_dictionary_v0.yaml"
OUT = ROOT / "config/metrics/metric_dictionary_v1.yaml"

# 分歧项的默认口径裁决（D047）：default = 行业标准默认；alternatives = 并存备选。
# 依据：国资委《中央企业综合绩效评价实施细则》（国资发分配〔2006〕157 号）、
# CPA《财务成本管理》2025 公式汇总（正保 PDF，调研 10 号 §3）、
# 联合资信评级报告指标附件（调研 08 号 §3）、CAS/IFRS 原文。
RULINGS: dict[str, dict] = {
    "cash_ratio": {
        "default_caliber": "分子仅取货币资金（最保守口径）",
        "default_basis": "CPA《财务成本管理》标准定义",
        "alternatives": ["分子含交易性金融资产（现金等价物扩展口径）"],
    },
    "interest_coverage": {
        "default_caliber": "分子 EBIT = 利润总额 + 费用化利息费用；分母 = 费用化 + 资本化全部利息",
        "default_basis": "CPA《财务成本管理》2025（费用化/资本化口径区分）",
        "alternatives": ["分母仅费用化利息（简化口径）"],
    },
    "ebitda_interest_coverage": {
        "default_caliber": "利息支出 = 费用化 + 资本化全部利息",
        "default_basis": "联合资信评级口径（全口径利息更审慎）",
        "alternatives": ["仅费用化利息"],
    },
    "total_debt_capitalization": {
        "default_caliber": "全部债务 = 短期借款 + 一年内到期非流动负债 + 长期借款 + 应付债券；不含应付票据与租赁负债",
        "default_basis": "联合资信评级附件口径（带息债务不含经营性应付款项）",
        "alternatives": ["含租赁负债（新租赁准则口径，标注后可用）"],
    },
    "ar_turnover": {
        "default_caliber": "分母 = 平均应收账款（不含应收票据）",
        "default_basis": "CPA 教材标准口径（周转率族教科书定义）",
        "alternatives": ["销售债权周转次数：分母含应收票据与应收款项融资（联合资信扩展口径）"],
    },
    "dso_days": {
        "default_caliber": "360 ÷ 应收账款周转率（360 天基准）",
        "default_basis": "CPA 教材与国资委细则惯例",
        "alternatives": ["365 天口径", "T12 收入滚动口径（FLOW 物流集 dso）"],
    },
    "ap_turnover": {
        "default_caliber": "分子 = 营业成本",
        "default_basis": "CPA 教材标准口径（与存货周转分子一致）",
        "alternatives": ["分子 = 采购成本（联合资信扩展口径）"],
    },
    "fixed_asset_turnover": {
        "default_caliber": "分母 = 平均固定资产净值",
        "default_basis": "CPA 教材标准口径（账面净值）",
        "alternatives": ["固定资产原值口径"],
    },
    "operating_margin": {
        "default_caliber": "营业利润 ÷ 营业收入（报表营业利润口径）",
        "default_basis": "财会〔2018〕15 号利润表行项目（报表口径为默认）",
        "alternatives": ["（营业总收入 − 营业成本 − 税金及附加）÷ 营业总收入（联合资信口径）"],
    },
    "roe": {
        "default_caliber": "净利润 ÷ 平均净资产（期初期末平均）；杜邦分解必须用本口径",
        "default_basis": "国资委《实施细则》与 CPA 教材一致采用平均口径",
        "alternatives": ["期末净资产口径（联合资信）", "加权平均口径（证监会 10 号文，上市公司披露）"],
    },
    "roce": {
        "default_caliber": "(净利润 + 费用化利息支出) ÷ (所有者权益 + 长期债务 + 短期债务)",
        "default_basis": "联合资信评级附件口径（中国市场主流评级口径）",
        "alternatives": ["EBIT ÷ 资本占用（国际口径）"],
    },
    "cost_expense_profit_ratio": {
        "default_caliber": "成本费用总额 = 营业成本 + 税金及附加 + 销售费用 + 管理费用 + 研发费用 + 财务费用（全口径）",
        "default_basis": "国资委《实施细则》成本费用利润率口径",
        "alternatives": ["不含税金及附加与研发费用的窄口径"],
    },
    "ebitda": {
        "default_caliber": "利润总额 + 计入财务费用的利息支出 + 固定资产折旧 + 无形资产摊销 + 长期待摊费用摊销（间接法）",
        "default_basis": "中国评级与信贷市场通行间接法（联合资信附件）",
        "alternatives": ["含投资收益与公允价值变动的宽口径（须标注）"],
    },
    "free_cash_flow": {
        "default_caliber": "经营活动现金流量净额 − 购建固定资产、无形资产和其他长期资产支付的现金（资本开支仅含购建付现）",
        "default_basis": "CPA 教材标准口径（管理用报表简化版）",
        "alternatives": ["含租赁付款本金与并购的扩展资本开支口径（MPM，须调节披露）"],
    },
    "cash_short_debt_ratio": {
        "default_caliber": "现金类资产 = 货币资金 + 交易性金融资产",
        "default_basis": "联合资信评级附件口径",
        "alternatives": ["仅货币资金（最保守）"],
    },
}

HEADER = """# FLOW 财务分析指标字典 v1.0（定稿）
# 状态：effective；定稿依据：D047（知识库默认推荐 + 行业标准口径校准）
# 派生自：metric_dictionary_v0.yaml（v0 保留不改写）
# 默认口径规则（D047）：行业标准/准则原文为默认口径，备选口径并存记录（alternative_calibers）
# 依据档案：research/07–10 号（财政部准则、国资委细则、CPA 2025 公式、联合资信附件）
"""


def main() -> int:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    data["dictionary_id"] = "flow.metric_dictionary.v1"
    data["status"] = "effective"
    data["derived_from"] = "flow.metric_dictionary.v0-draft"
    data["decision_ref"] = "D047"

    applied = 0
    for section in ("metrics_general", "metrics_logistics"):
        for metric in data.get(section, []):
            ruling = RULINGS.get(metric["metric_code"])
            if not ruling:
                continue
            metric["default_caliber"] = ruling["default_caliber"]
            metric["default_basis"] = ruling["default_basis"]
            metric["alternative_calibers"] = ruling["alternatives"]
            applied += 1

    OUT.write_text(
        HEADER + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110),
        encoding="utf-8",
    )
    print(f"已生成 {OUT.name}：{applied}/{len(RULINGS)} 项默认口径裁决已应用")

    # 结构自检：裁决项必有 default_caliber/default_basis；依赖闭合。
    check = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    codes = {m["metric_code"] for m in check["metrics_general"]} | {
        m["metric_code"] for m in check["metrics_logistics"]
    }
    missing = [
        code
        for code in RULINGS
        if not any(
            m["metric_code"] == code and m.get("default_caliber") and m.get("default_basis")
            for section in ("metrics_general", "metrics_logistics")
            for m in check.get(section, [])
        )
    ]
    assert not missing, f"裁决未生效: {missing}"
    bad = [
        (m["metric_code"], dep)
        for section in ("metrics_general", "metrics_logistics")
        for m in check.get(section, [])
        for dep in m.get("depends_on", [])
        if dep not in codes
    ]
    assert not bad, f"依赖不闭合: {bad}"
    print("结构自检通过：裁决齐备、依赖闭合")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
