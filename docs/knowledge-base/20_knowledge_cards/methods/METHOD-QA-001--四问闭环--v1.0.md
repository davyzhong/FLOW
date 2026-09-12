---
doc_id: METHOD-QA-001
title: 四问闭环（发生了什么/为什么/会怎样/怎么办）
doc_type: knowledge-card
status: verified
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-W1-wechat, GRP-D-wiki, GRP-W4-jiejue]
authority_level: D
sensitivity: public
domain: operational_efficiency
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [METHOD-REPORT-001]
related_code: [apps/web]
---

# 四问闭环

- **定义**：经营问题按「发生了什么（事实）→ 为什么（拆解归因）→ 会怎样（推演预警）→ 怎么办（行动）」四段递进的分析闭环。
- **业务目的**：防止分析停留在描述层，强制走到可执行动作。
- **输入**：指标异动事实 + 维度拆解路径 + 责任维度。
- **规则**：第一问只允许冻结事实（客观口径）；第二问拆解到可归因粒度（量价费/区域/客户/单品）；第三问情景推演与事实分离标注；第四问行动须挂责任人与期限。
- **适用**：月度经营分析、专项异动分析。
- **不适用**：纯客观财报分析阶段（U5 三章节叙事是本卡的客观子集）。
- **常见误用**：跳过第一问直接归因；把假设性推演当事实呈现（违反 FLOW 推断分离原则）。
- **来源与核验**：数据熊「五步闭环法」+ wiki 路径拆解框架系列 + 数研复盘狮开放/封闭提问递进；方法结构多源趋同。
- **FLOW 影响**：四问工作台（U7 已实现）的方法层权威定义；Copilot 提问设计的骨架。
