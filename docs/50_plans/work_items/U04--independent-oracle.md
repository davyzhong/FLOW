---
doc_id: FLOW-WI-U04
title: U04 独立 oracle 录入与全行验证
doc_type: work-item
status: blocked
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [U4-fullrow-diff, U4-holdout-generalization]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: verification
supersedes: []
superseded_by: null
---

# U04 独立 oracle

- **范围**：由未参与抽取器开发的独立会话录入 oracle；全行 diff 与留出泛化验收。
- **当前阻塞**：外部到料 + 独立会话人力（HANDOFF §0）；到料即并行，不依赖 U08。
- **验收**：全行 diff 通过率报告 + 留出集泛化结论；差异逐项归因（口径/抽取/数据三类）。
- **禁止**：为通过 diff 调整 oracle；用公开数据倒造内部行。
