---
doc_id: FLOW-NAV-READING-001
title: 最短阅读顺序
doc_type: navigation
status: current
version: 1.5
created_at: 2026-09-12
updated_at: 2026-09-25
owner: FLOW
applies_to: docs
---

# 最短阅读顺序

新 Agent 按以下顺序最多读五份文档即可接续项目（各角色可截断）：

1. [PROJECT_STATE.md](PROJECT_STATE.md) —— 现状、阻塞、唯一执行入口
2. [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md) —— 唯一路线图与工作包状态；需要执行步骤时继续读 [FLOW 统一完整实施计划](../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md)
3. [PRODUCT_SCOPE](../20_product/PRODUCT_SCOPE.md) + [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md) —— 三层两模块范围、冲突裁决矩阵与固定原则（D052–D054；含 [能力地图](../20_product/CAPABILITY_MAP.md)）
4. [战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md) —— 当前最高产品方向、量化出口与真实企业验证协议；现行机器合同见 [财务事实合同 V1](../superpowers/specs/financial-facts-contract.md)，[Facts V2](../40_specs/financial-facts/financial-facts-contract-v2.md) 已批准并实现基础模型，安全规格 V1.1 已批准且独立审查闭环（零 P1/P2）；当前数据库迁移头 `0030_page_anchor_vocabulary`（主线与当前开发库核验值；详细证据见 PROJECT_STATE）
5. [决策索引](../10_governance/DECISION_INDEX.md) —— D001–D054 正式决策；历史完整日志按字节保留于 `knowledge-base/04_decisions/DECISION_LOG.md`（只读，见 legacy sidecar）

知识引用：产品设计类文档的 `knowledge_release` 使用 `flow-knowledge-2026-09-12.1`（M2 后切换 `flow-knowledge-2026-09-12.1`）。
