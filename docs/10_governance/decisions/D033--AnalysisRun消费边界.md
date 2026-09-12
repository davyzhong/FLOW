---
doc_id: FLOW-DECISION-D033
title: D033 Analysis Run 消费边界
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

# D033 Analysis Run 消费边界

- 状态（原文）：有效（映射为 accepted）

- 状态（原日志）：有效
- 决定：Dashboard、Investigation、AI 和报告共同读取已发布且不可变的 Analysis Run；下游不得重新执行分析公式或修改 Finding 排名。
- 原因：保证所有界面和输出使用同一事实、Driver、证据和策略版本。
