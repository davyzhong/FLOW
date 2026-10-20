---
doc_id: FLOW-ARCH-SYSTEM-001
title: 系统架构
doc_type: architecture
status: approved
version: 1.1
created_at: 2026-09-12
updated_at: 2026-10-21
owner: FLOW
decision_refs: [D029, D045, D055]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: repository
supersedes: []
superseded_by: null
---

# 系统架构（聚合视图）

> 本页组合既有细节，不复制正文；细节以链接目标为准。

- **当前单机运行时**：FastAPI（services/api，Python 3.13）+ Next.js/React（apps/web）+ SQLite 单文件 + 本地内容目录；同步处理，由 `make flow` 在本机启动。PostgreSQL/Redis/MinIO Compose 仅保留给历史兼容性测试与 CI。详见 [flow-v1-runtime](../architecture/flow-v1-runtime.md)（原位）。
- **域对象**：见 [flow-v1-domain-objects](../architecture/flow-v1-domain-objects.md)（原位）。
- **当前态（implemented）**：阶段 7 单机冷启动、离线展示与集成门禁分片已验收；7a 仍在视觉和文档收敛。详细能力见 [能力地图](../20_product/CAPABILITY_MAP.md)，准确状态见 [唯一路线图](../50_plans/CURRENT_ROADMAP.md)。
- **后续范围**：真实企业内部试点及多人权限暂缓，按 D055 与唯一路线图决定启动时机。
- **外部依赖**：Chromium（PDF）、GitHub Actions、HKEX 披露源。
- **当前单机原型范围外**：总账、多租户、自动因果引擎。
