---
doc_id: OPS-PROFIT-001
title: 单票/单箱利润拆解
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
domain: logistics_and_supply_chain
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [OPS-CPP-001, METHOD-QA-001]
related_code: []
---

# 单票/单箱利润拆解

- **定义**：把利润中心净利按「量 × 价 − 费」拆到单票（快递/包裹）或单箱（仓发）颗粒度的完整实例框架。
- **业务目的**：定位亏损线路/客户/仓；支撑定价与网点考核。
- **输入**：分部收入、件量/箱量、分项成本（干支线/仓内/末端/返利）。
- **规则**：拆解层级固定为 量→价→费→返利；成本分摊规则显式（见 OPS-CPP-001）；城市/线路维度穿透。
- **适用**：内部经营分析（L2/L3 过程事实，授权后）。
- **不适用**：公开披露粒度（无单票数据）。
- **常见误用**：分摊规则黑箱导致口径不可比；返利计入时点与业务节奏错配。
- **来源与核验**：A 组财务与会计「经营单元利润拆解完整实例（拆到城市/返利动作）」——菜鸟一手业财资料（方法论参照，内部数值不取）。
- **FLOW 影响**：O5 窄主题分析包候选骨架；四问工作台「为什么」层的拆解路径模板。
