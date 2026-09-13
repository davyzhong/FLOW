---
doc_id: FLOW-WI-S01
title: S01 U8 后战略边界、事实合同与安全门禁
doc_type: work-item
status: active
version: 1.2
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
depends_on: [FLOW-WI-U08, FLOW-DESIGN-STRATEGIC-RESET-001]
acceptance_refs: [strategic-reset-stage-1, facts-contract-v2-gate, security-rbac-audit-gate]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: post-u8-boundary-gate
supersedes: []
superseded_by: null
---

# S01 U8 后战略边界、事实合同与安全门禁

- **当前状态**：active；Task 1–5 已完成：U8 冻结 `914a473`、Facts V2 `28a551c`、兼容适配 `2033db4`、Enterprise/AnalysisCycle 与迁移 0025 `15c57c6`，均有绿色 CI。当前领取 Gate 0 与 Task 6 Bootstrap：安全规格 V1.1 已获用户批准，正在独立审查；integration 基线含 CI 结果核验器。Kimi `0841ff9`、GLM `07d82f2` 是待审候选，不代表 Task 6/8 完成。
- **范围**：三层两模块工程边界、Financial Facts Contract V2、企业/月度周期身份、RBAC、追加式审计、两模块入口与旧路由兼容。
- **范围计划**：[2026-09-13-flow-post-u8-boundary-gate.md](../../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md)；Task 6–10 的并行执行、所有权和合并门禁由[三智能体计划](../../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md)覆盖。
- **前置规格**：战略设计 V1.1 已 approved；模块边界、Facts V2、安全/RBAC/审计三份实施子规格须在代码任务前另行 approved。
- **不包含**：公开模块 C 级完整报告链、内部月度工作台功能、真实企业三周期验证。
- **退出条件**：U8 冻结可恢复；V1 不回归；V2 身份完整；角色拒绝/不可自批/AI 无发布权通过；审计追加不改；两模块入口存在；旧 U9/O5、U10 已逐项裁决。
- **状态纪律**：任务领取和状态只写本文件与 `CURRENT_ROADMAP.md`，详细计划不维护第二份状态真相。
