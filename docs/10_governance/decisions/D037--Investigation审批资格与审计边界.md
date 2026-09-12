---
doc_id: FLOW-DECISION-D037
title: D037 Investigation 审批资格与审计边界
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

# D037 Investigation 审批资格与审计边界

- 状态（原文）：有效（映射为 accepted）

- 状态（原日志）：有效
- 决定：Finding 状态机为 candidate → in_review（提交）→ approved（签发，需全部证据 verified 且结论四要素完整）/ rejected，in_review 可退回 candidate，approved 可退回 in_review；rejected 在 V1 为终态。
- 证据决策：pending/verified/rejected 之间按受控迁移，每次证据决策与 Finding 迁移都追加 ReviewEvent（含 evidence_verified/evidence_rejected，迁移 0008），审计记录只增不改。
- 边界：记录级表格只展示 canonical 数值与文件/工作表/行血缘，不在 Investigation 中重算任何分析金额；演示种子 `--fresh-batch` 通过新建批次保证门禁可重复，不改动已发布历史。
