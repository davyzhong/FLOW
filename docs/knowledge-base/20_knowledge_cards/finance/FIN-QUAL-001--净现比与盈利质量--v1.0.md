---
doc_id: FIN-QUAL-001
title: 净现比与盈利质量
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: flow-knowledge-2026-09-12.1
source_refs: [GRP-A-finance]
authority_level: D
sensitivity: public
domain: profitability
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [FIN-STAT-001]
related_code: [services/api/src/flow_api/services/metrics]
---

# 净现比与盈利质量

- **定义**：经营活动现金流净额 / 净利润，衡量利润的现金含量。
- **业务目的**：识别「有利润没现金」的盈利质量问题。
- **输入**：经营现金净额（期间）、净利润（同期，含少数股东）。
- **规则**：分子分母同期同口径；负净利润时比值符号如实保留（不取绝对值）；比率无意义（分母≈0）时显式不可比而非伪造值。
- **适用**：季度/年度公开披露与内部月度口径。
- **不适用**：分母为负或近零（输出「不可比」）；跨准则直接对比未调口径。
- **常见误用**：abs() 掩盖符号；用净现比排序不同资本结构的企业。
- **来源与核验**：A 组「净利润 vs 现金流 ×4」；2026-09-08 P1 修复轮（去 abs()、显式 None）即工程核验。
- **FLOW 影响**：净现比已在指标库实现；负分母政策与 C03 统一（不伪造比率）。
