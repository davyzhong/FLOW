---
doc_id: FLOW-PROD-USERS-001
title: 用户与工作区
doc_type: product
status: canonical
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D010, D045]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: product
supersedes: []
superseded_by: null
---

# 用户与工作区

| 工作区 | 受众 | 入口 | 职责 |
|---|---|---|---|
| 财务分析工作区 | Finance BP | /data、/statements、/metric-library、/reports、调查与四问工作台 | 财报客观分析、指标口径管理、报告生产 |
| 经营分析工作区 | 经营/业务管理者 | /operations | 严格期间经营事实、六主题快照、状态灯与行动 |

- 两工作区共享同一底座与指标快照身份链；双轨数字同源（D045 边界）。
- 认证模型：单用户密码 + 会话 + 服务端 Bearer（无多角色/租户承诺）。
- 双工作区 ≠ 双角色页面（D010 的单角色限定被 D045 明确取代）。
