---
doc_id: FLOW-RELEASE-DOCSYS-001
title: 文档体系 v1 发布记录（迁移完成）
doc_type: delivery
status: verified
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
commit_refs: "[962b651, e3640aa]"
evidence_refs: "[FLOW-VERIFY-DOCMIG-001]"
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: repository
supersedes: []
superseded_by: null
---

# 文档体系 v1（M0–M6 迁移关闭记录）

- 知识发布：`flow-knowledge-2026-09-12.1`（CURRENT_RELEASE；旧发布可由 release-lock 恢复）
- 结构：docs/00–90 十区 + knowledge-base 分层（10_sources/20_cards/30_handbooks/40_methods/50_mappings + 不可变档案）
- 唯一事实源：PROJECT_STATE（状态）/ CURRENT_ROADMAP（执行）/ PRODUCT_SCOPE（范围）/ DECISION_INDEX（决策）/ SPEC_INDEX（规格）
- 治理：make docs-check（六门禁）+ CI m6 + legacy-exempt 哈希锁 + link-allowlist
- 剩余边界：见验证记录「已知边界」；产品代码无语义变更；不可变档案逐文件哈希未变
