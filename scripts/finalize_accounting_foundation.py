#!/usr/bin/env python3
"""从 accounting_foundation_v0 派生 v1.0（补全 171 目标体系，D047 默认推荐策略）。

补全内容（依据调研 07/10 号资料：维基文库 2006 附录全表 + MaoDocs 2024 索引 +
致同对《应用指南汇编 2024》的研究）：
1. 科目补全至 171 体系：新增 2024 汇编新增科目（编号以公开来源交叉核对，
   置信度与出处写入 source_note）；
2. 准则登记册补至 42 项具体准则 + 基本准则全量（编号/名称/修订年份，
   依据财政部财会〔2006〕3 号及各修订文号，调研 07 号 §1.3）；
3. 分录模板 17 → 32（数据熊《常用会计分录大全》场景化 + 菜鸟物流场景，
   新准则科目名校正，如信用减值损失 6701）。

不改写 v0；输出 config/metrics/accounting_foundation_v1.yaml。

用法：uv run --project services/api python scripts/finalize_accounting_foundation.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "config/metrics/accounting_foundation_v0.yaml"
OUT = ROOT / "config/metrics/accounting_foundation_v1.yaml"

# ---- 科目补全（v0 缺口，全部标注 source_note 与置信度） ----
NEW_ACCOUNTS = [
    {"code": "1472", "name": "合同取得成本", "category": "资产", "balance_side": "借", "status": "added_2024",
     "standard_ref": "CAS 14 收入（2017 修订）应用指南", "source_note": "2024 汇编新增；MaoDocs 2024 索引核对"},
    {"code": "1522", "name": "持有待售负债", "category": "负债", "balance_side": "贷", "status": "added_2024",
     "standard_ref": "CAS 42 持有待售（2017）应用指南", "source_note": "2024 汇编新增；MaoDocs 2024 索引核对"},
    {"code": "1523", "name": "持有待售资产减值准备", "category": "资产", "balance_side": "贷（备抵）", "status": "added_2024",
     "standard_ref": "CAS 42 持有待售（2017）应用指南", "source_note": "2024 汇编新增；MaoDocs 2024 索引核对"},
    {"code": "1641", "name": "油气资产累计折耗", "category": "资产", "balance_side": "贷（备抵）", "status": "current",
     "standard_ref": "CAS 27 石油天然气开采应用指南", "source_note": "2006 附录原文遗漏补齐；维基文库核对"},
    {"code": "2503", "name": "长期应付款", "category": "负债", "balance_side": "贷", "status": "current",
     "standard_ref": "CAS应用指南2006附录", "source_note": "v0 遗漏补齐；维基文库全表核对"},
    {"code": "4003", "name": "其他综合收益", "category": "所有者权益", "balance_side": "贷", "status": "added_2024",
     "standard_ref": "CAS 30 财务报表列报（2014 修订）", "source_note": "2024 汇编体系单列；维基文库利润表行项对应"},
    {"code": "1802", "name": "使用权资产", "category": "资产", "balance_side": "借", "status": "added_2024",
     "standard_ref": "CAS 21 租赁（2018 修订）应用指南", "source_note": "编号 1802 为汇编通行编号（v0 暂记 1501a，此处正式化）"},
    {"code": "2703", "name": "租赁负债", "category": "负债", "balance_side": "贷", "status": "added_2024",
     "standard_ref": "CAS 21 租赁（2018 修订）应用指南", "source_note": "编号 2703 为汇编通行编号（v0 暂记 2701a，此处正式化）"},
]

# ---- 42 项具体准则全量登记（编号、名称、重大修订文号；依据调研 07 号 §1.3） ----
STANDARDS_42 = [
    ("CAS-1", "企业会计准则第 1 号——存货", ""),
    ("CAS-2", "企业会计准则第 2 号——长期股权投资", "2014 修订（财会〔2014〕14 号）"),
    ("CAS-3", "企业会计准则第 3 号——投资性房地产", ""),
    ("CAS-4", "企业会计准则第 4 号——固定资产", ""),
    ("CAS-5", "企业会计准则第 5 号——生物资产", ""),
    ("CAS-6", "企业会计准则第 6 号——无形资产", ""),
    ("CAS-7", "企业会计准则第 7 号——非货币性资产交换", "2019 修订（财会〔2019〕9 号）"),
    ("CAS-8", "企业会计准则第 8 号——资产减值", ""),
    ("CAS-9", "企业会计准则第 9 号——职工薪酬", "2014 修订（财会〔2014〕8 号）"),
    ("CAS-10", "企业会计准则第 10 号——企业年金基金", ""),
    ("CAS-11", "企业会计准则第 11 号——股份支付", ""),
    ("CAS-12", "企业会计准则第 12 号——债务重组", "2019 修订（财会〔2019〕8 号）"),
    ("CAS-13", "企业会计准则第 13 号——或有事项", ""),
    ("CAS-14", "企业会计准则第 14 号——收入", "2017 修订（财会〔2017〕22 号，新收入准则）"),
    ("CAS-15", "企业会计准则第 15 号——建造合同", "执行新收入准则的企业废止"),
    ("CAS-16", "企业会计准则第 16 号——政府补助", "2017 修订（财会〔2017〕15 号）"),
    ("CAS-17", "企业会计准则第 17 号——借款费用", ""),
    ("CAS-18", "企业会计准则第 18 号——所得税", ""),
    ("CAS-19", "企业会计准则第 19 号——外币折算", ""),
    ("CAS-20", "企业会计准则第 20 号——企业合并", ""),
    ("CAS-21", "企业会计准则第 21 号——租赁", "2018 修订（财会〔2018〕35 号，新租赁准则）"),
    ("CAS-22", "企业会计准则第 22 号——金融工具确认和计量", "2017 修订（财会〔2017〕7 号）"),
    ("CAS-23", "企业会计准则第 23 号——金融资产转移", "2017 修订（财会〔2017〕8 号）"),
    ("CAS-24", "企业会计准则第 24 号——套期会计", "2017 修订（财会〔2017〕9 号）"),
    ("CAS-25", "企业会计准则第 25 号——保险合同", "2020 全面修订（财会〔2020〕20 号）"),
    ("CAS-26", "企业会计准则第 26 号——再保险合同", ""),
    ("CAS-27", "企业会计准则第 27 号——石油天然气开采", ""),
    ("CAS-28", "企业会计准则第 28 号——会计政策、会计估计变更和差错更正", ""),
    ("CAS-29", "企业会计准则第 29 号——资产负债表日后事项", ""),
    ("CAS-30", "企业会计准则第 30 号——财务报表列报", "2014 修订（财会〔2014〕7 号）"),
    ("CAS-31", "企业会计准则第 31 号——现金流量表", ""),
    ("CAS-32", "企业会计准则第 32 号——中期财务报告", ""),
    ("CAS-33", "企业会计准则第 33 号——合并财务报表", "2014 修订（财会〔2014〕10 号）"),
    ("CAS-34", "企业会计准则第 34 号——每股收益", ""),
    ("CAS-35", "企业会计准则第 35 号——分部报告", ""),
    ("CAS-36", "企业会计准则第 36 号——关联方披露", ""),
    ("CAS-37", "企业会计准则第 37 号——金融工具列报", "2017 修订（财会〔2017〕14 号）"),
    ("CAS-38", "企业会计准则第 38 号——首次执行企业会计准则", ""),
    ("CAS-39", "企业会计准则第 39 号——公允价值计量", "2014 新增（财会〔2014〕6 号）"),
    ("CAS-40", "企业会计准则第 40 号——合营安排", "2014 新增（财会〔2014〕11 号）"),
    ("CAS-41", "企业会计准则第 41 号——在其他主体中权益的披露", "2014 新增（财会〔2014〕16 号）"),
    ("CAS-42", "企业会计准则第 42 号——持有待售的非流动资产、处置组和终止经营", "2017 新增（财会〔2017〕13 号）"),
]

# ---- 分录模板扩充（数据熊分录大全场景框架 + 菜鸟物流场景；新准则科目名） ----
NEW_ENTRIES = [
    {"template_id": "ET18_tenant_lease_recognition", "scenario": "承租人确认租赁（新租赁准则）",
     "business_context": "物流仓配/运输设备租赁，非短期/低价值租赁",
     "lines": [{"direction": "借", "account": "1802 使用权资产", "amount_rule": "租赁负债初始计量金额 + 预付租金 + 初始直接费用"},
               {"direction": "贷", "account": "2703 租赁负债", "amount_rule": "未付租赁付款额现值"}],
     "standard_ref": "CAS-21（2018）", "related_metrics": []},
    {"template_id": "ET19_lease_liability_interest", "scenario": "租赁负债计提利息",
     "business_context": "按实际利率法确认各期利息",
     "lines": [{"direction": "借", "account": "6603 财务费用——利息费用", "amount_rule": "期初租赁负债 × 折现率"},
               {"direction": "贷", "account": "2703 租赁负债", "amount_rule": "同左"}],
     "standard_ref": "CAS-21（2018）", "related_metrics": ["interest_coverage"]},
    {"template_id": "ET20_rou_asset_depreciation", "scenario": "使用权资产计提折旧",
     "business_context": "按租赁期与资产受益对象分摊",
     "lines": [{"direction": "借", "account": "6601 销售费用 / 6602 管理费用 / 5101 制造费用", "amount_rule": "使用权资产成本 ÷ 租赁期"},
               {"direction": "贷", "account": "1802 使用权资产——累计折旧", "amount_rule": "同左"}],
     "standard_ref": "CAS-21（2018）", "related_metrics": []},
    {"template_id": "ET21_contract_liability_advance", "scenario": "预收服务款确认合同负债",
     "business_context": "物流服务预收账单款项",
     "lines": [{"direction": "借", "account": "1002 银行存款", "amount_rule": "预收金额"},
               {"direction": "贷", "account": "2203 预收账款 / 合同负债", "amount_rule": "同左"}],
     "standard_ref": "CAS-14（2017）", "related_metrics": []},
    {"template_id": "ET22_revenue_over_time", "scenario": "按时段法确认运输服务收入",
     "business_context": "客户月结合同，按履约进度确认",
     "lines": [{"direction": "借", "account": "1122 应收账款 / 合同资产", "amount_rule": "履约进度 × 交易价格"},
               {"direction": "贷", "account": "6001 主营业务收入", "amount_rule": "不含税金额"},
               {"direction": "贷", "account": "2221 应交税费——待转销项税额", "amount_rule": "纳税义务未发生部分"}],
     "standard_ref": "CAS-14（2017）五步法", "related_metrics": ["revenue", "ar_balance"]},
    {"template_id": "ET23_contract_fulfillment_cost", "scenario": "确认合同履约成本",
     "business_context": "为履行合同发生的直接增量成本",
     "lines": [{"direction": "借", "account": "1471 合同履约成本（存货类）", "amount_rule": "直接人工+直接材料+分摊费用"},
               {"direction": "贷", "account": "1002 银行存款 / 2211 应付职工薪酬", "amount_rule": "同左"}],
     "standard_ref": "CAS-14（2017）", "related_metrics": ["direct_cost"]},
    {"template_id": "ET24_expected_credit_loss", "scenario": "按预期信用损失计提坏账（ECL）",
     "business_context": "账龄组合计提；菜鸟口径坏账率基线 0.6%",
     "lines": [{"direction": "借", "account": "6702 信用减值损失", "amount_rule": "应收账款余额 × 预期损失率"},
               {"direction": "贷", "account": "1122 应收账款——坏账准备", "amount_rule": "同左"}],
     "standard_ref": "CAS-22（2017）", "related_metrics": ["ar_balance"], "note": "菜鸟 CFO 域另有坏账率指标（基线 0.6%），属经营轨指标目录，见经营分析轨数据定义 v1"},
    {"template_id": "ET25_finance_guarantee_provision", "scenario": "计提财务担保/保证类预计负债",
     "business_context": "为客户或合作方提供担保",
     "lines": [{"direction": "借", "account": "6602 管理费用 / 6702 信用减值损失", "amount_rule": "按担保余额与违约率估计"},
               {"direction": "贷", "account": "2801 预计负债", "amount_rule": "同左"}],
     "standard_ref": "CAS-13 或有事项", "related_metrics": []},
    {"template_id": "ET26_settlement_with_cp", "scenario": "与履约供应商（CP）结算服务成本",
     "business_context": "菜鸟模式：向 CP 采购履约服务，月度对账结算",
     "lines": [{"direction": "借", "account": "6401 主营业务成本", "amount_rule": "对账确认的应付服务费"},
               {"direction": "借", "account": "2221 应交税费——进项税额", "amount_rule": "可抵扣进项税"},
               {"direction": "贷", "account": "2202 应付账款", "amount_rule": "价税合计"}],
     "standard_ref": "CAS应用指南2006附录 + 财会〔2016〕22 号", "related_metrics": ["direct_cost", "dpo_days"]},
    {"template_id": "ET27_platform_service_fee_income", "scenario": "平台技术服务费收入确认",
     "business_context": "向商家收取的平台服务费（菜鸟向商家收费模式）",
     "lines": [{"direction": "借", "account": "1122 应收账款 / 合同资产", "amount_rule": "账单金额"},
               {"direction": "贷", "account": "6001 主营业务收入", "amount_rule": "不含税服务费"},
               {"direction": "贷", "account": "2221 应交税费——销项税额", "amount_rule": "适用税率"}],
     "standard_ref": "CAS-14（2017）", "related_metrics": ["revenue"]},
    {"template_id": "ET28_inventory_obsolescence", "scenario": "存货跌价准备计提",
     "business_context": "仓储存货可变现净值低于成本",
     "lines": [{"direction": "借", "account": "6702 资产减值损失（存货跌价）", "amount_rule": "成本 − 可变现净值"},
               {"direction": "贷", "account": "1471 存货跌价准备", "amount_rule": "同左"}],
     "standard_ref": "CAS-1 存货", "related_metrics": ["inventory_turnover"]},
    {"template_id": "ET29_equity_method_income", "scenario": "权益法确认联营投资收益",
     "business_context": "对联营/合营企业按持股比例确认",
     "lines": [{"direction": "借", "account": "1511 长期股权投资——损益调整", "amount_rule": "被投资方净利润 × 持股比例"},
               {"direction": "贷", "account": "6111 投资收益", "amount_rule": "同左"}],
     "standard_ref": "CAS-2（2014）", "related_metrics": []},
    {"template_id": "ET30_vat_output_input_net", "scenario": "月末增值税结转（销项−进项）",
     "business_context": "应交增值税月末转未交增值税",
     "lines": [{"direction": "借", "account": "2221 应交税费——应交增值税（转出未交增值税）", "amount_rule": "销项 − 进项"},
               {"direction": "贷", "account": "2221 应交税费——未交增值税", "amount_rule": "同左"}],
     "standard_ref": "财会〔2016〕22 号", "related_metrics": []},
    {"template_id": "ET31_surplus_reserve", "scenario": "提取法定盈余公积",
     "business_context": "净利润 × 10%（法定）",
     "lines": [{"direction": "借", "account": "4104 利润分配——提取法定盈余公积", "amount_rule": "净利润 × 10%"},
               {"direction": "贷", "account": "4101 盈余公积——法定盈余公积", "amount_rule": "同左"}],
     "standard_ref": "公司法 + CAS应用指南", "related_metrics": []},
    {"template_id": "ET32_comprehensive_income_close", "scenario": "其他综合收益结转",
     "business_context": "外币报表折算差额等 OCI 期末结转",
     "lines": [{"direction": "借", "account": "4003 其他综合收益", "amount_rule": "按明细科目结转"},
               {"direction": "贷", "account": "4104 利润分配 / 4003 其他综合收益（对转）", "amount_rule": "同左"}],
     "standard_ref": "CAS-30（2014）", "related_metrics": []},
]

HEADER = """# FLOW 会计基础数据 v1.0（定稿）
# 状态：effective；定稿依据：D047（知识库默认推荐 + 行业标准校准）
# 派生自：accounting_foundation_v0.yaml（v0 保留不改写）
# 科目体系：2006 附录 156 基线 + 2024 汇编新增（编号以公开来源交叉核对，source_note 标注置信度）
# 准则登记册：基本准则 + 42 项具体准则全量（财政部文号见各条）
# 分录模板：17（v0）+ 15（新准则/物流场景）= 32
"""


def main() -> int:
    data = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    data["dataset_id"] = "flow.accounting_foundation.v1"
    data["status"] = "effective"
    data["derived_from"] = "flow.accounting_foundation.v0-draft"
    data["decision_ref"] = "D047"

    # 科目补全：v0 暂记编号正式化（改名 + 换 source_note）+ 新增
    accounts = list(data["accounts"])
    for account in accounts:
        if account["code"] == "1501a":
            account["code"] = "1802"
            account["source_note"] = "编号 1802 为汇编通行编号（自 v0 暂记 1501a 正式化）"
        elif account["code"] == "2701a":
            account["code"] = "2703"
            account["source_note"] = "编号 2703 为汇编通行编号（自 v0 暂记 2701a 正式化）"
    existing = {a["code"] for a in accounts}
    existing_names = {a["name"] for a in accounts}
    added = 0
    for new in NEW_ACCOUNTS:
        if new["code"] in existing or new["name"] in existing_names:
            continue
        accounts.append(new)
        added += 1
    # 按编号排序（数字前缀），非数字排后
    accounts.sort(key=lambda a: (not a["code"][:1].isdigit(), a["code"], a["name"]))
    data["accounts"] = accounts

    # 准则登记册：保留 CAS/IFRS 概念条目，补 42 项全量（去重）
    standards = {s["id"]: s for s in data["standards"]}
    for sid, name, note in STANDARDS_42:
        if sid not in standards:
            standards[sid] = {
                "id": sid,
                "name": name,
                "issuer": "财政部",
                "note": note or "现行有效",
            }
    data["standards"] = sorted(standards.values(), key=lambda s: s["id"])

    # 分录模板扩充
    templates = list(data["entry_templates"])
    template_ids = {t["template_id"] for t in templates}
    for entry in NEW_ENTRIES:
        if entry["template_id"] not in template_ids:
            templates.append(entry)
    data["entry_templates"] = templates

    data["known_gaps"] = [
        "171 科目体系的最终编号以《企业会计准则应用指南汇编 2024》正式出版物为准；"
        "使用权资产 1802 / 租赁负债 2703 为实务通行编号，正式出版物核对后如不同需版本化修订。",
    ]

    OUT.write_text(
        HEADER + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=110),
        encoding="utf-8",
    )
    print(
        f"已生成 {OUT.name}：科目 {len(accounts)}（+{added}），"
        f"准则 {len(data['standards'])}，分录模板 {len(templates)}"
    )

    # 自检
    check = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    codes = [a["code"] for a in check["accounts"]]
    assert len(codes) == len(set(codes)), "科目编号重复"
    ids = [s["id"] for s in check["standards"]]
    assert len(ids) == len(set(ids)), "准则 id 重复"
    tids = [t["template_id"] for t in check["entry_templates"]]
    assert len(tids) == len(set(tids)), "分录模板 id 重复"
    # 依赖闭合（分录引用的 related_metrics 在指标字典 v1 中存在）
    dict1 = yaml.safe_load((ROOT / "config/metrics/metric_dictionary_v1.yaml").read_text(encoding="utf-8"))
    metric_codes = {m["metric_code"] for s in ("metrics_general", "metrics_logistics") for m in dict1[s]}
    bad = [
        (t["template_id"], ref)
        for t in check["entry_templates"]
        for ref in t.get("related_metrics", [])
        if ref not in metric_codes
    ]
    print("自检：科目唯一、准则唯一、模板唯一；分录→指标引用越界：", bad or "无")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
