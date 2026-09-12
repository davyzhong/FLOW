---
doc_id: TECH-COPILOT-001
title: Copilot 回答约束与推断分离
doc_type: knowledge-card
status: canonical
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-W4-jiejue, GRP-D-wiki]
authority_level: D
sensitivity: public
domain: finance_ai_governance
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [METHOD-QA-001]
related_code: [apps/web]
---

# Copilot 回答约束与推断分离

- **定义**：AI 回答按「客观事实（冻结事实+计算）→ 证据支持的推断（显式标注置信与依据）→ 建议行动」三层分离输出，客观层不得掺入生成内容。
- **业务目的**：可审计性；防 AI 幻觉污染财务事实。
- **输入**：冻结事实集、推断规则、会话上下文。
- **规则**：事实层只引用冻结事实与确定性计算；推断层必须挂证据引用；无证据时显式「不可判断」而非编造；few-shot 语料须来源核验+脱敏。
- **适用**：四问工作台、Copilot、报告生成。
- **不适用**：无。
- **常见误用**：让模型自由发挥口径；推断不标依据；用提示词硬编码当日数据。
- **来源与核验**：D049 方向（客观→推断→行动顺序）+ 解决方案研究所「一报一会」闭环与知识库治理文章 + wiki AI 工程簇。
- **FLOW 影响**：Copilot 评测（test_copilot_evals）与四问工作台的回答分层即本卡实现。
