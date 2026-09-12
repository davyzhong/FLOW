---
doc_id: FLOW-DECISION-D031
title: D031 Phase 5 分析输出边界
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

# D031 Phase 5 分析输出边界

- 状态（原文）：有效（映射为 accepted）

- 状态（原日志）：有效
- 决定：Phase 5 只生成由确定性计算和已有证据完全支持的 Finding；缺字段或分析不适用时显式降级，不生成假设性 Finding。
- 原因：财务金额、Driver、影响和排名必须可重现，AI 只能在后续阶段解释已有结果。
