---
doc_id: FLOW-OPS-S01-KIMI-CORRECTION-20260914
title: Kimi K3 路由与权限车道修正说明（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: s01-route-policy-lane
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
supersedes: []
superseded_by: null
source_refs:
  - docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md
  - docs/40_specs/security/route-inventory-v1.tsv
related_code:
  - services/api/src/flow_api/security/route_policy.py
commit_refs: ["0841ff9", "997c1ab", "a49a10f"]
evidence_refs: []
confidentiality: project-internal
---

# Kimi K3 路由与权限车道修正说明

## 当前裁决

- v1 `0841ff9` 整体废弃，不 cherry-pick。
- v2 `997c1ab`/`a49a10f` 已通过 `91bfb56` 合入 main，但只完成 registry、TSV parser、loader 查询和 mini-app 测试底稿；不得据此标 Task 2B verified。
- 不回滚整条 main；在新的 v3 窄分支补齐真实路由接线和测试。
- Task 6B 延后到 Wave 2 绿色后，用单独分支只提交一份 review 备忘。
- 当前 inventory 已登记 `GET /api/v1/metric-library/coverage` 和已挂载的 `/api/v1/modules`；必须从 `PENDING_MOUNT_ROUTES` 移除 modules，并将它从匿名豁免改为符合“仅 health 匿名”的真实认证/授权入口。

## 必须修正

1. 以协调者冻结的 `main@774799e7` 之后的 R1 security checkpoint 新建 `codex/s01-route-policy-v3`；不 merge v1，不重新 cherry-pick 已在 main 的 v2。
2. 先和安全 owner 固化 401 audit bridge、durable writer provider、role+action owner semantics，并先写失败交叉测试。
3. 按计划白名单逐个真实 route 接 `require_action`。publishing/operations 只登记为 security owner 的串行待接线，不修改其 route。
4. scanner 必须检查真实 `APIRoute` dependency/introspection：每个非豁免入口的 action、loader 和 policy 唯一匹配；只比 method/path 不合格。
5. 对真实入口逐项测试 401、403、allow、跨企业、旧 Bearer、AI publish deny、hidden-write GET，并断言拒绝时 handler 没有执行。
6. 删除或忽略 request body/query 中的 actor/reviewer/operator/enterprise 身份；业务与审计只使用 Principal。兼容字段冲突按规格返回 409，但 AuditEvent.actor 永远是 Principal。
7. owner loader 必须真正解析可信 owner/assignment。无法解析 finance_bp owner 的入口先 blocked；不得用函数名假装 owner，也不得令 analyst/AI 的合法动作被全局 owner-required 误拒。
8. `require_action` 自己从权威 entry 取唯一 loader，或严格 identity 校验传入 loader；防止同 resource_type 的 owner/non-owner loader 被替换。
9. UUID/JSON/不存在对象/legacy lineage/module_kind 错误全部转为类型化 deny/error，并在返回前 durable audit；不得在 audit barrier 前裸异常。
10. resource loader 只使用一个专用只读预加载 Session（autoflush off、无 commit）；业务 handler 的写 Session 与其隔离，且不得在 durable allow 前创建副作用或触发 autoflush。Task 6 关闭前清除 `PENDING_MOUNT_ROUTES` 过渡例外。
11. 将 route-policy 与 auth-boundary 真实测试接入 required CI；当前错误完成声明先降为 delivery 合法的 `draft`，在最新 integration、最新迁移上全绿后才改为 `verified`。

## 文件范围

只允许 route-policy、计划逐项列出的七组 routes/schemas/models、指定测试和 route inventory。不得重写 Principal/authorize/audit ORM/迁移，不得修改前端、权威状态、README 或知识库 manifest。

## Task 6B 纪律

从 Wave 2 green SHA 新建规范分支，只创建计划指定 review 文件。补 D052–D054，重新核对 U09/O05/U10，不修改 `PROJECT_STATE`、backlog、capability map、manifest 或 hash；保持 `status: open`，由协调者应用裁决。
