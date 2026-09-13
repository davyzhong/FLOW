---
doc_id: FLOW-WI-S01
title: S01 U8 后战略边界、事实合同与安全门禁
doc_type: work-item
status: active
version: 1.1
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

- **当前状态**：active；Task 1 冻结完成（main=914a473，标签 `flow-u8-freeze-20260913`，CI 16/16 绿）；Task 2 三份实施子规格已以 review 状态登记（SPEC_INDEX 可查），approved-spec 门禁脚本与测试已就位，**待用户批准后转 approved**，随后进入 Task 3。
- **范围**：三层两模块工程边界、Financial Facts Contract V2、企业/月度周期身份、RBAC、追加式审计、两模块入口与旧路由兼容。
- **详细计划**：[2026-09-13-flow-post-u8-boundary-gate.md](../../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md)。
- **前置规格**：战略设计 V1.1 已 approved；模块边界、Facts V2、安全/RBAC/审计三份实施子规格须在代码任务前另行 approved。
- **不包含**：公开模块 C 级完整报告链、内部月度工作台功能、真实企业三周期验证。
- **退出条件**：U8 冻结可恢复；V1 不回归；V2 身份完整；角色拒绝/不可自批/AI 无发布权通过；审计追加不改；两模块入口存在；旧 U9/O5、U10 已逐项裁决。
- **状态纪律**：任务领取和状态只写本文件与 `CURRENT_ROADMAP.md`，详细计划不维护第二份状态真相。
