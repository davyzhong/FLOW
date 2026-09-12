---
doc_id: OPS-CFO-001
title: 红黄绿灯指标治理
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
domain: operational_efficiency
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [GOV-METRIC-001, FIN-RECV-001]
related_code: []
---

# 红黄绿灯指标治理

- **定义**：指标按「目标-实际-偏差-灯色-原因」五行治理：偏离阈值自动亮灯并强制原因登记与跟进。
- **业务目的**：把月度指标审视从「读数」变成「处理异常」。
- **输入**：指标实际值、目标值、阈值配置、责任人。
- **规则**：灯色阈值显式配置且可追溯到版本；红黄项必须挂原因与动作；绿灯项不展开。
- **适用**：内部经营月报与驾驶舱（菜鸟 CFO Metrics 报表实证）。
- **不适用**：无目标基线的首次披露期。
- **常见误用**：阈值拍脑袋无版本记录；灯色逻辑藏在代码里不可配置。
- **来源与核验**：菜鸟 CFO 红黄绿灯运营指标报表（应收/坏账率/逾期率/对账完成率）——一手治理模板。
- **FLOW 影响**：/operations 概览与经营快照的状态灯设计；C 系列指标治理（草稿/验证/激活/退役）的呈现层参照。
