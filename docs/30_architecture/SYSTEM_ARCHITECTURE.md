---
doc_id: FLOW-ARCH-SYSTEM-001
title: 系统架构
doc_type: architecture
status: approved
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decision_refs: [D029, D045]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: repository
supersedes: []
superseded_by: null
---

# 系统架构（聚合视图）

> 本页组合既有细节，不复制正文；细节以链接目标为准。

- **运行时**：FastAPI（services/api，Python 3.13）+ Next.js/React（apps/web）+ PostgreSQL（迁移头 0024）+ MinIO（Quay 镜像）。详见 [flow-v1-runtime](../../architecture/flow-v1-runtime.md)（原位）。
- **域对象**：见 [flow-v1-domain-objects](../../architecture/flow-v1-domain-objects.md)（原位）。
- **当前态（implemented）**：Phase 1–10 + B/C/U/O 系列已交付能力（见 [能力地图](../20_product/CAPABILITY_MAP.md)）。
- **设计态（designed）**：U8 部署拓扑收口、U9/O5 内部试点扩展。
- **外部依赖**：Chromium（PDF）、GitHub Actions、HKEX 披露源。
- **out-of-scope**：总账、多租户、自动因果引擎。
