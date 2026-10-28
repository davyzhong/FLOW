---
doc_id: FLOW-WI-REAL-DATA-IMPORT-20261028-001
title: 真实数据导入（单机原型从演示走向可用）
doc_type: work-item
status: active
version: 1.4
created_at: 2026-10-28
updated_at: 2026-10-28
owner: FLOW
depends_on: [FLOW-WI-SINGLE-MACHINE-VISUAL-20261018-001]
acceptance_refs: []
applies_to: services/api, apps/web
decision_refs: [D055]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
source_refs:
  - docs/50_plans/work_items/FLOW--single-machine-visual-prototype.md
confidentiality: project-internal
---

# 真实数据导入（单机原型从演示走向可用）

## 目标

让单机原型从「只能看大麦 synthetic 演示数据」升级为「能导入用户自己的财务数据并生成驾驶舱」，补齐原型走向日常可用工具的最大缺口。

## 背景

D055 单机原型已交付：SQLite 单文件、一键启动、九页 CFO 驾驶舱、图表下钻、报告导出、备份恢复——但数据面只有大麦演示包（synthetic）。用户无法把自己的财务数据放进去看自己的经营分析。

K3 知识刷新已于 2026-10-28 由用户裁决挂起（批次 134–162 共 696 条审毕推送，剩余 7,813 条挂起），主线转产品功能；本工作包为用户裁决后的新队首。

## 范围与批次

### R1 导入模板与校验引擎（后端）

- 定义三张 Excel/CSV 导入模板：**科目余额表**（期初/期末余额）、**利润表**（月度或多期）、**银行/现金流流水**（可选，第一期可后置）。
- 模板字段采用通俗中文列名 + 内置示例行；提供模板下载（静态 xlsx 生成脚本）。
- 校验引擎（Decimal 全程）：借贷平衡（资产=负债+权益）、必填列、日期格式、重复期间检测；错误逐行报告（行号+原因），不合格整批拒绝。
- 单元测试：合法样例全通过、典型错误各一（不平衡/缺列/坏日期/重复期间）。

### R2 导入 API 与账套装载（后端）

- `POST /api/import/dataset`：上传文件 → 校验 → 写入 SQLite 独立 schema（与演示数据隔离，按 dataset_id 区分）。
- 导入成功后复用现有归一化/驾驶舱投影链路，生成指标快照与九页数据。
- 每数据集可整体删除重导（幂等）；演示数据与导入数据可切换查看。
- 隔离测试：不触碰常驻库，临时目录 SQLite。

### R3 导入向导 UI（前端）

- 新页面 `/data/import`（AppShell 内 + 导航登记 + e2e 清单更新）：模板下载 → 上传 → 校验报告（错误逐行展示）→ 成功后跳转驾驶舱（切换到该数据集）。
- 五态齐全（loading/empty/error/ready/degraded）；契约更新走 `make contracts-check`。

### R2b 导入数据概览驾驶舱（已完成）

- cockpit_view.py：五项 KPI（资产/负债/权益总计、本期净利润、资产负债率）+ 勾稽校验直接派生自科目余额表；GET /dataset/{id}/cockpit。
- 边界：只读校验视图，不写治理发布链；九页全量接线需要归一化管线设计（AnalysisRun→MetricSnapshot），列为独立后续阶段。

### R4 验收（已完成）

- HTTP 级端到端 4 项（TestClient）：模板下载 PK 魔数、上传→概览→cockpit→余额→删除全链、不平衡整批拒绝含行级定位、数据集清单——全过。
- 后端 21 项单测 + 4 项 e2e 全绿；ruff/mypy 干净；前端 213 项 vitest 全绿、typecheck/build 通过。
- 契约首轮失败（openapi.json 未随 importer 路由再生成），`make contracts` 修复后推送。
- 准确 SHA CI：main `3d6e1fb3`（run `40627155163`）全部 job success。

### R5 九页驾驶舱全量接线（设计定稿，待实施）

**目标**：导入账套经归一化管线升格为治理发布链（AnalysisRun→MetricSnapshot），九页驾驶舱自动以导入数据为活跃源；不直接改 dashboard service 伪装接通，不重复造业务事实源。

**管线设计（已按代码核实，main `b4756942`）**：

1. **桥接模块** `flow_api/importer/publish_chain.py`：从 `import_trial_balance_row`（Decimal 已校验）构造 `CanonicalPackage`（`data_contract/records.py`）——BatchRecord（分析窗口=数据集期间范围，场景码 ACTUAL/BUDGET）、PeriodRecord（`period` 列 `YYYY-MM` 与 `month_key` 格式直通）、单主体 OrganizationRecord、五个管理科目（TB_REVENUE/TB_EXPENSE/TB_ASSET/TB_LIABILITY/TB_EQUITY，按科目类别聚合）、FinancialActualRecord（期间×科目：损益贷方=收入、损益借方=费用、三类期末余额按方向）。`_validate_package` 仅校验存在行引用完整性，空维度元组合法。
2. **canonical 直写**：复用 `data_contract/persistence.load_canonical_package` 写 Period/Organization/ManagementAccount/FactFinancialActual + SourceRecord 溯源；`version.summary["batch"]` 由包元数据自动写入（`MetricSourceRepository.get_published_source` 的读取契约）。原始上传字节经 LocalObjectStore 留存为不可变源。
3. **质量与发布**：勾稽校验（资产−负债−权益=0）写入 ReconciliationResult；`IntakeService.publish_import` 复用既有发布门禁（无 blocking、勾稽全过、版本与批次置 published）。
4. **快照与运行**：`MetricSnapshotService.create_snapshot` 逐期间（新目录 `config/metrics/trial_balance_v1_metrics.yaml`，definition_set_id `flow.metrics.trial-balance.v1`）+ `AnalysisRunService.create_run`（最新期间快照，published）。
5. **引擎最小通用化** `metrics/calculator.py` + `metrics/models.py`：MetricSpec 增可选 `financial_account` 声明；计算器财务科目绑定 = 显式声明 or 既有 `_FINANCIAL_ACCOUNTS` 兜底（**flow_v1 目录与 YAML 不动 → definition hash/fingerprint 不变 → 大麦链零扰动**）；operating/AR/dso 块加 specs 成员守卫；`direct_codes` 改为固定序+目录声明财务基座按 specs 成员过滤；存量科目 `aggregation: closing_balance`，损益发生额 `flow`。
6. **指标口径对齐**：目录 7 指标与 `normalization.derive_metrics` 同码同式（revenue/total_expenses/net_profit/total_assets/total_liabilities/total_equity/debt_ratio）；**口径一致性验收 = 治理链快照值 == 直读派生值（等价测试）**。
7. **删除与活跃源语义**：dataset 删除级联下线其发布链（batch 名 `import-dataset-{dataset_id}` 定位；链行删除，原始字节留存不可变对象存储）；`DashboardSourceRepository.get_latest` 按期间最新优先，导入期间晚于大麦（2023-03）自然成为活跃源；数据集概览 API 报告 `active` 布尔，向导如实呈现。

**九页口径**：九页（/cockpit 总览+7 子模块 + /data/import）全部以导入数据集快照为数据契约；科目余额表可推导的指标出真数，不可推导（毛利率/DSO/经营现金流/客户维度）如实 unavailable 灰态（D054 不虚构）；趋势序列按数据集期间出线。

**验收**：
- 等价测试：TB 目录快照值 == derive_metrics 直读值（七项全等）。
- HTTP e2e：上传合法样例账套 → 发布链 → `/api/dashboard/overview` 返回导入 revenue 与新 snapshot_id → metrics 端点与快照等值 → 删除数据集 → 总览回落（无导入链时回落大麦演示或如实无源）。
- 回归：flow_v1 既有快照/指纹不受引擎通用化影响（大麦测试全绿）。
- 契约再生成（make contracts）；前端 vitest/typecheck/build；六门禁。

**不做什么**：不改 dashboard service 与 CARD_DEFINITIONS；不做利润表/流水模板接线（后续迭代）；不做自动科目映射 AI；不动大麦演示链路数据。

## 不做什么

- ❌ 多币种、合并抵销、预算编制（后续迭代）
- ❌ 自动科目映射 AI（第一期用固定模板列名，用户按模板填数）
- ❌ 连接常驻 PostgreSQL/外部数据库（保持单机 SQLite 边界）
- ❌ 改动大麦演示数据链路（隔离共存）

## 边界与红线

- 不触碰 ObsidianWiki、不恢复 K3（用户已裁决挂起）。
- 不删除文件、不改 CI 配置、密钥不进代码。
- 每批次：门禁全绿 → 提交 → 立即推送。

## 依赖关系

R1 → R2 → R3 → R4（严格串行）

## 关联文档

- 上游原型：[FLOW--single-machine-visual-prototype.md](FLOW--single-machine-visual-prototype.md)（completed，回归基线）
- 唯一队列：[CURRENT_ROADMAP](../CURRENT_ROADMAP.md)
