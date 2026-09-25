---
doc_id: FLOW-WI-U04
title: U04 独立 oracle 录入与全行验证
doc_type: work-item
status: blocked
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-25
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
- **当前阻塞**：三份 oracle 已到齐并于 2026-09-24 首跑；199 行均为 `not_comparable`，不是精度失败，也不能作为泛化通过。当前需先让 `cn_ashare_table` 适配「合并及公司」标题与年报页码提示区间，原三样本转为回归集；其后另需由非实现方提供新的独立留出，才可评估泛化。首跑原始材料保存在 `docs/validation/financial_reports/holdout_runs/2026-09-24/` 与 `holdout-results.md`。
- **验收**：全行 diff 通过率报告 + 留出集泛化结论；差异逐项归因（口径/抽取/数据三类）。
- **禁止**：为通过 diff 调整 oracle；用公开数据倒造内部行。
