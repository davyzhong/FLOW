---
doc_id: FLOW-PLAN-050
title: 计划体系
doc_type: navigation
status: current
version: 2.0
created_at: 2026-09-12
updated_at: 2026-10-24
owner: FLOW
applies_to: docs
---

# 计划体系

**唯一主线**是 [CURRENT_ROADMAP.md](CURRENT_ROADMAP.md)（状态真相 + 执行队列），
稳定工作包 `work_items/` 保存各包验收细节。允许 doc_type: plan/work-item。
禁止第二份状态路线图或第二份 active 总计划。

2026-09-25 用户裁决（2A）后，下列文档已归档为历史/验收细节参考，不再作为
归档参考（不得作为第二份 To-do）：[EXECUTION_TODO](EXECUTION_TODO.md)、
[整合总计划（2026-09-24）](2026-09-24-integrated-master-plan.md)、
[统一完整实施计划（2026-09-24）](../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md)、
[执行收敛与验收计划（2026-09-25）](2026-09-25-project-execution-convergence-plan.md)。

D055 单机原型收尾已完成：7a.1–7a.8 已关闭并合入 main；PR #4 状态归档 merge commit `b068796f906cfbb91ac33775f5578194acc98a51` 的准确 SHA run `40096497668` 为 28/28 success。当前唯一执行项为“可复用视觉语言提炼与 FLOW 全项目视觉统一”，设计规格与工作包已获用户批准，正在分支 `codex/flow-visual-language` 串行实施；首阶段 token/主要页面映射及 20 路由×3 视口截图已采集，修复 `/operations` UUID 参数后 60/60 路由视口基础渲染检查通过；逐图表与导出格式视觉验收尚未关闭。阶段记录见[视觉覆盖验收](../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。K2 顺延为排队。完整状态见 [CURRENT_ROADMAP](CURRENT_ROADMAP.md) 和[完结差距报告](../60_delivery/verification/2026-10-24--prototype-completion-gap-review-v1.md)。历史状态和旧分支指引不作为执行入口。
