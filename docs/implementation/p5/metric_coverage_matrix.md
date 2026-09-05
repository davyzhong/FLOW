# P5 指标覆盖率矩阵：指标库 v0 通用指标 × 样本快照

- 生成：`scripts/p5_query_facts.py`，2026-09-06T06:05:51
- 口径注意：avg 为（期末+期初）/2、prior 为上年同期列；单季数据未年化；腾讯一般及行政开支含研发（口径差异已标注）；绝对额指标已换算为亿元。

| 指标 | 名称 | jd_logistics_2618 2026Q1 | jd_logistics_2618 FY2025 | sf_002352 2026Q1 | tencent_0700 2Q2026 |
|---|---|---|---|---|---|
| current_ratio | 流动比率 | 缺 bs.current_assets(end) | 缺 bs.current_assets(end) | 1.28 | 缺 bs.current_assets(end) |
| quick_ratio | 速动比率 | 缺 bs.current_assets(end) | 缺 bs.current_assets(end) | 1.23 | 缺 bs.current_assets(end) |
| cash_ratio | 现金比率 | 缺 bs.cash(end) | 缺 bs.cash(end) | 0.24 | 缺 bs.cash(end) |
| ocf_current_liab_ratio | 现金流量比率 | 缺 cf.ocf(cur) | 缺 cf.ocf(cur) | 0.05 | 缺 cf.ocf(cur) |
| debt_asset_ratio | 资产负债率 | 缺 bs.total_liab(end) | 缺 bs.total_liab(end) | 47.8% | 缺 bs.total_liab(end) |
| debt_equity_ratio | 产权比率 | 缺 bs.total_liab(end) | 缺 bs.total_liab(end) | 0.92 | 缺 bs.total_liab(end) |
| interest_coverage | 利息保障倍数 | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 9.84 | 缺 is.interest_exp(cur) |
| ebitda_interest_coverage | EBITDA 利息倍数 | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| total_debt_capitalization | 全部债务资本化比率 | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 29.7% | 缺 bs.short_debt(end) |
| long_debt_capitalization | 长期债务资本化比率 | 缺 bs.long_debt(end) | 缺 bs.long_debt(end) | 18.7% | 缺 bs.long_debt(end) |
| ar_turnover | 应收账款周转率 | 缺 bs.ar(end) | 缺 bs.ar(end) | 2.49 | 缺 bs.ar(end) |
| dso_days | 应收账款周转天数 | 缺 bs.ar(end) | 缺 bs.ar(end) | 145 | 缺 bs.ar(end) |
| inventory_turnover | 存货周转率 | 缺 is.cogs(cur) | 缺 is.cogs(cur) | 20.98 | 缺 bs.inventory(end) |
| dio_days | 存货周转天数 | 缺 is.cogs(cur) | 缺 is.cogs(cur) | 17 | 缺 bs.inventory(end) |
| ap_turnover | 应付账款周转率 | 缺 is.cogs(cur) | 缺 is.cogs(cur) | 2.23 | 缺 bs.ap(end) |
| dpo_days | 应付账款周转天数 | 缺 is.cogs(cur) | 缺 is.cogs(cur) | 162 | 缺 bs.ap(end) |
| current_asset_turnover | 流动资产周转率 | 缺 bs.current_assets(end) | 缺 bs.current_assets(end) | 0.82 | 缺 bs.current_assets(end) |
| fixed_asset_turnover | 固定资产周转率 | 缺 bs.fixed_assets(end) | 缺 bs.fixed_assets(end) | 1.43 | 缺 bs.fixed_assets(end) |
| total_asset_turnover | 总资产周转率 | 缺 bs.total_assets(end) | 缺 bs.total_assets(end) | 0.34 | 缺 bs.total_assets(end) |
| gross_margin | 毛利率 | 缺 is.cogs(cur) | 缺 is.cogs(cur) | 13.7% | 57.8% |
| operating_margin | 营业利润率 | 缺 is.operating_profit(cur) | 缺 is.operating_profit(cur) | 4.6% | 32.9% |
| net_margin | 净利率 | 1.4% | 3.2% | 3.6% | 28.3% |
| roe | 净资产收益率 | 缺 bs.equity(end) | 缺 bs.equity(end) | 2.4% | 缺 bs.equity(end) |
| total_assets_return | 总资产报酬率 | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 1.8% | 缺 is.interest_exp(cur) |
| roce | 总资本收益率 | 缺 is.interest_exp(cur) | 缺 is.interest_exp(cur) | 1.9% | 缺 is.interest_exp(cur) |
| cost_expense_profit_ratio | 成本费用利润率 | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 5.0% | 49.8% |
| equity_multiplier | 权益乘数 | 缺 bs.total_assets(end) | 缺 bs.total_assets(end) | 1.94 | 缺 bs.total_assets(end) |
| ebitda | EBITDA | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| adjusted_ebitda | 调整后 EBITDA | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| ebitda_margin | EBITDA 利润率 | 缺 is.total_profit(cur) | 缺 is.total_profit(cur) | 缺 is.dep_amort(cur) | 缺 is.interest_exp(cur) |
| revenue_growth | 营业收入增长率 | 缺 is.revenue(prev_yoy) | 缺 is.revenue(prev_yoy) | 6.1% | 11.0% |
| net_profit_growth | 净利润增长率 | 缺 is.net_profit(prev_yoy) | 缺 is.net_profit(prev_yoy) | 12.3% | 3.4% |
| operating_profit_growth | 营业利润增长率 | 缺 is.operating_profit(cur) | 缺 is.operating_profit(cur) | 12.1% | 11.9% |
| total_asset_growth | 总资产增长率 | 缺 bs.total_assets(end) | 缺 bs.total_assets(end) | -1.2% | 缺 bs.total_assets(end) |
| equity_growth | 净资产增长率 | 缺 bs.equity(end) | 缺 bs.equity(end) | 1.2% | 缺 bs.equity(end) |
| cash_revenue_ratio | 现金收入比 | 缺 cf.cash_from_sales(cur) | 缺 cf.cash_from_sales(cur) | 107.8% | 缺 cf.cash_from_sales(cur) |
| ocf_net_profit_ratio | 盈利现金比率 | 缺 cf.ocf(cur) | 缺 cf.ocf(cur) | 1.27 | 缺 cf.ocf(cur) |
| free_cash_flow | 自由现金流 | 缺 cf.ocf(cur) | 缺 cf.ocf(cur) | 5.0 亿 | 缺 cf.ocf(cur) |
| cash_short_debt_ratio | 现金短期债务比 | 缺 bs.cash(end) | 缺 bs.cash(end) | 0.79 | 缺 bs.cash(end) |
| debt_ebitda | 全部债务 / EBITDA | 缺 bs.short_debt(end) | 缺 bs.short_debt(end) | 缺 is.dep_amort(cur) | 缺 bs.short_debt(end) |

| **可计算指标数** | | **1/40** | **1/40** | **35/40** | **7/40** |
