---
doc_id: OPS-LOGI-001
title: 物流成本科目体系
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: flow-knowledge-2026-09-12.1
source_refs: [GRP-C-logistics]
authority_level: D
sensitivity: public
domain: logistics_and_supply_chain
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [OPS-CPP-001]
related_code: []
---

# 物流成本科目体系

- **定义**：物流成本按环节的 L3 科目分类：揽收、干线、转运、分拨、末端派送、燃油附加、包材、退件等。
- **业务目的**：成本结构对标与环节降本；单位成本对标锚点（如千元收入结算成本、百单客服成本）。
- **输入**：成本科目字典 + 环节归集口径。
- **规则**：科目到环节多对一映射显式；对标锚点必须注明企业与期间（不可跨期直接比）。
- **适用**：物流企业经营成本指标构建（O2 43 指标的行业集）。
- **不适用**：非物流企业；混业分部未拆前的整体口径。
- **常见误用**：把某家内部对标值当行业标准；科目合并口径变化后直接环比。
- **来源与核验**：C 组跨境物流「703 行物流成本科目字典」（L3 科目线索）；菜鸟 OKR 对标锚点（结算成本 3.3→2.19 元、百单客服 1.39→1.10 等——内部数值仅方法论参照）。
- **FLOW 影响**：经营轨成本指标 YAML 候选清单；字段/公式/授权状态逐项核验后进指标库。
