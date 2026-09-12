---
doc_id: METHOD-REPORT-001
title: 月报四象限与报告四列表
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-W1-wechat, GRP-A-finance]
authority_level: D
sensitivity: public
domain: management_reporting
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [METHOD-QA-001]
related_code: [services/api/src/flow_api]
---

# 月报四象限与报告四列表

- **定义**：月度经营报告首页四象限（经营结果/增长质量/运营效率/重点风险）；正文指标表固定四列（实际/同比/预算达成率/状态）。
- **业务目的**：固定信息架构降低阅读与编写成本；状态列驱动注意力分配。
- **输入**：核心指标集 + 目标值 + 同比基期。
- **规则**：四列缺一显式标注（无预算时达成列标 N/A 而非删列）；状态灯阈值显式配置且版本留痕；结论摘要先行。
- **适用**：月/季/年度经营报告与专项（应收/费用/成本/现金流）。
- **不适用**：对外披露口径（监管格式优先）。
- **常见误用**：把模板数值当默认阈值；状态灯无阈值版本记录导致不可追溯。
- **来源与核验**：数研复盘狮 20 页月报结构；A 组报告模板族 21 篇趋同结构；财务总监驾驶舱 11 模块系列。
- **FLOW 影响**：报告中心月度章节编排与 /operations 概览的信息架构参照；经营快照多格式输出的内容合同。
