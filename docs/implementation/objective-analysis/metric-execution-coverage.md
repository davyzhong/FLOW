# 指标执行覆盖清单（C02）

- 生成：2026-09-06，由 `scripts/generate_metric_coverage_doc.py` 机械生成
- 总数：55；engine（指标引擎）：15；facts（事实 AST）：40；narrative（暂不执行）：0
- 对等性门禁：`tests/metrics/test_dictionary_execution_parity.py`（同指标同输入双路径一致 + 本清单防漂移）

| 指标 | 名称 | 集合 | 绑定 | 执行器 / 缺失原因 |
|---|---|---|---|---|
| `current_ratio` | 流动比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `quick_ratio` | 速动比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `cash_ratio` | 现金比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ocf_current_liab_ratio` | 现金流量比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `debt_asset_ratio` | 资产负债率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `debt_equity_ratio` | 产权比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `interest_coverage` | 利息保障倍数 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ebitda_interest_coverage` | EBITDA 利息倍数 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `total_debt_capitalization` | 全部债务资本化比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `long_debt_capitalization` | 长期债务资本化比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ar_turnover` | 应收账款周转率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `dso_days` | 应收账款周转天数 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `inventory_turnover` | 存货周转率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `dio_days` | 存货周转天数 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ap_turnover` | 应付账款周转率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `dpo_days` | 应付账款周转天数 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `current_asset_turnover` | 流动资产周转率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `fixed_asset_turnover` | 固定资产周转率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `total_asset_turnover` | 总资产周转率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `gross_margin` | 毛利率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `operating_margin` | 营业利润率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `net_margin` | 净利率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `roe` | 净资产收益率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `total_assets_return` | 总资产报酬率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `roce` | 总资本收益率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `cost_expense_profit_ratio` | 成本费用利润率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `equity_multiplier` | 权益乘数 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ebitda` | EBITDA | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `adjusted_ebitda` | 调整后 EBITDA | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ebitda_margin` | EBITDA 利润率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `revenue_growth` | 营业收入增长率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `net_profit_growth` | 净利润增长率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `operating_profit_growth` | 营业利润增长率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `total_asset_growth` | 总资产增长率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `equity_growth` | 净资产增长率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `cash_revenue_ratio` | 现金收入比 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `ocf_net_profit_ratio` | 盈利现金比率 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `free_cash_flow` | 自由现金流 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `cash_short_debt_ratio` | 现金短期债务比 | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `debt_ebitda` | 全部债务 / EBITDA | general | 事实 AST 执行 | 报表事实 AST 求值器（extraction/normalization 链） |
| `orders` | 订单量 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `fulfilled_units` | 履约件量 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `revenue` | 收入 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `revenue_per_order` | 单均收入 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `direct_cost` | 直接成本 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `cost_per_order` | 单均成本 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `gross_profit` | 毛利 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `gross_margin` | 毛利率（物流口径） | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `fulfillment_cost_rate` | 履约成本率 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `operating_profit` | 经营利润 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `ar_balance` | 应收余额 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `collection_rate` | 回款率 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `operating_cash_flow` | 经营现金流 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `cash_conversion` | 现金转换率 | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
| `dso` | 应收账款周转天数（T12 口径） | logistics | 引擎执行（库内目录） | metrics 引擎（库内目录 metric_catalog_document） |
