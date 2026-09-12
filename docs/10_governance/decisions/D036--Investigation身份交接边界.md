---
doc_id: FLOW-DECISION-D036
title: D036 Investigation 身份交接边界
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

# D036 Investigation 身份交接边界

- 状态（原文）：有效（映射为 accepted）

- 状态（原日志）：有效
- 决定：Phase 6 的每个 Finding 跳转必须保留 `finding_id`、`batch_id`、`metric_snapshot_id` 和 `analysis_run_id`，并先由不可变身份回执页确认上下文。
- 当前边界：Phase 6 不实现证据下钻和评审；Phase 7 在该身份之上建设 Evidence-first Investigation，不得静默切换批次、快照或运行。
