---
doc_id: FLOW-WI-U04
title: U04 独立 oracle 录入与全行验证
doc_type: work-item
status: active
version: 1.4
created_at: 2026-09-12
updated_at: 2026-09-29
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
- **当前执行步骤（2026-09-29 晚更新）**：适配器修复、pypdf 运行依赖与 CI 收尾修正均已完成——用户批准两处最小 CI 变更（intake-e2e 超时 40→45、module-boundaries-e2e 关闭未使用的 uv 缓存）后提交 `229069ca` 准确 SHA CI run `36511316012` 17/17 success。**小米/阿里未调参首跑已完成（run ID `2026-09-29-holdout-first-run`）并双双失败**：小米 0/25（UnsupportedLayoutError，三适配器得分 0/1/1，英文版文件身份正确，真实版式泛化失败）；阿里 0/15（hk_traditional_text 硬编码京东物流年报页锚 106±5 对 26 页简体季度公告必然失效）。40 行 oracle 全部 not_comparable，0 行值比对，无伪造输出/静默错值，原始产物全量保留。归因与协议处置见 [holdout-results.md §4](../../../docs/implementation/objective-analysis/holdout-results.md)。**按 oracle-register §4.5：使用该两样本开发适配器即自动降为回归集，并按 §3 启用备选（yunda_2026h1/jdl_2026h1）补新留出**；这是下一执行 fork。
- **独立 oracle 审计**：冻结的14份 C 级报告目前没有完整逐行独立 oracle（0/14）。5份已登记 oracle 对应另外的 holdout，均属部分行转录。不得将 L1 v5、实现方复核或既有 AI 交叉评冒充完整独立 oracle。
- **首跑历史与降级纪律**：2026-09-24 三份旧候选共199行均 `not_comparable`，不是准确率通过或数值失败；解析修复后可作为回归。小米与阿里新留出在首次机器运行前不得用于版式适配、参数选择或人工纠错。发现样本已被实现用于调参时，按 `oracle-register.md` 降级并启用已冻结备选，不重新抽签。
- **验收**：全行 diff 通过率报告 + 留出集泛化结论；差异逐项归因（口径/抽取/数据三类）。当前旧三样本回归产物见 `validation/financial_reports/holdout_runs/2026-09-29-adapter-v4/`；生产依赖 smoke 已在隔离 Compose 实测修复；修复提交的功能性 CI 通过，但 CI workflow 收尾清理仍需获批修正；新的小米/阿里结果仍待准确 SHA CI 全绿后首次运行。
- **禁止**：为通过 diff 调整 oracle；用公开数据倒造内部行。
