---
doc_id: FLOW-PROD-BOUND-001
title: 产品边界
doc_type: product
status: canonical
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D039, D049, D050]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: product
supersedes: []
superseded_by: null
---

# 产品边界（不可越过）

1. **事实/推断/行动三层分离**：冻结事实与确定性计算为第一层；推断必须挂证据与置信标注；建议行动属第三层。数学分解不冒充业务因果（D049）。
2. **缺失不补造**：财报缺表阻断发布（不 500 也不假成功）；公开数据不倒造企业分录；预测依赖与确定性公式分开。
3. **AI 不创造数字**：客观层禁止生成内容；few-shot 语料须核验脱敏（TECH-COPILOT-001）。
4. **内部数据授权门禁**：内部数值/明细进产品须 U9/O5 授权+脱敏+审计（GOV-AUTH-001）；示例阈值不得成为默认值。
5. **双轨数字同源**：不允许两套口径各自计算（D045）。
6. **不建设总账**；经营轨主观归因在证据治理就绪前不得进入正式输出。
