---
doc_id: FIN-STAT-001
title: 三大报表勾稽关系
doc_type: knowledge-card
status: verified
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-A-finance, GRP-W1-wechat]
authority_level: D
sensitivity: public
domain: finance_statements
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [FIN-QUAL-001]
related_code: [services/api/tests/statements]
---

# 三大报表勾稽关系

- **定义**：资产负债表、利润表、现金流量表之间由会计恒等式与编制逻辑决定的系统性对应（期末未分配利润衔接、净利润→经营现金起点、现金净变动=期末-期初等）。
- **业务目的**：数据可信性的第一道校验；勾稽不通过的报表不可用于分析。
- **输入**：三表科目全集（期间 + 期初余额）。
- **规则**：净利衔接权益变动；经营现金起点为净利润；现金及等价物净变动与资产负债表一致；融资/投资分类与负债/资产变动对应。
- **适用**：已通过 B 系列抽取归一的财报（IFRS/US GAAP/HKEX 披露）。
- **不适用**：分部披露独立口径；非完整三表的业绩公告（须显式缺表守卫，不伪造勾稽通过）。
- **常见误用**：用勾稽通过证明科目正确（勾稽只覆盖跨表一致性）；把权益变动表的准备项并入未分配利润。
- **来源与核验**：A 组「三大报表勾稽 ×4」（wechat-7506597e2649 等）+ B 系列实现核验；方法结构经代表篇精读。
- **FLOW 影响**：`financial-facts-contract` 的勾稽器与缺表守卫（P0 修复轮）即本卡落地；缺表必须阻断发布而非 500。
