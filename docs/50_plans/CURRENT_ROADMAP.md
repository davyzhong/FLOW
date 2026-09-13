---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 1.2
created_at: 2026-09-12
updated_at: 2026-09-13
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

## 顺序与状态（2026-09-13 迁移关闭后核对）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **active** | — | U8-C 结构化日志 088977b；剩真实存储旅程/HTTPS 拓扑/统一部署验收 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked(外部到料)** — 可并行 | 独立会话人力 | HANDOFF §0：oracle 需人工录入 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **blocked(U08 完成后)** | U08 | 冻结 U8；三层两模块边界；Facts V2；RBAC/审计；[详细计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) |
| 3 | 公开财报模块 C 级出口 | **gated(阶段 2 后)** | 边界门禁 | company-level holdout、正式数字 100% 可复算/可追源、零严重事实错误、独立盲评；[验收 §14.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#141-公开模块-c-级出口协议) |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告 |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked(授权 + 待重新裁决)** | U08 + 数据授权 | 历史工作包，不按旧顺序自动领取 |
| R2 | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked(待重新裁决)** | 原依赖链 | 历史工作包，不按旧顺序自动领取 |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

战略方向（2026-09-13，D052–D054）：企业内部月度财务经营分析工作台为最终产品，公开财报模块独立并先行成熟共享底座；顺序为 U8 → 边界重构 → 公开模块 C 级出口 → 内部工作台 → 四级验证。详见[战略重构设计](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)。

并行动作（非阻塞）：rnd_exp 官方核验（待《应用指南汇编 2024》原文，复核暂登记 4301）。

## 纪律

- 任务领取/勾选/提交只用本页与工作包；模块可以维护不可领取的 workstream/backlog 视图，但不得形成第二份状态真相；每完成一阶段提交推送、CI 绿才算 done；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
