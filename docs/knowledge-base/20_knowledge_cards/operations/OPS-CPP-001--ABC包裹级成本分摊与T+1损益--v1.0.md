---
doc_id: OPS-CPP-001
title: ABC 包裹级成本分摊与 T+1 损益
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: flow-knowledge-2026-09-12.1
source_refs: [GRP-D-wiki]
authority_level: D
sensitivity: public
domain: logistics_and_supply_chain
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [OPS-PROFIT-001, OPS-LOGI-001]
related_code: []
---

# ABC 包裹级成本分摊与 T+1 损益

- **定义**：作业成本法（ABC）把间接成本按动因分摊到单个包裹，形成包裹级 CPP（cost per parcel）与 T+1 日结损益。
- **业务目的**：单包裹真实盈利视图；实时损益反应。
- **输入**：成本池、作业动因（件/重量/体积/距离）、包裹事实流。
- **规则**：分摊规则白盒可解释；预估与实际差异按期回补；准确率披露（范本声明 98%）须附口径。
- **适用**：快递/仓配一体化企业内部核算（L3 事件事实）。
- **不适用**：公开披露；动因数据缺失时退化为线路级分摊并显式降级。
- **常见误用**：黑箱分摊不可审计；用预估 CPP 直接对外承诺。
- **来源与核验**：wiki 业财簇「ABC 包裹级 CPP 分摊 + T+1 损益体系」5 篇（含白盒规则与预估准确率）。
- **FLOW 影响**：U9/O5 分部经营分析核算底座范本；成本指标 YAML 候选的方法依据。
