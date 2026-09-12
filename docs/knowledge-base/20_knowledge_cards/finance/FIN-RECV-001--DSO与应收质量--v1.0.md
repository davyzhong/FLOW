---
doc_id: FIN-RECV-001
title: DSO 与应收质量
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
domain: cash_and_working_capital
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [FIN-QUAL-001]
related_code: []
---

# DSO 与应收质量

- **定义**：应收周转天数（DSO）= 平均应收 / 收入 × 期间天数；配套逾期率、坏账率构成应收质量组。
- **业务目的**：衡量回款速度与信用风险敞口。
- **输入**：应收账款（期初期末）、收入、账龄/逾期口径（内部数据，L2+）。
- **规则**：应收含应收票据与否须声明；季节性业务用月末平均而非两点平均；逾期/坏账属内部过程事实（L2/L3），公开披露不可得。
- **适用**：内部月度经营分析（授权后）与公开披露的粗粒度 DSO。
- **不适用**：公开数据推断逾期率（披露不足）。
- **常见误用**：期末单点应收粉饰 DSO；把 DSO 延长一律解读为恶化（可能是收入确认节奏）。
- **来源与核验**：菜鸟 CFO Metrics 红黄绿灯报表（应收/坏账/逾期/对账完成率）为治理模板实证；数据熊应收模型 ×3。
- **FLOW 影响**：O2 经营指标候选（43 指标含回款类）；红黄绿灯治理模板（见 OPS 卡）的锚定指标。
