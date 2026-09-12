---
doc_id: OPS-MASTER-001
title: L1-L4 利润中心与经营主数据
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: flow-knowledge-2026-09-12.1
source_refs: [GRP-D-wiki, GRP-B-management]
authority_level: D
sensitivity: public
domain: operational_efficiency
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [OPS-PROFIT-001]
related_code: []
---

# L1-L4 利润中心与经营主数据

- **定义**：经营单元按 L1（集团）—L2（事业群/BU）—L3（利润中心/城市）—L4（成本单元/网点）四级组织；配套成本单元与支出项主数据。
- **业务目的**：多维盈利与考核的组织维度底座（谁盈利、谁超支）。
- **输入**：组织树、利润中心属性（法人/考核双视角）、成本单元、支出项目录。
- **规则**：主数据源头唯一打标；法人视图与考核视图分离；历史组织变更保留时间有效区间（不可回写）。
- **适用**：内部多维盈利分析（S16/U9 落地细节）。
- **不适用**：公开披露（组织披露粒度不足）。
- **常见误用**：用当前组织树回溯历史（忽视组织变迁）；双视图混用导致合并口径漂移。
- **来源与核验**：wiki 业财一体化/主数据/损益分摊簇 182 篇（字段级组织维度设计）+ B 组 note_4/note_7。
- **FLOW 影响**：U9 主数据与版本合同候选的字段蓝本；组织维度键设计参照。
