---
doc_id: FLOW-P5-COVERAGE-MATRIX-001
title: P5 指标覆盖率矩阵：指标库 v0 通用指标 × 样本快照
doc_type: generated
status: generated
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
generator_ref: scripts/p5_query_facts.py
input_hash: 85fb7e1f8851c67a7862909ccb6c8bf13ee873855a072c1689f6d06f4180ab9c
---

# P5 指标覆盖率矩阵：指标库 v0 通用指标 × 样本快照

- 生成：`scripts/p5_query_facts.py`，2026-09-14T08:54:05
- 口径注意：avg 为（期末+期初）/2、prior 为上年同期列；单季数据未年化；腾讯一般及行政开支含研发（口径差异已标注）；绝对额指标已换算为亿元。

| 指标 | 名称 | alibaba_9988 FY2019 | alibaba_9988 FY2020 | alibaba_9988 FY2021 | alibaba_9988 FY2022 | alibaba_9988 FY2023 | alibaba_9988 FY2024 | alibaba_9988 FY2025 | alibaba_9988 FY2026 | cainiao FY2021 | cainiao FY2022 | cainiao FY2023 | jd_logistics_2618 2026Q1 | jd_logistics_2618 FY2025 | sf_002352 2026Q1 | tencent_0700 2Q2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| current_ratio | 流动比率 | 1.30 | 1.91 | 1.70 | 1.66 | 1.81 | 1.79 | 1.55 | 1.28 | 1.43 | 0.81 | 1.16 | 缺 bs.current_assets(end) | 1.32 | 1.28 | 缺 bs.current_assets(end) |
| quick_ratio | 速动比率 | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 1.42 | 0.81 | 1.15 | 缺 bs.current_assets(end) | 1.30 | 1.23 | 缺 bs.current_assets(end) |
| cash_ratio | 现金比率 | 0.91 | 1.37 | 0.85 | 0.49 | 0.50 | 0.59 | 0.33 | 0.28 | 0.64 | 0.47 | 0.39 | 缺 bs.cash(end) | 0.41 | 0.24 | 缺 bs.cash(end) |
| ocf_current_liab_ratio | 现金流量比率 | 0.73 | 0.75 | 0.61 | 0.37 | 0.52 | 0.43 | 0.38 | 0.16 | 0.27 | 0.11 | 0.08 | 缺 cf.ocf(cur) | 0.42 | 0.05 | 缺 cf.ocf(cur) |
| debt_asset_ratio | 资产负债率 | 36.2% | 33.0% | 35.9% | 36.2% | 35.9% | 37.0% | 39.6% | 41.0% | 58.0% | 62.9% | 63.2% | 缺 bs.total_liab(end) | 52.0% | 47.8% | 缺 bs.total_liab(end) |
| debt_equity_ratio | 产权比率 | 0.57 | 0.50 | 0.56 | 0.57 | 0.57 | 0.59 | 0.66 | 0.70 | 1.38 | 1.69 | 1.72 | 缺 bs.total_liab(end) | 1.08 | 0.92 | 缺 bs.total_liab(end) |
| interest_coverage | 利息保障倍数 | 19.65 | 32.06 | 39.55 | 16.05 | 14.71 | 12.81 | 17.82 | 14.50 | -0.68 | -0.70 | -1.01 | 缺 is.total_profit(cur) | 缺 is.interest_exp(cur) | 9.84 | 缺 is.interest_exp(cur) |
| ebitda_interest_coverage | EBITDA 利息倍数 | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.total_profit(cur) | 缺 is.interest_exp(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| total_debt_capitalization | 全部债务资本化比率 | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 27.3% | 29.7% | 缺 bs.short_debt(end) |
| long_debt_capitalization | 长期债务资本化比率 | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 19.6% | 18.7% | 缺 bs.long_debt(end) |
| ar_turnover | 应收账款周转率 | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 12.20 | 2.49 | 缺 bs.ar(end) |
| dso_days | 应收账款周转天数 | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 缺 bs.ar(end) | 30 | 145 | 缺 bs.ar(end) |
| inventory_turnover | 存货周转率 | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(open) | 498.00 | 465.13 | 缺 is.cogs(cur) | 257.57 | 20.98 | 缺 bs.inventory(end) |
| dio_days | 存货周转天数 | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(end) | 缺 bs.inventory(open) | 1 | 1 | 缺 is.cogs(cur) | 1 | 17 | 缺 bs.inventory(end) |
| ap_turnover | 应付账款周转率 | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 is.cogs(cur) | 20.53 | 2.23 | 缺 bs.ap(end) |
| dpo_days | 应付账款周转天数 | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 bs.ap(end) | 缺 is.cogs(cur) | 18 | 162 | 缺 bs.ap(end) |
| current_asset_turnover | 流动资产周转率 | 缺 bs.current_assets(open) | 1.39 | 1.30 | 1.33 | 缺 bs.current_assets(open) | 1.30 | 1.40 | 1.59 | 缺 bs.current_assets(open) | 3.06 | 3.58 | 缺 bs.current_assets(end) | 3.43 | 0.82 | 缺 bs.current_assets(end) |
| fixed_asset_turnover | 固定资产周转率 | 缺 bs.fixed_assets(open) | 5.22 | 5.72 | 5.34 | 缺 bs.fixed_assets(open) | 5.21 | 5.13 | 4.21 | 缺 bs.fixed_assets(open) | 5.33 | 5.06 | 缺 bs.fixed_assets(end) | 12.80 | 1.43 | 缺 bs.fixed_assets(end) |
| total_asset_turnover | 总资产周转率 | 缺 bs.total_assets(open) | 0.45 | 0.48 | 0.50 | 缺 bs.total_assets(open) | 0.54 | 0.56 | 0.55 | 缺 bs.total_assets(open) | 1.17 | 1.19 | 缺 bs.total_assets(end) | 1.79 | 0.34 | 缺 bs.total_assets(end) |
| gross_margin | 毛利率 | 45.1% | 44.6% | 41.3% | 36.8% | 36.7% | 37.7% | 40.0% | 39.8% | 10.5% | 10.7% | 10.5% | 缺 is.cogs(cur) | 9.1% | 13.7% | 57.8% |
| operating_margin | 营业利润率 | 15.1% | 17.9% | 12.5% | 8.2% | 11.6% | 12.0% | 14.1% | 4.9% | -2.4% | -2.0% | -2.2% | 缺 is.operating_profit(cur) | 缺 is.operating_profit(cur) | 4.6% | 32.9% |
| net_margin | 净利率 | 21.3% | 27.5% | 20.0% | 5.5% | 7.5% | 7.6% | 12.6% | 10.0% | -3.8% | -3.4% | -3.6% | 1.4% | 3.2% | 3.6% | 28.3% |
| roe | 净资产收益率 | 缺 bs.equity(open) | 19.0% | 14.7% | 4.4% | 缺 bs.equity(open) | 6.4% | 11.6% | 9.3% | 缺 bs.equity(open) | -10.1% | -11.6% | 缺 bs.equity(end) | 11.2% | 2.4% | 缺 bs.equity(end) |
| total_assets_return | 总资产报酬率 | 缺 bs.total_assets(open) | 14.6% | 11.8% | 4.7% | 缺 bs.total_assets(open) | 5.8% | 9.6% | 7.6% | 缺 bs.total_assets(open) | -1.5% | -1.9% | 缺 is.total_profit(cur) | 缺 is.interest_exp(cur) | 1.8% | 缺 is.interest_exp(cur) |
| roce | 总资本收益率 | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 is.interest_exp(cur) | 缺 is.interest_exp(cur) | 1.9% | 缺 is.interest_exp(cur) |
| cost_expense_profit_ratio | 成本费用利润率 | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | 缺 is.fin_exp(cur) | -3.6% | -3.0% | -3.2% | 缺 is.total_profit(cur) | 3.5% | 5.0% | 49.8% |
| equity_multiplier | 权益乘数 | 缺 bs.total_assets(open) | 1.54 | 1.54 | 1.58 | 缺 bs.total_assets(open) | 1.59 | 1.64 | 1.69 | 缺 bs.total_assets(open) | 2.53 | 2.71 | 缺 bs.total_assets(end) | 1.98 | 1.94 | 缺 bs.total_assets(end) |
| ebitda | EBITDA | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.total_profit(cur) | 缺 is.interest_exp(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| adjusted_ebitda | 调整后 EBITDA | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.total_profit(cur) | 缺 is.interest_exp(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| ebitda_margin | EBITDA 利润率 | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.dep_amort(cur) | 缺 is.total_profit(cur) | 缺 is.interest_exp(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| revenue_growth | 营业收入增长率 | 2234.3% | 35.3% | 40.7% | 18.9% | 2726.9% | 8.3% | 5.9% | 2.7% | 缺 is.revenue(prev_yoy) | 26.8% | 16.4% | 缺 is.revenue(prev_yoy) | 18.8% | 6.1% | 11.0% |
| net_profit_growth | 净利润增长率 | 163642.9% | 74.9% | 2.1% | -67.1% | 51532.3% | 8.8% | 76.6% | -18.9% | 缺 is.net_profit(prev_yoy) | 13.4% | 22.6% | 缺 is.net_profit(prev_yoy) | -2.8% | 12.3% | 3.4% |
| operating_profit_growth | 营业利润增长率 | 5568.7% | 60.2% | -1.9% | -22.3% | 4807.1% | 13.0% | 24.3% | -64.4% | 缺 is.operating_profit(prev_yoy) | 4.1% | 30.5% | 缺 is.operating_profit(cur) | 缺 is.operating_profit(cur) | 12.1% | 11.9% |
| total_asset_growth | 总资产增长率 | 缺 bs.total_assets(open) | 36.0% | 28.7% | 0.3% | 缺 bs.total_assets(open) | 0.7% | 2.2% | 5.8% | 缺 bs.total_assets(open) | 5.6% | 22.0% | 缺 bs.total_assets(end) | 5.7% | -1.2% | 缺 bs.total_assets(end) |
| equity_growth | 净资产增长率 | 缺 bs.equity(open) | 43.0% | 23.5% | -0.2% | 缺 bs.equity(open) | -1.0% | -2.1% | 3.7% | 缺 bs.equity(open) | -6.6% | 20.9% | 缺 bs.equity(end) | -5.1% | 1.2% | 缺 bs.equity(end) |
| cash_revenue_ratio | 现金收入比 | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 107.8% | 缺 cf.cash_from_sales(cur) |
| ocf_net_profit_ratio | 盈利现金比率 | 1.88 | 1.29 | 1.62 | 3.03 | 3.05 | 2.56 | 1.30 | 0.75 | -2.45 | -1.02 | -0.66 | 缺 cf.ocf(cur) | 2.72 | 1.27 | 缺 cf.ocf(cur) |
| free_cash_flow | 自由现金流 | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 缺 cf.capex(cur) | 4.8 亿 | -31.9 亿 | -37.3 亿 | 缺 cf.ocf(cur) | 118.9 亿 | 5.0 亿 | 缺 cf.ocf(cur) |
| cash_short_debt_ratio | 现金短期债务比 | 25.83 | 64.13 | 89.09 | 21.48 | 25.86 | 19.46 | 6.45 | 4.66 | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 bs.cash(end) | 2.29 | 0.79 | 缺 bs.cash(end) |
| debt_ebitda | 全部债务 / EBITDA | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 is.interest_exp(cur) | 缺 is.dep_amort(cur) | 缺 bs.short_debt(end) |

| **可计算指标数** | | **14/40** | **22/40** | **22/40** | **22/40** | **14/40** | **22/40** | **22/40** | **22/40** | **13/40** | **26/40** | **26/40** | **1/40** | **29/40** | **35/40** | **7/40** |
