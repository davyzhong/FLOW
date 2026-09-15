---
doc_id: FLOW-WI-S01
title: S01 U8 后战略边界、事实合同与安全门禁
doc_type: work-item
status: completed
version: 1.4
created_at: 2026-09-13
updated_at: 2026-09-15
owner: FLOW
depends_on: [FLOW-WI-U08, FLOW-DESIGN-STRATEGIC-RESET-001]
acceptance_refs: [strategic-reset-stage-1, facts-contract-v2-gate, security-rbac-audit-gate]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: post-u8-boundary-gate
supersedes: []
superseded_by: null
---

# S01 U8 后战略边界、事实合同与安全门禁

- **当前状态（2026-09-15 关闭）**：completed。Task 1–5、R0/R1（台账 §6）与 R2/R3/R4（台账 §7）全部交付：治理写 7 条策略化、publishing/operations 四阶段 ABI 接线（迁移 0028）、旁路 pipeline 删除、§3.3 身份字段全链 Principal 化、module-boundaries-v2（path-glob + 全树 AST）、full-verification-v2（隔离恢复 + 双证明 PASS）。Task 6 正式关闭。R2–R4 完成登记见[协调台账 §7](../70_operations/2026-09-14-coordination-ledger-glm.md)。
- **历史状态（2026-09-14 对齐 `c9f4c6c`）**：Task 1–5 已完成：U8 冻结 `914a473`、Facts V2 `28a551c`、兼容适配 `2033db4`、Enterprise/AnalysisCycle 与迁移 0025 `15c57c6`。安全规格 V1.1 已获用户批准，独立审查已闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 五路并合 `ff42c67` 及其后回落修复系列（`c1510ce`→`2570bf8`）把路由策略注册表 v2（`997c1ab`）、`main.py` 启动 fail-fast、迁移 0026 的 `gen_random_uuid` 修复与审计 schema/原子性测试、模块边界与 U8 升级门禁、两模块入口（`07d82f2`）全部带入 main。**Kimi `0841ff9`（route-policy v1）不在 main**：与已批准的 V1.1 设计冲突、会实质回退 S01 方向，由 v2 `997c1ab` 取代，分支保留在 `cf90df0` 作审计证据。台账 §5.2 裁决 F2/F3/F5 成立，**Task 6 维持不关闭**；唯一恢复基线 `ba5f34c`（main = integration 同树，登记为 17/17 全绿，尚未由本会话独立复核）。
- **阻塞退出条件的两处残余缺口**：① 运行时未注册 durable `AuditWriter`——`register_audit_writer` 仅在 `security/route_policy.py` 定义，默认实现 `_UnwiredAuditWriter` 返回 503，追加式审计目前只有 0026 的 schema/触发器层保证，故"角色拒绝/不可自批/AI 无发布权"的运行时验证无法通过；② `main.py` 启动 fail-fast 校验 `flow_legacy_bearer_cutoff`（默认 `2026-10-31T15:59:59Z`），到期后**所有**环境（含 development）启动即 `SystemExit(2)`，S01 车道须在该日前完成 identity bindings 迁移或调整默认。
- **范围**：三层两模块工程边界、Financial Facts Contract V2、企业/月度周期身份、RBAC、追加式审计、两模块入口与旧路由兼容。
- **范围计划**：[2026-09-13-flow-post-u8-boundary-gate.md](../../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md)；Task 6–10 的并行执行、所有权和合并门禁由[三智能体计划](../../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md)覆盖。
- **前置规格**：战略设计 V1.1 已 approved；三份实施子规格已全部 approved——[模块边界 V1](../../40_specs/platform/module-boundaries-v1.md)（v1.0）、[Financial Facts Contract V2](../../40_specs/financial-facts/financial-facts-contract-v2.md)（v2.0）、[内部工作台 RBAC 与审计 V1](../../40_specs/security/internal-workbench-rbac-audit-v1.md)（V1.1，独立审查零 P1/P2）。
- **不包含**：公开模块 C 级完整报告链、内部月度工作台功能、真实企业三周期验证。
- **退出条件**：U8 冻结可恢复；V1 不回归；V2 身份完整；角色拒绝/不可自批/AI 无发布权通过；审计追加不改；两模块入口存在；旧 U9/O5、U10 已逐项裁决。
- **状态纪律**：任务领取和状态只写本文件与 `CURRENT_ROADMAP.md`，详细计划不维护第二份状态真相。
