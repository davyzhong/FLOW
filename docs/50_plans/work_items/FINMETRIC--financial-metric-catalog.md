---
doc_id: FLOW-WI-FINMETRIC-001
title: 财务指标目录（驾驶舱前置）
doc_type: work-item
status: active
version: 1.3
created_at: 2026-09-30
updated_at: 2026-10-11
owner: FLOW
depends_on: [FLOW-WI-COCKPIT-CFO-001]
acceptance_refs: [FLOW-PLAN-COCKPIT-IMPL-20260930]
applies_to: services/api
decision_refs: [D052, D053, D055]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
source_refs:
  - docs/superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md
  - docs/05_design/2026-09-29-cfo-cockpit-design.md
  - docs/50_plans/work_items/COCKPIT--cfo-dashboard-implementation.md
confidentiality: project-internal
---

# 财务指标目录（驾驶舱前置）

## 目标

补齐 API 侧的**财务指标目录**，使 CFO 驾驶舱的 8 个模块能在真实数据上成立，而不是靠 unavailable 占位。

## 为什么这是驾驶舱的真实阻塞（2026-09-30 实测）

驾驶舱要画 ROE / 资产负债率 / CCC / DIO / DPO / 利息保障倍数 / EBITDA 率 / 净利率 /
周转率。实测 API 侧现状：

| 事实 | 证据 |
|---|---|
| 指标引擎只有 15 个指标 | `config/metrics/flow_v1_metrics.yaml` |
| 其中财务类**只有 1 个**（`dso`） | 同上；其余是 `orders`/`revenue`/`gross_margin`/`fulfillment_cost_rate`/`ar_balance`/`operating_cash_flow` 等物流口径 |
| `MetricAggregation` 是封闭 3 值枚举 | `services/api/src/flow_api/metrics/models.py:7` — `sum` / `closing_balance` / `ratio` |
| `MetricUnit` 是封闭 6 值枚举 | 同文件 `:9` — `order`/`unit`/`CNY`/`CNY/order`/`ratio`/`day`；**没有 `%`、倍（x）、百分点（pp）** |
| `MetricSpec` 是 `extra="forbid"` | 同文件 `:19` — 新字段必须先改模型 |
| Dashboard 的 `MetricCard.unit` 同样是封闭枚举 | `services/api/src/flow_api/dashboard/models.py:136` |
| 公式是硬编码 if 链 | `services/api/src/flow_api/metrics/formulas.py:38-45` — `ratio`/`subtract`/`closing_ar_over_...` 逐个 if |
| `accounting_foundation_v1.yaml` 有 167 科目 / 48 准则但**无 metrics** | 该文件是会计科目基础，不是指标目录 |

**结论**：这不是"补几条 YAML"。财务指标需要扩展指标引擎的**类型系统**（单位枚举、
聚合枚举、公式注册表），再落目录，然后驾驶舱才有数据可画。批次 C 依赖本工作包。

## 范围

### F2 来源裁决（2026-10-11）

只读盘点发现本项目已有 `config/metrics/metric_dictionary_v1_1.yaml`，含 50 条
`metrics_general` 指标定义；包括利息保障倍数、EBITDA/EBITDA 利润率、ROE、资产周转、
DSO/DIO/DPO、CCC、流动/速动/现金比率等。本包不得再复制一份平行指标定义或公式。

已有大麦覆盖生成器 `scripts/build_damai_metric_coverage.py` 与产物
`config/metrics/damai_demo_metric_coverage_v1.yaml`，但生成器读取旧研究草案
`docs/knowledge-base/02_research/synthesis/指标库初始数据集_v0_草案.yaml`，而非当前有效
字典。其当前报告为 FY2025 37/40、FY2026 40/40。F2 的执行范围修订为：以 v1.1 作为公式、
口径和定义事实源；修正覆盖生成器及必要测试，使大麦覆盖矩阵从有效字典生成；复用
`config/statements/item_alias_map_v1.yaml#damai_syn`、现有 Decimal 公式 AST 引擎和映射
校验；验证重点指标的勾稽恒等式，并对缺失输入保留 typed unavailable，不复制字典内容。

大麦演示财报包含利息费用行，且 FY2025/FY2026 有期初/期末资产、权益、应收、存货和应付
余额；但发行版注释声明利息费用是财务费用的 65% 合成子项，折旧按固定资产年率 10% 估算。
因此相关比率可以用于产品功能验证，但产物和来源链必须标记 synthetic，不得表述为独立
总账/真实企业财务证据。大麦事实输入是合并财报行项目，并非逐科目试算平衡表；与会计
科目的连接通过规范 statement item 映射表达，汇总行不强行伪映射到单个总账科目。

### 1. 指标引擎类型扩展（前置）

| 改动 | 内容 | 理由 |
|---|---|---|
| `MetricUnit` 增 `%` / `x`（倍） / `pp`（百分点） | 百分比、倍数、百分点是财务标准单位 | 驾驶舱 KPI 大量使用；`day` 已有 |
| `MetricAggregation` 增 `average`（期初期末平均） | ROE/ROA/周转率必须用平均口径（设计文档 §6.3 修正项） | 用期末值算 ROE 会误判 |
| 公式注册表化 | 把 `formulas.py` 的 if 链改为 `{formula_name: fn}` 注册表 | 新增 10+ 财务公式时不改核心逻辑 |
| 守恒/勾稽断言 | 每个财务指标声明其恒等式（如 `资产 = 负债 + 权益`） | 财务指标的「可复算」铁律（设计文档 §2.2） |

### 2. 财务指标集（按驾驶舱模块）

| 模块 | 指标 | 口径要点 |
|---|---|---|
| 盈利能力 | 毛利率、营业利润率、净利率、EBITDA 率、ROA、ROE | ROA/ROE 用**平均**资产/权益 |
| 盈利能力 | 总资产周转率、权益乘数 | 杜邦三因子 |
| 营运资金 | DSO、DIO、DPO、CCC | CCC = DSO + DIO − DPO（恒等式需断言） |
| 资产负债 | 资产负债率、流动比率、速动比率、现金比率、权益比率 | 点时值（`closing_balance`） |
| 偿债 | 利息保障倍数、净负债/EBITDA | 流量/存量的复合口径 |
| 费用 | 销售/管理/研发/财务费用、期间费用、期间费用率 | 需利润表明细科目映射 |
| 现金流 | 经营/投资/筹资净额、自由现金流率、净现比、收现比 | 现金流量表科目映射 |

**首版规模**：约 28 个财务指标（覆盖 8 个模块），不含预算/合并/多币种（内部期或批次 D）。

### 3. 驾驶舱投影接入

- `CockpitProjectionService` 从财务指标目录取数，替换当前「环比/行业分位永久 unavailable」；
- 每个新增指标同样带 `snapshot_id`（可追溯铁律）、`polarity`、`control_status`（管控线）。

## 不做什么

- ❌ 预算/目标/预测指标（内部期，依赖 L2 预算层）
- ❌ 多法人合并与抵销指标（批次 C5 降级态）
- ❌ 多币种折算（批次 D）
- ❌ 自动因果归因（超出 D001 边界）
- ❌ 不解除 C 级门禁

## 批次与验收门禁

| 批次 | 范围 | 门禁 |
|---|---|---|
| **F1** | 指标引擎类型扩展（单位/聚合/公式注册表/守恒断言）+ 回归 | mypy · ruff · 既有 metrics 测试零回归 · 新增引擎单测 |
| **F2** | 复用有效指标字典，更新大麦覆盖生成器与覆盖/勾稽测试（盈利能力 + 偿债 + 营运） | 生成源为 v1.1；重点指标勾稽通过；标准 statement item 映射覆盖明确；缺失不补零；synthetic 来源可追溯 |
| **F3** | 财务指标目录 YAML（费用 + 现金流，约 12 个）+ 计算测试 | 同上 |
| **F4** | 驾驶舱投影接入（环比/行业分位逐步解锁）+ 契约更新 | cockpit 测试全绿 · contracts-check · 同 SHA CI 17/17 |

每批门禁与驾驶舱批次 A 同级（mypy / lint / vitest / pytest / build / contracts / docs / CI）。

### F2 实施记录（2026-10-11）

覆盖生成器现读取有效指标字典 v1.1 的 50 条通用定义，产物记录字典 ID、来源路径及 SHA-256；FY2025 覆盖 42/50、FY2026 覆盖 45/50。保留 synthetic 来源说明，并补充 CCC、杜邦 ROE、期间费用率公式勾稽测试。API schema/OpenAPI/TS contract 与指标库页面同步展示定义来源。提交 `385fedf7` 的准确 SHA CI run `38151001948` 为 16/17；integration 仅因 missing 断言不接受 `nopat` 公式输入标识符而失败，相关测试集 270 passed。现正修正断言；F2 尚未关闭。

### F1 完成记录（2026-10-11）

指标类型扩展、公式注册表和可选勾稽字段已实现；未显式声明的 `conservation_law` 不进入既有目录指纹，显式值参与新目录哈希。增加回归测试，指标测试 70/70、mypy 19 文件通过。因固定演示月份与真实时钟的差异导致第一次 CI 14/17；经时钟依赖注入与专用 E2E 冻结时钟修复后，提交 `11129263` 准确 SHA `11129263110d296f33c48b6cb94237a6fcedfd13` 的 CI run `38147756845` 17/17 success。故 F1 标记完成，队首进入 F2。

## 未决问题

| # | 问题 | 阻塞 | 建议 |
|---|---|---|---|
| Q1 | 财务指标的科目映射基准：用 `accounting_foundation_v1` 的 167 科目，还是先只映射可从财报直接取得的科目？ | F2 | 先映射财报可直接取得者，其余标 `not_mapped` 并在驾驶舱显式 unavailable（不补零） |
| Q2 | 平均口径的期初值从哪来？需历史快照支撑 | F1 | 用 `MetricSnapshot` 历史；不足时显式 `insufficient_history`，不静默用期末值 |
| Q3 | 利息保障倍数需要利息费用科目——大麦演示数据是否具备？ | F2 | 需核实；不具备则该指标在演示期显式 unavailable |
| Q4 | 行业参考包基准（Q4 三基准之一）何时接入？ | F4 | 依赖 16 行业参考包建设，可与 F4 并行或后置 |

## 依赖关系

```text
FINMETRIC（本工作包）──→ COCKPIT 批次 C（8 个模块页）
                          │
                          └──→ COCKPIT 批次 D（结论条自动生成 / 问数）
```

## 关联文档

- 实施方案：[2026-09-30-cfo-cockpit-implementation-plan.md](../../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md)
- 驾驶舱工作包：[COCKPIT--cfo-dashboard-implementation.md](COCKPIT--cfo-dashboard-implementation.md)
- 设计文档：[2026-09-29-cfo-cockpit-design.md](../../05_design/2026-09-29-cfo-cockpit-design.md)
- 指标引擎现状：`services/api/src/flow_api/metrics/models.py` / `formulas.py` / `config/metrics/flow_v1_metrics.yaml`
