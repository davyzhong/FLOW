# FLOW Pilot Readiness Phase 2 — 最小安全部署计划

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本计划仍是当前推进依据，但仅 Task A/B 的 API 认证及浏览器登录会话已实现并有定向验收；以[认证运行说明](../../operations/authentication.md)中的配置与实际路由行为为准。Task C–G（密钥与部署加固、备份恢复、日志、完整出口门禁及阶段证据）尚未完成；`make test-security-deployment-e2e` 仍是计划目标，不能直接当作现有命令。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **Execution rule:** Apply `superpowers:test-driven-development` to every behavior change,
> `superpowers:systematic-debugging` to failures, and
> `superpowers:verification-before-completion` before closing the phase. Keep the seven
> root-level user archive files untracked and out of every commit.
>
> **前置**：Phase 1（用户闭环）已完成，出口门禁 `make test-user-closure-e2e` 已绿。

**Goal:** 让系统可以安全部署到真实服务器并对外开放给真实用户：API 有认证边界、密钥不进
仓库、数据库与对象存储有备份与恢复演练、部署有 HTTPS 与回滚方案、日志可追踪。

**Product boundary:** 不做多租户/SSO/角色体系（单租户单用户起步）；不做 KMS 级密钥管理
（.env + 服务器文件权限起步）。安全能力以"试点所需最小集"为限。

## Exit gate

```bash
make test-security-deployment-e2e
```

## Task A — API 认证边界（TDD）

- 新增 `Settings.auth_token: str | None`：未配置 = 本机开发模式（不鉴权）；配置后所有
  `/api/v1` 路由（除 `GET /health`）要求 `Authorization: Bearer <token>`，constant-time
  比较，否则 401 `{code:"unauthorized"}`。
- RED：`tests/api/test_auth_boundary.py`（无 token 401 / 错 token 401 / 正确 token 200 /
  health 豁免 / 未配置时开放）。
- 前端代理（`app/api/v1/[...path]/route.ts`）从服务端环境读取同一 token 自动附加，
  浏览器不接触凭据。

## Task B — 登录会话（浏览器入口）

- Next 中间件：未持有有效会话 cookie 时，除 `/api/health` 外重定向到 `/login`；
- `/login` 单用户凭据页（环境变量 `FLOW_WEB_PASSWORD`），登录后设置 HttpOnly 会话 cookie；
- 代理仅在会话有效时转发 `/api/v1`。

## Task C — 密钥出仓

- `infra/compose.yaml` 明文口令改为 `${VAR}` 注入；提供 `.env.example`；
- `services/api/.env`、根 `.env` 均确认 gitignored；文档补密钥轮换说明。

## Task D — 备份与恢复演练

- `scripts/backup_postgres.sh`：pg_dump + gzip + 保留策略（7 日滚动）；
- `scripts/backup_objects.sh`：MinIO 对象目录同步快照；
- `scripts/restore_drill.sh`：从最新备份恢复到空实例并跑验收子集（health + workspace + 指标抽查）；
- `make backup / make restore-drill` 目标。

## Task E — 网络边界与部署拓扑

- compose 中 postgres/redis/minio 移除宿主端口暴露（仅内网）；
- 生产部署文件 `infra/compose.prod.yaml` + Caddy HTTPS 反代（自动证书）；
- 部署/回滚 runbook：`docs/operations/deployment.md`。

## Task F — 结构化日志与关联 ID

- API 中间件注入 `X-Request-ID`（缺省生成）并贯穿响应头与日志；
- uvicorn/celery 日志 JSON 化开关（`flow_log_json=1`）。

## Task G — 验收门禁与证据

- `make test-security-deployment-e2e`：认证拒绝/放行、备份→恢复演练、健康检查、日志关联 ID；
- CI workflow 增加 `security-deployment` job；
- 证据文档 `docs/implementation/phase-pilot-2-security-deployment.md`、PROJECT_STATE、
  决策日志条目、绿色提交打 tag。

## Explicitly deferred

- 多租户、SSO、角色权限体系；KMS/HSM；ERP 连接器；邮件/聊天分发。
