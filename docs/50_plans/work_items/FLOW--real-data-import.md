---
doc_id: FLOW-WI-REAL-DATA-IMPORT-20261028-001
title: 真实数据导入（单机原型从演示走向可用）
doc_type: work-item
status: active
version: 1.5
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

### R5 九页驾驶舱全量接线（已交付，本地全绿）

**目标**：导入账套经归一化管线升格为治理发布链（AnalysisRun→MetricSnapshot），九页驾驶舱自动以导入数据为活跃源；不直接改 dashboard service 伪装接通，不重复造业务事实源。

**交付清单（与设计一致，含实施中的两处契约修正）**：

- `importer/publish_chain.py`：CanonicalPackage 桥接（五管理科目聚合、`period YYYY-MM` 直通、单主体）→ `load_canonical_package` 直写 canonical → 勾稽写 ReconciliationResult → `IntakeService.publish_import` 发布门禁 → `trial_balance_v1` 目录逐期间快照 → 最新期间 AnalysisRun；`chain_receipt`/`is_active_source`/`withdraw_dataset_chain`（子表先行，Fact* 行先于 SourceRecord 删，共享维度不删）。
- 实施修正①：canonical 载荷要求 `record_id` 为 UUID——采用 uuid5 确定性生成（同数据集重复发布同 id）。
- 实施修正②：playbook 输入模型 `source_record_count` 从 `gt=0` 放宽为 `ge=0`（FulfillmentTotals/ProfitBridgeInput/ArCashInput），`_ar_input` 的 DSO 计算加零分母守卫——无经营行的导入账套走 playbook 既有 degraded 分支而非硬崩；flow_v1 回归全绿（metrics 70 + analysis/dashboard 集成 78+28）。
- 引擎最小通用化：`MetricSpec.financial_account` 可选声明 + `metric_catalog_hash` 对 None pop（**flow_v1 指纹经 stash 对比确认不变**：4214ae85339e）+ calculator 目录驱动财务绑定（显式声明优先、内置兜底）+ operating/AR/dso/budget 块 specs 成员守卫 + `direct_codes` 固定序与目录基座并集。
- `config/metrics/trial_balance_v1_metrics.yaml`：七指标与 derive_metrics 同码同式。
- 路由：`GET /dataset/{id}/chain`、`POST /dataset/{id}/publish`（勾稽不平 422）、DELETE 级联下线（`chain_withdrawn`）；契约已再生成。
- 前端：向导新增「发布到驾驶舱」步骤（published + is_active_source + 跳转链接）；vitest 213 全绿、tsc/build 通过。

**验收结果（本地）**：

- 集成测试 4/4（`tests/integration/test_importer_publish_chain.py`，进 CI core 分片）：口径等价（逐期间快照==独立复算；流量指标全期快照和==直读合计）、治理切换（总览活跃源==最新导入快照，revenue 卡出真数 7000，orders/gross_margin/operating_cash_flow 如实 unavailable；两期数据凑不满 12 月趋势→degraded 属设计内降级）、幂等发布、勾稽不平 422 且零残留、删除级联后 get_latest 回到基线 run。
- 六门禁：plan_views / m1 / m6 / links / kb_manifest / contracts-check 全 PASS（coverage_validator 属 K3 知识批次门禁，本轮未动知识库不适用）。
- CI：准确 SHA 待推送后核对。

**已知边界**：CI 分片映射只跑 `tests/{integration,investigation,copilot,api}`——既有 `tests/importer` 套件（R1–R4 的 25 项）不在 CI 分片内，属本地回归套件（不改 CI 配置，此处如实登记）。

**不做什么**：不改 dashboard service 与 CARD_DEFINITIONS；不做利润表/流水模板接线（后续迭代）；不做自动科目映射 AI；不动大麦演示链路数据。

## 不做什么（工作包总边界）

- ❌ 多币种、合并抵销、预算编制（后续迭代）
- ❌ 自动科目映射 AI（第一期用固定模板列名，用户按模板填数）
- ❌ 连接常驻 PostgreSQL/外部数据库（保持单机 SQLite 边界）
- ❌ 改动大麦演示数据链路（隔离共存）

## 边界与红线

- 不触碰 ObsidianWiki、不恢复 K3（用户已裁决挂起）。
- 不删除文件、不改 CI 配置、密钥不进代码。
- 每批次：门禁全绿 → 提交 → 立即推送。

## 依赖关系

R1 → R2 → R3 → R4 → R5（严格串行；R5 九页接线已交付）

## 关联文档

- 上游原型：[FLOW--single-machine-visual-prototype.md](FLOW--single-machine-visual-prototype.md)（completed，回归基线）
- 唯一队列：[CURRENT_ROADMAP](../CURRENT_ROADMAP.md)
