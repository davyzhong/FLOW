---
doc_id: FLOW-OPS-NGINX-TLS-001
title: U8-B HTTPS 反向代理拓扑（开发自签）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
applies_to: deployment
knowledge_release: pre-static-obsidian-2026-09-12T15:46+08:00
decision_refs: [D049]
supersedes: []
superseded_by: null
source_refs: [docs/superpowers/plans/2026-09-07-unified-next-plan.md]
related_code: [infra/compose.yaml, infra/nginx/nginx.conf]
confidentiality: project-internal
---

# U8-B HTTPS 拓扑（开发自签）

部署图：浏览器 → nginx:443（TLS 终止，自签 dev-tls）→ /api/ → api:8000；/ → web:3000。
80 端口 301 跳转 https。安全头：HSTS/nosniff/DENY/referrer-policy。
生产替换：真实 CA 证书 + server_name，凭据仍只走服务端 env（API 侧 Bearer 边界不变）。
