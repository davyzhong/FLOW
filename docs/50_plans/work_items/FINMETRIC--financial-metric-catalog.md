---
doc_id: FLOW-WI-FINMETRIC-001
title: 财务指标目录（驾驶舱前置）
doc_type: work-item
status: active
version: 1.0
created_at: 2026-09-30
updated_at: 2026-09-30
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
| **F2** | 财务指标目录 YAML（盈利能力 + 偿债 + 营运，约 16 个）+ 计算测试 | 每个指标有守恒/勾稽测试；与 `accounting_foundation_v1` 科目映射完整 |
| **F3** | 财务指标目录 YAML（费用 + 现金流，约 12 个）+ 计算测试 | 同上 |
| **F4** | 驾驶舱投影接入（环比/行业分位逐步解锁）+ 契约更新 | cockpit 测试全绿 · contracts-check · 同 SHA CI 17/17 |

每批门禁与驾驶舱批次 A 同级（mypy / lint / vitest / pytest / build / contracts / docs / CI）。

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
