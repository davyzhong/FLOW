---
doc_id: GOV-METRIC-001
title: 指标全要素配置与版本留痕
doc_type: knowledge-card
status: verified
version: "1.0"
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
source_refs: [GRP-W1-wechat]
authority_level: D
sensitivity: public
domain: finance_ai_governance
effective_from: 2026-09-12
supersedes: []
superseded_by: null
related_knowledge: [OPS-CFO-001]
related_code: [services/api/src/flow_api]
---

# 指标全要素配置与版本留痕

- **定义**：指标配置 = 公式 + 口径 + 目标值 + 预警阈值 四要素成组定义，任何变更版本留痕。
- **业务目的**：指标含义稳定可追溯；目标与预警不漂移。
- **输入**：指标定义、口径说明、目标序列、阈值规则。
- **规则**：四要素同版本管理；变更走草稿→验证→激活→退役生命周期；集团—区域—仓库—物料多级钻取继承同一指标身份。
- **适用**：指标库治理（C 系列）与经营驾驶舱。
- **不适用**：一次性测算（非注册指标）。
- **常见误用**：只管公式不管目标/阈值；阈值变更不留版本导致历史灯色不可解释。
- **来源与核验**：数据熊 2026-08 指标五件套系列（公式+口径+目标+阈值配置与版本留痕、多级钻取）。
- **FLOW 影响**：指标库 v1.1 与 C01-C06 治理（草稿/验证/激活/退役、审计、影响沙箱）即本卡的产品化实现。
