---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 1.7
created_at: 2026-09-12
updated_at: 2026-09-17
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一执行入口）

> 本页只维护顺序、依赖、状态与证据链接；详细步骤在各工作包。全仓唯一可执行总计划——历史计划均已 superseded。

## 顺序与状态（2026-09-17 对 `defd823` 核对；前次为 2026-09-15 v1.6）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked(外部到料)** — 可并行 | 独立会话人力 | HANDOFF §0：oracle 需人工录入 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **blocked(用户裁决)** | S01 关闭 ✓ | **T09 已交付**：L0 1454/1454 + L1 页级答案集 98.9%（1775/1795，strong 972/weak 803）且锚失效/值不一致双 0（`accuracy_benchmark.py --level L1`）；余项=独立盲评与 holdout 抽签（需用户/第三方） |
| 3a | [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | — | B3 溯源 95.5% 行项目带页锚（迁移 0029 + 导入/API/前端）；B4 supersedes 链 + 差异脚本；B5 只读 MCP 三工具（token fail-closed）；B6 确定性差异说明起草 |
| 3b | [数据扩张、行业基准与 10× 性能基线](work_items/PUBLIC--data-expansion-benchmarks.md) | **active** | 性能基线 ✓；扩张待外部财报 | G2 完成：10×（1034→10340 行）P95 明细 6.2ms/检索 0.97ms/聚合 1.11ms（`perf_baseline.py`）；C1 扩张需真实财报到料 |
| 3c | [AI 问数 v1 与评测集](work_items/PUBLIC--ai-qa-v1.md) | **completed(v1)** | — | 确定性检索引用 QA + 94 问评测集（60 数值 + 34 拒答）命中率 100%、拒答零误答（`ask_facts.py` / `generate_qa_eval.py`）；LLM 通道与 v2/v3 另行裁决 |
| 3d | Web 前端一致性整改（信息架构/设计 token/组件库/五态/响应式） | **completed(基线)** | — | P0–P3 五批：`fe61b5c`（F2 17 token 补定义+值漂移修复+登录/退出/错误中文化）→ `8fa13a6`（生产构建门禁+四页 390px 溢出修复）→ `53ef2eb`（数据态拦截门禁+触控目标+溯源交互）→ `defd823`（PageState 组件+FlowDataTable 内建滚动+operations/investigations 迁移）；门禁矩阵 390/1024/1440 × 数据态，生产 e2e 56/56、单测 84/84、lint 1 登记例外；执行日志见[整改计划 v1.4 §10](../superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md)。遗留（不阻塞）：metric-library 全量迁移、溯源真实来源链接（待后端供稿决策） |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告。设计输入已备：知识库第二截面登记经营分析会四体系/月度周期蓝本与月报可视化实例（借鉴 #20/#22/#24，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)） |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked(授权 + 待重新裁决)** | U08 + 数据授权 | 历史工作包，不按旧顺序自动领取 |
| R2' | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked(待重新裁决)** | 原依赖链 | 历史工作包，不按旧顺序自动领取 |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

战略方向（2026-09-13，D052–D054）：企业内部月度财务经营分析工作台为最终产品，公开财报模块独立并先行成熟共享底座；顺序为 U8 → 边界重构 → 公开模块 C 级出口 → 内部工作台 → 四级验证。详见[战略重构设计](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)。

并行动作（非阻塞）：

- rnd_exp 官方核验（待《应用指南汇编 2024》原文，复核暂登记 4301）。
- 知识库第二截面增量扫描完成（2026-09-17，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）：四分类真新增 203 篇（HIGH 138）+ Davybase 图片知识化附录层 915 篇（微信全库批次进行中）；借鉴附录 #20–#24 已登记并入统一计划输入。
- 指标库行业包扩展素材已备（借鉴 #21：15 行业财务指标参考值、13 行业数据指标体系、美团指标体系实例）——作为指标库 v1.x 的候选增项，领取时按取用协议回读原文。

## 纪律

- 任务领取/勾选/提交只用本页与工作包；模块可以维护不可领取的 workstream/backlog 视图，但不得形成第二份状态真相；每完成一阶段提交推送、CI 绿才算 done；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
