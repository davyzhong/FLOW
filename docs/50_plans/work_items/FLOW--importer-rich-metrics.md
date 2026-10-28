---
doc_id: FLOW-WI-IMPORTER-RICH-METRICS-20261028-001
title: 导入账套指标补厚（科目级映射 + 利润表/银行流水接线）
doc_type: work-item
status: completed
version: 1.1
created_at: 2026-10-28
updated_at: 2026-10-28
owner: FLOW
depends_on: [FLOW-WI-REAL-DATA-IMPORT-20261028-001]
acceptance_refs: []
applies_to: services/api, apps/web, config
decision_refs: [D055]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
source_refs:
  - docs/50_plans/work_items/FLOW--real-data-import.md
confidentiality: project-internal
---

# 导入账套指标补厚（科目级映射 + 利润表/银行流水接线）

## 目标

用户指令（2026-10-28）：沿「利润表+银行流水模板接线（把九页能出的指标再补厚）、导入账套的科目级映射（突破类别聚合）」继续。R5 后导入账套只出 7 项类别级指标；本工作包把九页能亮起来的指标扩展到 **资产负债结构、损益结构与毛利、现金流量口径** 三组。

## 设计（已按 main `7400c44f` 代码核实）

**总原则（延续 R5 红线）**：全部新指标走 R5 已建的治理发布链（CanonicalPackage→发布门禁→快照→AnalysisRun）；引擎零改动（R5 的 `MetricSpec.financial_account` 目录驱动绑定已支撑全部新基座）；不改 dashboard service；口径不虚构——数据缺席指标缺席。

### M1 科目级映射（余额表结构化，突破类别聚合）

- 新配置 `config/importer/account_mapping_v1.yaml`：科目编码前缀 → 明细管理科目组（货币资金 TB_CASH=1001/1002/1012/1021/1031、应收账款 TB_AR=1122/1123、存货 TB_INVENTORY=1403/1405/1406/1411、固定资产净额 TB_FIXED_ASSET=1601/1602/1603、应付账款 TB_AP=2202/2203、应付职工薪酬 TB_PAYROLL=2211、短期借款 TB_LOAN=2001/2011、实收资本 TB_PAID_IN=3001），组内**方向净额**=Σ(匹配方向余额)−Σ(反向余额)（固定资产净额=借向原值−贷向折旧/减值）。
- 未命中科目**回落类别聚合**（R5 的五 TB_* 合计不变，等价测试基线不动）；一个科目只归一组（前缀表顺序优先）。
- 新指标（closing_balance/balance）：`cash`、`receivables`、`inventory`、`fixed_assets`、`accounts_payable`。
- 收益：资产负债页从「三个总数」变为「总数+结构明细」。

### M2 利润表接线（损益结构与毛利）

- 利润表「项目」列（自由文本）经**标准化映射字典**（去空白/去「减：加：其中：」前缀后精确匹配）→ IS_* 管理科目：营业收入/营业成本/税金及附加/销售费用/管理费用/研发费用/财务费用/营业利润/营业外收入/营业外支出/利润总额/所得税费用/净利润；未匹配项忽略并在回执列出。
- 新指标：`operating_cost`（IS_COST）、`gross_profit`=subtract(revenue, operating_cost)、`gross_margin`=ratio(gross_profit, revenue)（dashboard 毛利率卡随之亮起）、`selling_expense`/`admin_expense`/`rd_expense`/`finance_expense`（四项期间费用分项）。
- **口径声明**：revenue 仍=科目余额表损益贷方发生额合计（不改绑定，等价基线零扰动）；毛利率分母即该口径，business_definition 显式写明。损益明细（成本/费用分项）只来自利润表——科目级映射只做资产负债结构，**不双源**。
- **新勾稽门禁**：期间交集内 |TB 净利润（Σ损益贷−Σ损益借）− IS 净利润| > 0.01 → ReconciliationResult failed → 发布拒绝（两表不一致的账套不进治理链）。
- 利润表期间与余额表期间取并集入库（缺 TB 事实的期间部分指标如实缺席）。

### M3 银行流水接线（现金流量口径）

- 新模板「银行流水」：交易日期（YYYY-MM-DD）/摘要/收入金额/支出金额/账户余额；读取、校验（金额 Decimal、日期格式、**行内余额连续性**：余额[i]=余额[i-1]+收入−支出±0.01，首行自由锚定，整批拒绝制）。
- 存储 `import_bank_statement_row`；上传链路 import_workbook 扩展第三张可选表（余额表仍为锚定必选）。
- 桥接按期间聚合：`cash_inflow`、`cash_outflow`（sum/flow）、`net_cash_flow`=subtract(两者)。
- **口径声明**：现金收付实现制口径，**不绑** dashboard 的 `operating_cash_flow`（权责发生制 OCF），标签如实「现金口径」。
- 与 TB 货币资金变动的交叉核对 v1 不做（口径差异源多：现金/支付宝/微信账户），登记为后续候选。

### 指标目录

全部新指标并入 `config/metrics/trial_balance_v1_metrics.yaml`（文件名与 definition_set_id 不变，只追加条目；既有 7 指标逐字节不动）。流水模板链接补进导入向导；上传回执增加流水行数。

## 交付记录（2026-10-28，M1–M3 全部交付）

- **M1**（`082f2f94`）：`config/importer/account_mapping_v1.yaml`（5 组前缀映射）+ `importer/account_mapping.py`（前缀优先/方向净额/逐期命中登记）+ 桥接明细组事实 + 目录 5 指标（cash/receivables/inventory/fixed_assets/accounts_payable）；实施修正：**空组不写 0 金额事实**（缺席≠零——0 会冒充真实余额并让环比 variance_pct 0/0 硬崩）。映射单测 6 项。
- **M2**（`f6a52467`）：`importer/income_items.py`（13 项标准化项目字典，去「减：/加：/其中：」前缀）+ 桥接 IS_* 事实与期间并集 + **净利润勾稽门禁**（income_statement_net_profit，TB Σ损益贷−Σ损益借 vs IS 净利润逐期对照，容差 0.01，不符发布拒绝且零残留）+ 目录 7 指标（operating_cost/gross_profit/gross_margin/selling/admin/rd/finance expense）；dashboard 毛利率卡随之出真数。
- **M3**（`715a2d6d`）：银行流水模板/读取/校验（**余额连续性**：余额[i]=余额[i-1]+收入−支出±0.01，整批拒绝）+ `import_bank_statement_row` 存储 + 上传链路第三张可选表 + 桥接现金口径事实 + 目录 3 指标（cash_inflow/cash_outflow/net_cash_flow，收付实现制，不绑权责 OCF）+ 向导模板链接与行数。
- 验收：集成测试 6/6（进 CI core 分片）+ importer 本地套件 28 项 + metrics 70 项 + 前端 213 项全绿；六门禁 PASS；目录终态 22 指标；准确 SHA CI 见路线图。

## 范围与批次（严格串行 M1→M2→M3，每批门禁全绿→提交→立即推送）

- **M1**：mapping 配置 + `importer/account_mapping.py` + 桥接扩展（明细组事实）+ 目录 5 新指标 + 等价回归（既有 4 项集成测试不变全绿）+ M1 单测（映射命中/回落/方向净额/前缀优先）。
- **M2**：IS 项目映射字典 + 桥接（IS_* 事实 + 并集期间 + 净利润勾稽）+ 目录 7 新指标 + M2 测试（映射/勾稽拒绝/毛利率与费用分项值/无利润表时新指标如实缺席）。
- **M3**：流水模板/读取/校验/存储/路由 + 桥接现金事实 + 目录 3 新指标 + M3 测试（连续性拒绝/现金三项值/无流水缺席）+ 向导模板链接。

## 验收

- 既有 4 项集成测试不变全绿（7 指标等价零扰动）；新增集成测试覆盖：M1 结构指标值、M2 毛利率/费用分项/勾稽拒绝、M3 现金三项/连续性拒绝。
- 目录新指标在无对应数据时全部缺席（不虚构）；dashboard 对应卡片/面板如实 unavailable。
- 前端 vitest/typecheck/build；六门禁（plan_views/m1/m6/links/kb_manifest/contracts-check）；准确 SHA CI 全绿。

## 不做什么

- ❌ 不动 dashboard service/CARD_DEFINITIONS；不动大麦链路与 flow_v1 目录。
- ❌ 不做自动科目映射 AI（固定前缀表 + 类别回落）。
- ❌ 现金流与权责 OCF 不混口径；营业外收入/税金等 IS 项目入库但不发指标（无驾驶舱归属）。
- ❌ 不动 ObsidianWiki/K3（挂起不变）。

## 依赖关系

M1 → M2 → M3（严格串行）；上游 FLOW-WI-REAL-DATA-IMPORT-20261028-001（completed）。

## 关联文档

- 上游工作包：[FLOW--real-data-import.md](FLOW--real-data-import.md)（completed，R5 管线即本包复用的发布链）
- 唯一队列：[CURRENT_ROADMAP](../CURRENT_ROADMAP.md)
