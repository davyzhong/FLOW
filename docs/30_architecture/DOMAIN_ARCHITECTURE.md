---
doc_id: FLOW-ARCH-DOMAIN-001
title: 领域架构
doc_type: architecture
status: approved
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D045, D053]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: domain
supersedes: []
superseded_by: null
---

# 领域架构（双轨共享底座）

> **2026-09-13 注记**：D045 的"双轨"框架已被 D053 取代为"三层两模块"（共享专业底座 + 公开财报模块 + 企业内部工作台）。本页描述的共享底座与数字同源约束继续有效；"两条轨道"应读作共享底座上的两组既有页面，财务与经营指标在目标结构中同属内部工作台的固定分析对象。

一套底座：来源/事实/指标语义/确定性引擎/证据复核/界面体系。两条轨道仅数据定义不同（D045）：

- **财务分析轨**：statements（四表一注）、metric-library、objective reports、investigation、四问、reports。
- **经营分析轨**：operations（严格期间事实、六主题、状态灯、多格式快照）。
- **共享身份链**：同一指标快照身份链；两轨数字同源；经营轨 demo 只读消费已发布快照。

领域知识口径见知识库 `30_domain_handbooks/`（flow-knowledge-2026-09-12.1）。
