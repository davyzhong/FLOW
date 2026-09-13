---
doc_id: FLOW-SPEC-MODULE-BOUNDARIES-V1
title: 模块边界规格 V1（三层两模块）
doc_type: specification
status: review
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: services/api, apps/web, config/modules
---

# 模块边界规格 V1（三层两模块）

- 依据：战略重构设计 V1.1 §5（三层、两模块的目标结构）、§13 阶段 1；S01 计划 Task 7 / Task 8。
- 适用范围：`services/api` 后端模块划分、`apps/web` 前端入口、`config/modules/ownership_v1.yaml` 归属清单。
- 本规格固定「哪些模块存在、谁可以依赖谁、归属如何判定、违规如何失败」，不规定各模块内部业务逻辑。

## 1. 输入

- 现有代码树：`services/api/src/flow_api/` 下的 routes、statements、operations、workbench、publishing、intake、metrics、investigation 等包；
- 现有前端路由与导航：`apps/web/app/`、`apps/web/components/dashboard/workflow-nav.tsx`；
- 战略设计 V1.1 §5 的三层两模块结构与 D053 执行顺序决定。

## 2. 输出

- `GET /api/v1/modules`：只读能力发现端点，返回且仅返回三个模块及其可见状态；
- 三个非空 facade 包：`modules/shared_core/`、`modules/public_analysis/`、`modules/internal_workbench/`；
- 归属清单 `config/modules/ownership_v1.yaml`：每个被纳管文件恰好归属一个 owner；
- 前端两个入口页 `/public`、`/internal` 与更新后的导航语义；
- 守护测试：模块集合测试、AST 导入方向测试、导航测试。

## 3. 对象

| 对象 | 字段 | 说明 |
|---|---|---|
| ModuleDescriptor | `id`、`name`、`layer`、`status` | `status ∈ implemented / designed / gated`；只读，不从路线图读取运行状态 |
| OwnershipManifest | `version`、`(module, path-glob)` 条目集合 | 每个纳管文件恰好归属一次；文件必须存在 |
| ModuleRegistry | 三个模块的静态描述 | 硬编码或配置加载；禁止从 `CURRENT_ROADMAP.md` 推导 |

模块集合固定为：

| 模块 id | 名称 | 层 |
|---|---|---|
| `professional_governance` | 专业治理底座 | 治理层 |
| `shared_core` | 共享分析底座 | 共享层 |
| `public_analysis` | 公开财报分析 | 产品模块 |
| `internal_workbench` | 企业内部分析工作台 | 产品模块 |

`GET /api/v1/modules` 返回产品可见视图：`public_analysis`、`internal_workbench`、`professional_governance`；旧双轨（财务分析轨/经营分析轨）不得作为当前模块出现。

## 4. 状态

- 模块可见状态机：`designed -> gated -> implemented`；首版 `public_analysis` 为 `implemented`（U8 已交付），`internal_workbench` 为 `designed`，`professional_governance` 为 `designed`；
- 状态是声明性的产品可见性标签，不代表运行健康度；不得从运行时指标自动升降级。

## 5. 不变量

1. 依赖方向固定为 `public_analysis -> shared_core <- internal_workbench`；两产品模块**禁止互相导入**；两者均可导入 `shared_core` 与 `professional_governance` 暴露的接口；
2. 归属清单覆盖范围内，每个文件恰好归属一次；新增被纳管文件未登记归属即测试失败；
3. AST 检查对每个 import 的**源文件与目标模块**都通过 ownership manifest 求 owner 后判定方向，禁止只扫描 facade 包（须有位于原路径的跨 owner 导入 fixture 证明）；
4. 旧路由（statements/operations/workbench 等）保留为兼容层，不删除、不搬迁业务数据；新前缀只提供能力发现；
5. 前端入口页只用文字展示职责与 `implemented` / `designed` / `gated` 状态，不得用可操作按钮暗示未实现能力；`/public`、`/internal` 必须包裹 AppShell，登录页仍是唯一例外；
6. `GET /api/v1/modules` 是只读端点，不产生任何写副作用。

## 6. 失败行为

| 情况 | 必须行为 |
|---|---|
| 新增路由/包未在 ownership manifest 登记 | 守护测试失败，合并阻断 |
| public ↔ internal 互相导入 | AST 测试失败，合并阻断 |
| manifest 中文件不存在或重复归属 | 守护测试失败并指出具体路径 |
| `/api/v1/modules` 被请求写方法 | 405；不得隐式创建模块 |
| 前端入口页渲染缺失模块状态 | 组件测试失败 |

## 7. 迁移

- 无数据库迁移；
- 旧路由与旧页面全部保留为兼容层，不删除任何既有路由；旧页面在前端归入「兼容分组」；
- 兼容层的退役条件：内部工作台达到阶段出口且旧路由消费者清零后，另行决策（不在本规格范围）。

## 8. 验收

1. `GET /api/v1/modules` 仅返回三个模块及正确可见状态，旧双轨不出现（`tests/api/test_module_boundaries.py`）；
2. 三个 facade 包非空；ownership manifest 模块集合非空、所有纳管文件恰好归属一次且文件存在；
3. AST 导入方向测试通过，且包含原路径跨 owner 导入的违规 fixture 被正确判定（`tests/architecture/test_module_imports.py`）；
4. `tests/api` 全量回归通过；
5. 前端导航出现企业内部分析工作台、公开财报分析、专业治理三个语义入口；web test、typecheck、lint 与两个 Playwright 规格通过；
6. 本规格转 approved 后，Task 7/8 的实现与本规格逐条对账，偏差必须回本规格修订而非暗改实现。
