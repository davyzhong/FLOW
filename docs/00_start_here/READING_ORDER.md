---
doc_id: FLOW-NAV-READING-001
title: 最短阅读顺序
doc_type: navigation
status: current
version: 2.0
created_at: 2026-09-12
updated_at: 2026-10-25
owner: FLOW
applies_to: docs
---

# 最短阅读顺序

新 Agent 按以下顺序最多读五份文档即可接续项目（各角色可截断）：

1. [PROJECT_STATE.md](PROJECT_STATE.md) —— 现状、阻塞、唯一执行入口
2. [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md) —— 唯一路线图与工作包状态；当前执行项为[可复用视觉语言与全项目视觉统一](../50_plans/work_items/FLOW--portable-visual-language-and-full-project-restyle.md)，视觉方向见[设计稿](../superpowers/specs/2026-10-24-flow-visual-language-system-design.md)，可复制 token 与表达范式见[视觉语言包](../../packages/flow-visual-language/README.md)，页面和 HTML/PDF/PPTX/XLSX 输出验收见[视觉覆盖报告](../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。D055 单机原型工作包已 completed
3. [PRODUCT_SCOPE](../20_product/PRODUCT_SCOPE.md) + [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md) —— 三层两模块范围、冲突裁决矩阵与固定原则（D052–D054；含 [能力地图](../20_product/CAPABILITY_MAP.md)）
4. [战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md) 与 [D055](../10_governance/decisions/D055--单机单用户验证原型.md) —— 长期产品边界与当前单机原型目标；当前代码迁移头为 `0032_cockpit_action_item`，验收和 CI 以路线图记录的准确 SHA 为准
5. [决策索引](../10_governance/DECISION_INDEX.md) —— D001–D056 正式决策；历史完整日志按字节保留于 `knowledge-base/04_decisions/DECISION_LOG.md`（只读，见 legacy sidecar）

知识引用：产品设计类文档的 `knowledge_release` 使用 `flow-knowledge-2026-09-12.1`（M2 后切换 `flow-knowledge-2026-09-12.1`）。
