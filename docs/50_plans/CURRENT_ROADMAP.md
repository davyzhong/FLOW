---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
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

## 顺序与状态（2026-09-12 23:20 核对）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **active** | — | U8-C 结构化日志 088977b；剩真实存储旅程/HTTPS 拓扑/统一部署验收 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked(外部到料)** — 可并行 | 独立会话人力 | HANDOFF §0：oracle 需人工录入 |
| 2 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked(授权)** | U08 + 数据授权 | 无授权不得摊月/伪造 L2-L3 |
| 3 | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked(依赖链)** | U04+U08+U09/O05 | go/hold/drop 逐项 |
| 4 | [DOC-M5 历史整理](../../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **active**（迁移批次，待批准推进） | M0–M4 done | 962b651 发布 / df7f6e3 规格统一 |
| 5 | [DOC-M6 全面验证](../../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | proposed | M5 | 五题接续测试 |

并行动作（非阻塞）：rnd_exp 官方核验（待《应用指南汇编 2024》原文，复核暂登记 4301）。

## 纪律

- 任务领取/勾选/提交只用本页与工作包；每完成一阶段提交推送、CI 绿才算 done；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
