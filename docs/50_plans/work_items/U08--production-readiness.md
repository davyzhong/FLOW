---
doc_id: FLOW-WI-U08
title: U08 生产就绪收口
doc_type: work-item
status: active
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001, FLOW-ARCH-SEC-001]
acceptance_refs: [U8-deploy-acceptance]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: deployment
supersedes: []
superseded_by: null
---

# U08 生产就绪收口

- **范围**：真实存储完整旅程验收、HTTPS 部署拓扑、统一部署验收。
- **已完成**：备份恢复演练（done）；结构化日志 U8-C（088977b：JSON 行、旅程关联、敏感遮蔽）。
- **验收**：生产栈端到端（冻结→发布→下载→SHA-256 校验）+ HTTPS 拓扑文档 + 部署清单核对。
- **授权边界**：不涉及产品合同变更；操作手册落 70_operations。
- **证据**：完成后在 60_delivery 登记验证记录并回写 ROADMAP。
