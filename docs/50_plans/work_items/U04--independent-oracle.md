---
doc_id: FLOW-WI-U04
title: U04 独立 oracle 录入与全行验证
doc_type: work-item
status: active
version: 1.2
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
- **当前执行步骤**：先修复 `cn_ashare_table` 对「合并及公司」标题和年报页码提示区间的支持；按 TDD 建立版式测试，运行旧三样本回归并将199行 `not_comparable` 首跑原件作为历史证据保留。适配代码固定后，才运行已冻结的小米 2026H1 和阿里 FY2027Q1 新留出；目前仓库未发现两份新样本的首跑 diff artifact，故必须完成首次未调参运行并保存完整机器输出。
- **独立 oracle 审计**：冻结的14份 C 级报告目前没有完整逐行独立 oracle（0/14）。5份已登记 oracle 对应另外的 holdout，均属部分行转录。不得将 L1 v5、实现方复核或既有 AI 交叉评冒充完整独立 oracle。
- **首跑历史与降级纪律**：2026-09-24 三份旧候选共199行均 `not_comparable`，不是准确率通过或数值失败；解析修复后可作为回归。小米与阿里新留出在首次机器运行前不得用于版式适配、参数选择或人工纠错。发现样本已被实现用于调参时，按 `oracle-register.md` 降级并启用已冻结备选，不重新抽签。
- **验收**：全行 diff 通过率报告 + 留出集泛化结论；差异逐项归因（口径/抽取/数据三类）。
- **禁止**：为通过 diff 调整 oracle；用公开数据倒造内部行。
