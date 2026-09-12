---
doc_id: FLOW-ARCH-SEC-001
title: 安全与部署
doc_type: architecture
status: approved
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D003]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: deployment
supersedes: []
superseded_by: null
---

# 安全与部署（聚合视图）

- **认证**：单用户密码 + 会话 + 服务端 Bearer + 同源代理（[authentication](../../operations/authentication.md) 原位）；无多角色/SSO 承诺。
- **部署**：docker compose（infra/compose.yaml）；MinIO quay.io 镜像；部署方式中立（D003）。
- **运行安全（U8 进行中）**：结构化日志 JSON 行/旅程关联/敏感遮蔽（U8-C 已交付）；真实存储完整旅程与 HTTPS 拓扑待收口。
- **敏感边界**：内部数据授权门禁（GOV-AUTH-001）；授权/降敏须新知识版本与新发布。
