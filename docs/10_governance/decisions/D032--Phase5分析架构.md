---
doc_id: FLOW-DECISION-D032
title: D032 Phase 5 分析架构
doc_type: decision
status: accepted
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decided_at: 2026-09-12
authority: user
source_refs: [docs/knowledge-base/04_decisions/DECISION_LOG.md]
---

# D032 Phase 5 分析架构

- 状态（原文）：有效（映射为 accepted）

- 状态（原日志）：有效
- 决定：采用 typed analysis playbooks + shared protocol，不使用单体硬编码服务，也不在 V1 引入通用公式 DSL。
- 结果：首批注册 `revenue_vpm`、`fulfillment_cost_rve`、`gross_profit_bridge`、`operating_profit_bridge` 和 `ar_cash_impact`。
