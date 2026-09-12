---
doc_id: FIN-MARGIN-001
title: 毛利率与净利率的结构差异
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-A-finance, GRP-W1-wechat]
authority_level: D
sensitivity: public
domain: profitability
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [FIN-DUPONT-001]
related_code: []
---

# 毛利率与净利率的结构差异

- **定义**：毛利率=（收入-营业成本）/收入；净利率=净利润/收入；两者之差由费用、减值、税项与其他损益构成。
- **业务目的**：定价与成本竞争力（毛利）对比最终盈利效率（净利），差异结构指向费用或非经营项目异常。
- **输入**：收入、营业成本、期间费用、其他损益、净利润。
- **规则**：分母统一为总收入口径（净额法/总额法先对齐）；结构差异拆解按损益表层级逐项。
- **适用**：制造业/物流企业的分部与整体口径。
- **不适用**：金融业务占比较高主体（营业成本语义不同）。
- **常见误用**：不同收入确认口径（总额/净额）直接比毛利；把非经常损益留在「差异」里不单列。
- **来源与核验**：A 组「毛利率 vs 净利率 ×2」及数据熊系列；代表篇精读。
- **FLOW 影响**：利润桥（dashboard）的层级拆解骨架；多维盈利（U9/O5 候选）的分解基础。
