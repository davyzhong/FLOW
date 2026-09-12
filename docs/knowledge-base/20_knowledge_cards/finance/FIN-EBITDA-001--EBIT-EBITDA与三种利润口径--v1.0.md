---
doc_id: FIN-EBITDA-001
title: EBIT/EBITDA 与三种利润口径
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-A-finance, GRP-W4-benxiang]
authority_level: D
sensitivity: public
domain: finance_statements
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [FIN-MARGIN-001]
related_code: []
---

# EBIT/EBITDA 与三种利润口径

- **定义**：会计利润（净利润）/ 财务利润（EBIT，剔除融资与税）/ 管理利润（EBITDA，再剔除折摊）三层口径。
- **业务目的**：跨资本结构与折旧政策比较经营盈利能力；管理层视角剔除非现金费用。
- **输入**：净利润、财务费用、所得税、折旧摊销（或经由附注重建）。
- **规则**：EBIT=净利+税+财务费用（口径变体须显式声明）；EBITDA 叠加 D&A；调整项（减值/股权激励）单列不并入基础口径。
- **适用**：重资产物流/电商分部对标（如经调整 EBITA 披露）。
- **不适用**：未披露折摊明细时的「精确 EBITDA」声明（只能给重建口径与假设）。
- **常见误用**：把公司自定义「经调整」口径当标准 EBITDA 直接对标；忽略 IFRS 18 后非 GDP 指标的呈现限制（须核对准则原文）。
- **来源与核验**：A 组「三种利润 ×3」「EBIT/EBITDA ×2」；菜鸟分部经调整 EBITA 序列（C 组）为实证样例。
- **FLOW 影响**：菜鸟分部 YAML 已含经调整 EBITA；指标库扩展候选（声明口径变体字段）。
