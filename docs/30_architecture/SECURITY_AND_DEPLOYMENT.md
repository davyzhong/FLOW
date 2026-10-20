---
doc_id: FLOW-ARCH-SEC-001
title: 安全与部署
doc_type: architecture
status: approved
version: 1.1
created_at: 2026-09-12
updated_at: 2026-10-21
owner: FLOW
decision_refs: [D003, D055]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: deployment
supersedes: []
superseded_by: null
---

# 安全与部署（聚合视图）

- **认证**：单机单用户密码 + 会话 + 服务端 Bearer + 同源代理（[authentication](../operations/authentication.md) 原位）；多角色/SSO 暂缓。
- **普通运行**：`make flow-init` 初始化 SQLite 与本地内容目录，`make flow` 在回环地址启动 Web/API；[运行架构](../architecture/flow-v1-runtime.md)列明启动、备份和恢复边界。`infra/compose.yaml` 中的 PostgreSQL/Redis/MinIO 只供历史兼容性测试与 CI，不是本机使用前置条件。
- **运行安全**：保留结构化日志、旅程关联与敏感遮蔽；真实企业数据及多人部署未在 D055 单机原型中验收。
- **敏感边界**：内部数据授权门禁（GOV-AUTH-001）；授权/降敏须新知识版本与新发布。
