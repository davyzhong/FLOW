---
doc_id: FLOW-PLAN-THREE-AGENT-PARALLEL-001
title: FLOW 三智能体并行重构实施计划
doc_type: plan
status: archived
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-PLAN-POST-U8-BOUNDARY-001, FLOW-DESIGN-THREE-AGENT-ORCH-001, FLOW-WI-S01]
acceptance_refs: [three-agent-file-ownership-gate, s01-task6-security-gate, s01-task9-full-chain-gate]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: s01-task6-task10-orchestration
supersedes: []
superseded_by: FLOW-HANDOFF-STRATEGY-20260912
---

# FLOW 三智能体并行重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保持 U8 可恢复基线与 S01 合同不变的前提下，让 GPT-5.6 Sol、Kimi K3、GLM 5.3 并行完成 Task 6–10，并由主协调者无歧义地验收和集成。

**Architecture:** 先串行冻结安全 ABI，再把安全核心、敏感路由和前端入口分到独立 worktree；后续以波次串行合并。数据库迁移、生成契约、路线图状态和阶段关闭只由单一所有者处理。

**Tech Stack:** Git worktree、Python 3.13、FastAPI、SQLAlchemy 2、Alembic、PostgreSQL、pytest、Next.js 16、React 19、Vitest、Playwright、GitHub Actions。

---

## 文件结构与所有权

| 单元 | 路径 | 所有者 |
|---|---|---|
| 编排设计 | `docs/superpowers/specs/2026-09-13-flow-three-agent-parallel-orchestration-design.md` | 主协调者 |
| 使用手册 | `docs/70_operations/three-agent-parallel-execution-runbook.md` | 主协调者 |
| 总交接 | `HANDOFF.md` | 主协调者 |
| 安全核心 | `services/api/src/flow_api/security/`（除 `route_policy.py`） | GPT-5.6 Sol |
| 敏感入口 | `security/route_policy.py`、指定 route/schema/tests | Kimi K3 |
| 模块与 UI | `modules/**`、模块 API/AST 测试、`apps/web` 指定入口与导航 | GLM 5.3 |
| 状态与交付 | `PROJECT_STATE`、`CURRENT_ROADMAP`、S01 work-item、views、delivery | 主协调者 |

`base_sha` 按 checkpoint 维护：Bootstrap 使用 Gate 0 SHA；Wave 1 使用 Bootstrap CI 绿色 SHA；Wave 2 使用 Task 6 CI 绿色 SHA；Wave 3 使用 Wave 2 CI 绿色 SHA。同一波次共享一个 base，后续波次不得继续使用旧 base。

## Task 0：主协调者建立 Gate 0

**Files:**
- Modify: `docs/40_specs/security/internal-workbench-rbac-audit-v1.md`
- Modify: `docs/40_specs/SPEC_INDEX.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Modify: `docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md`
- Modify: `docs/50_plans/README.md`
- Modify: `docs/superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md`
- Create: `config/ci/required_jobs_s01.txt`
- Create: `scripts/ci/verify_workflow_jobs.py`
- Test: `scripts/tests/test_verify_workflow_jobs.py`

- [ ] **Step 1: 确认最新 main 与 CI**

Run: `git fetch origin --prune && git status --short --branch && gh run list --branch main --limit 3`

Expected: 工作区干净；包含 Task 5 的最新 main CI 为 success；迁移头事实指向 `0025_enterprise_cycle`。

- [ ] **Step 2: 修正状态漂移**

把 PROJECT_STATE、READING_ORDER、CURRENT_ROADMAP、S01 work-item 更新为：Task 1–5 完成，Task 6 进入合同冻结；不得提前声称 Task 6 完成。

- [ ] **Step 3: 把安全规格降为 review 后修订**

写入设计文档 §5 的安全 ABI、旧 Bearer 截止、public/enterprise scope、audit intent/outcome、365 天最低保留和事务失败语义；从最终 `api_router` 生成完整 route inventory，明确纳入 copilot/orchestration 和隐藏写 GET；固定 publication 的 `prepare_intent → caller commit → execute_object → finalize_success/failure → caller commit` 调用序列、`PreparedPublication`/`AuditContext` 字段和四个精确签名。Kimi 只登记 publishing/operations 的 Sol owner，不并行修改这两条 route。

- [ ] **Step 4: 对修订规格做独立审查并取得用户批准**

Expected: `review` 状态下最多三轮审查并清零 P1/P2；随后由用户明确批准最终字节，才把规格和 SPEC_INDEX 转回 `approved`。用户未批准时不得用门禁脚本代替批准。

- [ ] **Step 5: 重跑门禁**

Run: `python3 scripts/documentation/require_approved_specs.py FLOW-SPEC-MODULE-BOUNDARIES-V1 FLOW-SPEC-FINANCIAL-FACTS-V2 FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1 && make docs-check && git diff --check`

Expected: 全部 PASS。

- [ ] **Step 6: 登记执行权威关系**

在原 post-U8 计划 Task 6 前加入“Task 6–10 由本计划编排”的明确链接；CURRENT_ROADMAP、S01 work-item 与计划 README 同时链接两份计划，说明原计划定义范围、本计划定义并行执行，禁止形成第二路线图。

- [ ] **Step 7: 创建集成基线**

记录 `base_sha`，创建 `codex/s01-parallel-integration` 并推送；所有执行者必须从这个 SHA 建分支，不从各自旧会话继续。

- [ ] **Step 8: 建立 FLOW CI 结果核验器**

`config/ci/required_jobs_s01.txt` 逐行登记 `static-python`、`integration`、`intake-e2e`、`analysis-invariants`、`unit`、`data-contract`、`metrics-known-answers`、`static-web`、`migrations`、`investigation-e2e`、`dashboard`、`publishing-golden`、`user-closure-e2e`、`copilot-evals`、`contracts`、`smoke`、`module-boundaries-e2e`。校验器必须接收 run id 与 expected SHA，断言 workflow 名为 FLOW CI、headSha 精确匹配、conclusion success、清单中每个 job success 且无 skipped；新增 job 在尚未接入的 checkpoint 由清单的版本化注释/阶段参数明确豁免，不能静默缺失。

Run: `gh run watch <run_id> --exit-status && python3 scripts/ci/verify_workflow_jobs.py --run-id <run_id> --expected-sha <checkpoint_sha> --phase <bootstrap|task6|wave2|final>`

- [ ] **Step 9: 提交并推送**

Commit: `docs(security): freeze S01 parallel implementation contracts`

## Task 1：GPT-5.6 Sol 交付安全 ABI Bootstrap

**Files:**
- Create: `services/api/src/flow_api/security/__init__.py`
- Create: `services/api/src/flow_api/security/principal.py`
- Create: `services/api/src/flow_api/security/authorization.py`
- Create: `services/api/src/flow_api/security/audit.py`（协议与事件输入模型，不含 ORM）
- Test: `services/api/tests/security/test_authorization.py`

- [ ] **Step 1: 从 integration base 创建独立 worktree `codex/s01-security-abi`。**
- [ ] **Step 2: 先写失败测试**：全部角色×动作矩阵、deny-by-default、跨企业拒绝、规则不可自批、AI 无发布权、public scope 不等于跨企业通配。
- [ ] **Step 3: 运行目标测试确认因模块不存在而 FAIL。**
- [ ] **Step 4: 实现最小不可变类型和纯 `authorize`**；同时冻结 audit writer Protocol 与规格已批准的 `AuditContext`/`PreparedPublication` 事务 ABI，使后续车道不猜测接口。
- [ ] **Step 5: 运行测试、ruff、mypy 与 diff-check。**

Run: `cd services/api && uv run pytest tests/security/test_authorization.py -v && uv run ruff check src tests && uv run mypy src`

- [ ] **Step 6: 提交并推送。**

Commit: `feat(security): define principal and authorization core`

- [ ] **Step 7: 主协调者审查并先合并 Bootstrap，同时修改 `.github/workflows/ci.yml` 将 `tests/security/test_authorization.py` 接入 `unit`。** 推送 Bootstrap checkpoint，使用 FLOW CI 核验器确认授权测试所在 job 绿色后，才发布 Wave 1 的新 `base_sha`。

## Task 2A：Sol 完成身份、审计持久化和 0026

**Files:**
- Modify: `services/api/src/flow_api/security/audit.py`
- Create: `services/api/src/flow_api/security/models.py`
- Modify: `services/api/src/flow_api/api/auth.py`
- Modify: `services/api/src/flow_api/settings.py`
- Modify: `services/api/src/flow_api/main.py`
- Modify: `services/api/src/flow_api/infrastructure/models/__init__.py`
- Modify: `services/api/src/flow_api/publishing/publication.py`
- Modify: `services/api/src/flow_api/operations/publication.py`
- Modify: `services/api/src/flow_api/infrastructure/object_store.py`
- Create: `services/api/migrations/versions/0026_security_audit.py`
- Test: `services/api/tests/integration/test_security_schema.py`
- Test: `services/api/tests/integration/test_audit_atomicity.py`
- Test: `services/api/tests/publishing/test_publication.py`
- Test: `services/api/tests/operations/test_operations_publication.py`
- Test: `services/api/tests/integration/test_object_store.py`
- Test: `services/api/tests/security/test_principal_resolution.py`

- [ ] **Step 1: 从 Bootstrap SHA 创建 `codex/s01-security-audit`。**
- [ ] **Step 2: 写失败测试**：credential 解析、非 development fail-fast、旧 Bearer 截止、角色绑定、AuditEvent 字段、UPDATE/DELETE trigger、迁移往返。
- [ ] **Step 3: 实现 ORM、writer、身份配置和 0026**；0026 的 `down_revision` 必须是 `0025_enterprise_cycle`。
- [ ] **Step 4: 按已批准 ABI 收敛发布 service 事务边界**：实现 `prepare_intent`、`execute_object`、`finalize_success`、`finalize_failure`，database mutation 与 audit 复用 Session；service/writer 不自行 commit。本分支不修改调用 route。
- [ ] **Step 5: 写故障注入测试**：audit intent 失败时对象存储未调用；对象写失败时业务不发布且 failure outcome 存在；内部 service 不偷跑 commit。
- [ ] **Step 6: 在一次性数据库运行 schema、trigger、atomicity 和 migration 测试。**

Run: `cd services/api && uv run pytest tests/security tests/integration/test_security_schema.py tests/integration/test_audit_atomicity.py tests/integration/test_migrations.py tests/publishing/test_publication.py tests/operations/test_operations_publication.py tests/integration/test_object_store.py -v`

- [ ] **Step 7: 静态检查、提交并推送。** 本车道现有 CI 只作参考，新增门禁由主协调者在 integration 接入。

Commit: `feat(security): persist scoped identities and append-only audit`

## Task 2B：Kimi K3 完成路由盘点与权限接线

**Files:**
- Create: `services/api/src/flow_api/security/route_policy.py`
- Modify: `services/api/src/flow_api/api/routes/intake.py`
- Modify: `services/api/src/flow_api/api/routes/investigations.py`
- Modify: `services/api/src/flow_api/api/routes/metric_library.py`
- Modify: `services/api/src/flow_api/api/routes/objective_reports.py`
- Modify: `services/api/src/flow_api/api/routes/statements.py`
- Modify: `services/api/src/flow_api/api/routes/copilot.py`
- Modify: `services/api/src/flow_api/api/routes/orchestration.py`
- Modify: `services/api/src/flow_api/api/schemas/intake.py`
- Modify: `services/api/src/flow_api/api/schemas/investigation.py`
- Modify: `services/api/src/flow_api/api/schemas/metric_library.py`
- Modify: `services/api/src/flow_api/api/schemas/publishing.py`
- Modify: `services/api/src/flow_api/api/schemas/statement.py`
- Modify: `services/api/src/flow_api/api/schemas/copilot.py`
- Modify: `services/api/src/flow_api/investigation/models.py`
- Test: `services/api/tests/api/test_auth_boundary.py`
- Test: `services/api/tests/api/test_copilot.py`
- Test: `services/api/tests/api/test_orchestration_api.py`
- Test: `services/api/tests/security/test_route_policy.py`

- [ ] **Step 1: 从 Bootstrap SHA 创建 `codex/s01-route-policy`；不得等待或复制 Sol 的 ORM 实现。**
- [ ] **Step 2: 输出机器可读的全路由 inventory**：method、normalized path、actual side effect、action、resource loader、owner 或只读豁免理由；GET 隐藏写、copilot 模型调用、orchestration build 必须登记。publishing/operations 登记 owner=Sol 和 pending serial wiring，本分支不得修改其 route。
- [ ] **Step 3: 写失败的路由扫描和逐入口测试**：未登记敏感路由、401、跨企业/跨角色 403、合法 allow、旧 Bearer 无发布权、actor 不可由请求体伪造。
- [ ] **Step 4: 实现集中 route policy 与 dependency 接线**，使用 Bootstrap 的 Protocol 和测试 fake，不实现第二套审计存储。
- [ ] **Step 5: 运行 route-policy 与 API 目标测试；允许需要真实 0026 的集成断言在合并后由主协调者执行，但本分支纯测试必须全绿。**
- [ ] **Step 6: 静态检查、文件白名单检查、提交、推送。** 未列文件一律触发停机并由主协调者修订工作单，不使用可选 glob。

Commit: `feat(security): enforce policy across sensitive routes`

## Task 2C：GLM 5.3 完成两模块前端入口

**Files:**
- Create: `apps/web/app/public/page.tsx`
- Create: `apps/web/app/internal/page.tsx`
- Create: `apps/web/components/modules/module-landing.tsx`
- Create: `apps/web/components/modules/module-landing.css`
- Modify: `apps/web/components/dashboard/workflow-nav.tsx`
- Modify: `apps/web/e2e/navigation.spec.ts`
- Test: `apps/web/tests/components/workflow-nav.test.tsx`
- Test: `apps/web/e2e/module-boundaries.spec.ts`
- Create: `scripts/test_module_boundaries_e2e.sh`
- Modify: `Makefile`

- [ ] **Step 1: 从 Bootstrap SHA 创建 `codex/s01-module-ui`。**
- [ ] **Step 2: 写失败测试**：三个产品语义入口、旧路由兼容分组、AppShell、implemented/designed 状态、无虚假操作按钮。
- [ ] **Step 3: 使用设计 §5.4 固定 fixture 实现页面和导航**；不调用 `/api/v1/modules`，不修改 API client 和生成契约。
- [ ] **Step 4: 仿照现有 E2E runner 实现动态端口、受控启动和 cleanup trap，并运行 Vitest、lint、typecheck 和两个 Playwright 规格。**

Run: `npx --yes pnpm@10.17.1 --filter @flow/web exec vitest run tests/components/workflow-nav.test.tsx && npx --yes pnpm@10.17.1 --filter @flow/web lint && npx --yes pnpm@10.17.1 --filter @flow/web typecheck && make test-module-boundaries-e2e`

Expected: runner 自行分配端口并执行 `e2e/navigation.spec.ts e2e/module-boundaries.spec.ts`，退出后端口释放，全部 PASS。

- [ ] **Step 5: 提交并推送；分支保持待集成状态。**

Commit: `feat(web): add explicit public and internal module entrypoints`

## Task 3：主协调者关闭 Task 6

- [ ] **Step 1: 审查三个分支的提交、测试证据和文件白名单。**
- [ ] **Step 2: 先 merge Sol Task 2A，再 merge Kimi Task 2B；每个候选只跑本地目标/交叉测试，不先推远端 checkpoint。**
- [ ] **Step 3: 从两者合并后的 integration SHA 创建 `codex/s01-publication-route-wiring`，交给 Sol 串行修改 `services/api/src/flow_api/api/routes/publishing.py`、`services/api/src/flow_api/api/routes/operations.py`、`services/api/tests/api/test_publishing_api.py` 和 `services/api/tests/operations/test_operations_public_api.py`。** 使用最终 route_policy 接入权限，并严格执行 `prepare_intent → route commit → execute_object → finalize success/failure → route commit`；`test_auth_boundary.py` 仍由 Kimi 独占，主协调者只运行不修改。Sol 完成目标测试后以 `feat(security): secure publication transaction routes` 提交并推送；主协调者核对白名单、审查完整 diff、运行故障注入与全 route inventory 扫描，再以普通 merge commit 合入 integration。该分支未合并前禁止进入下一步或关闭 Task 6。
- [ ] **Step 4: 在最终路由集合上运行角色矩阵、route scanner、逐入口 API、0026 schema/trigger/migration 往返。**
- [ ] **Step 5: 验证 intent/outcome 审计和 publication 事务；发现 internal service commit、intent 未 durable 即对象写、无 failure outcome 或无审计外部副作用即阻断。**
- [ ] **Step 6: 主协调者独占修改 `.github/workflows/ci.yml`**：无数据库安全单测进入 `unit`，security schema/atomicity 由 `integration` 覆盖；不得只依赖本地测试。
- [ ] **Step 7: 运行 approved-spec、文档与 contracts-check；全部绿色后才更新 S01 为 Task 6 完成。**
- [ ] **Step 8: Task 6 security lanes 全部合并后推送一次 integration，使用 FLOW CI 核验器的 `task6` 阶段逐项确认清单 job success 且无 skip。** GLM UI commit 此时仍在未合并分支，不计入该 checkpoint。

## Task 4：GLM 5.3 完成 Task 7 模块边界

**Files:**
- Create: `services/api/src/flow_api/modules/shared_core/__init__.py`
- Create: `services/api/src/flow_api/modules/public_analysis/__init__.py`
- Create: `services/api/src/flow_api/modules/internal_workbench/__init__.py`
- Create: `services/api/src/flow_api/modules/registry.py`
- Create: `services/api/src/flow_api/api/routes/modules.py`
- Create: `config/modules/ownership_v1.yaml`
- Modify: `services/api/src/flow_api/api/router.py`
- Test: `services/api/tests/api/test_module_boundaries.py`
- Test: `services/api/tests/architecture/test_module_imports.py`
- Regenerate: `packages/contracts/openapi.json`
- Regenerate: `packages/contracts/src/schema.d.ts`

- [ ] **Step 1: 从 Task 6 CI 绿色的 integration SHA 创建 `codex/s01-module-boundaries`。**
- [ ] **Step 2: 先写 API、manifest 完整性与 AST 违规 fixture 的失败测试。**
- [ ] **Step 3: 实现 registry、facade、ownership 和只读 `/api/v1/modules`。**
- [ ] **Step 4: ownership 必须覆盖 Task 6 新增 security 文件；composition root 单独登记，禁止 public↔internal。**
- [ ] **Step 5: 从 FastAPI 重新生成契约并运行 contracts-check，禁止手改 JSON/d.ts。**
- [ ] **Step 6: 运行模块测试、`tests/api` 回归、ruff、mypy，提交并推送。**

Commit: `refactor(api): expose explicit product module boundaries`

并行只读审查：Kimi 复核路由 inventory/ownership 是否漏项；Sol 复核 `/modules` 未被错误视为敏感写入口。审查者不直接修改 GLM 分支。

## Task 5：主协调者集成 Task 7 与 Task 8

- [ ] **Step 1: 先合并 GLM Task 7，运行 API、AST、契约和 CI。**
- [ ] **Step 2: 从已通过的 Task 7 SHA 新建 `codex/s01-module-ui-integration`，由 GLM cherry-pick 已审的 UI commit 并只解决 UI 侧冲突。** 保留原已推送分支，不 rebase、不 force-push。
- [ ] **Step 3: 合并 Task 8，运行导航 unit、lint、typecheck 和 Playwright。**
- [ ] **Step 4: 主协调者更新 `.github/workflows/ci.yml`**：static-python 或独立 job 必须运行 `tests/architecture/test_module_imports.py`；static-web 必须运行导航 Vitest；新增 `module-boundaries-e2e` required job 调用 `make test-module-boundaries-e2e`。
- [ ] **Step 5: 更新 S01 当前领取项为 Task 9，生成计划视图；完成整个 Wave 2 后推送一次 integration。**
- [ ] **Step 6: 使用 FLOW CI 核验器确认目标 SHA、workflow success、阶段清单中每个 job success 且无 skip后启动 Wave 3。**

## Task 6A：GLM 5.3 执行 Task 9 全链技术验证

**Files:**
- Create: `scripts/verify_s01_upgrade_from_u8.sh`
- Test: `scripts/tests/test_s01_upgrade_gate.py`
- Create: `infra/compose.s01-acceptance.yaml`
- Regenerate: `packages/contracts/openapi.json`
- Regenerate: `packages/contracts/src/schema.d.ts`
- Modify: `docs/architecture/flow-v1-domain-objects.md`

- [ ] **Step 1: 从 Wave 2 绿色 SHA 创建 `codex/s01-full-verification`。**
- [ ] **Step 2: 重新生成契约并执行全链回归。**

Run: `make contracts && make contracts-check && make test-api && make test-web && make lint && make typecheck && make test-user-closure-e2e && make test-statements-e2e && make test-module-boundaries-e2e`
- [ ] **Step 3: 先写 runner 失败测试，再新增独立验收 compose 与 runner**：使用唯一 compose project 和 volume 启动专属 PostgreSQL、API、web、nginx；恢复 U8/0024 dump 后，专属 API 的 `DATABASE_URL` 必须指向该恢复库，nginx 使用动态 HTTPS 宿主端口。runner 用 trap 保留原始退出码并清理整个专属 project。
- [ ] **Step 4: runner 先核验备份完整 SHA，再在同一恢复库运行 `alembic upgrade head`、schema/trigger 测试；通过 HTTPS 读取恢复库独有的已知财报载荷，与 SQL 与冻结哈希三方对账，证明 nginx/API 没有误连常驻 `flow` 库。** 任何恢复、哈希、升级、绑定证明、HTTPS 或清理失败均返回非零。

Run: `FLOW_U8_BACKUP_PATH=/Users/qiming/workspace/FLOW/backups/u8-baseline/flow-u8-final.dump FLOW_U8_BACKUP_SHA256=1811ebb2666254158deb1a9e9189d4d860ba45b31c6008a4921be318a704daa4 FLOW_U8_CA_CERT=/Users/qiming/workspace/FLOW/infra/nginx/dev-tls.crt bash scripts/verify_s01_upgrade_from_u8.sh`
- [ ] **Step 5: 将机器证据写入忽略的 `work/s01-verification/` 并在交接中列出；交付记录由主协调者在最终复验后创建。任何 skip 令交付失败。**
- [ ] **Step 6: 提交生成契约与领域对象更新并推送。**

Commit: `test(acceptance): verify S01 upgrade from U8 baseline`

## Task 6B：Kimi K3 准备 Task 10 只读裁决备忘

**Files:**
- Create: `docs/80_reviews/2026-09-13-s01-work-item-disposition-review.md`

- [ ] **Step 1: 从 Wave 2 绿色 SHA 创建 `codex/s01-work-item-disposition-review`。**
- [ ] **Step 2: 以 `FLOW-REVIEW-S01-DISPOSITION-001`、`doc_type: review`、`status: open`、`subject_ref: FLOW-WI-S01` 和 `findings: []` 建立元数据头；逐条标注保留重命名、拆入公开 C、拆入内部工作台或取消，并保留证据继承与失效假设。**
- [ ] **Step 3: 在 review 文档中给出两个 gated backlog 的建议正文，但不创建 backlog 文件。**
- [ ] **Step 4: 不修改 U09/O05、U10、CAPABILITY_MAP、PROJECT_STATE、CURRENT_ROADMAP、S01 work-item、生成视图或 manifest，不声称 S01 completed。**
- [ ] **Step 5: 运行链接/metadata 检查，提交并推送草案。**

Commit: `docs(roadmap): draft post-S01 work item disposition`

## Task 6C：Sol 执行最终安全独立复核

- [ ] **Step 1: 只读审查 Task 9 最终代码和证据，重点检查 AI 发布拒绝、不可自批、跨企业、旧 Bearer 到期、隐藏写 GET、审计 UPDATE/DELETE 和外部副作用。**
- [ ] **Step 2: 输出按 P1/P2/P3 分类的审查报告，不直接修改 Task 9/10 分支。**
- [ ] **Step 3: P1/P2 未清零时阻断最终关闭。**

## Task 7：主协调者合并并关闭 S01

- [ ] **Step 1: 先合并 Task 9 技术证据，复跑关键命令并清零 Sol 的 P1/P2。**
- [ ] **Step 2: 合并 Kimi 的 review 备忘；主协调者据此创建/修改 U09/O05、U10、CAPABILITY_MAP 和两个 gated backlog。涉及取消或改变产品目标时依据 D052–D054 裁决并记录。**
- [ ] **Step 3: 主协调者创建 `docs/60_delivery/2026-09-13-post-u8-boundary-gate-verification.md`，只登记亲自复验的证据。**
- [ ] **Step 4: 只有退出条件全部有证据时更新 S01、CURRENT_ROADMAP、PROJECT_STATE 和 CAPABILITY_MAP。**
- [ ] **Step 5: 运行 `plan_views.py --write`、知识 manifest（仅知识库发生变化时）、`make docs-check`、`git diff --check`。**
- [ ] **Step 6: 完成 Wave 3 全部合并后推送一次 integration，使用 FLOW CI 核验器确认目标 SHA、workflow success、清单内所有 job success 且无 skip。**
- [ ] **Step 7: 最终 fetch；若 `origin/main` 已前进，普通 merge 最新 `origin/main` 到 integration，解决冲突后重跑全门禁和远端 CI，禁止 rebase 已共享的 integration 历史。**
- [ ] **Step 8: 确认 main 未再漂移后使用 `--ff-only` 前进到 integration，推送 main，再确认 main workflow 全绿。**
- [ ] **Step 9: 保留所有执行分支至 main CI 绿；随后按用户决定清理，不自动删除。**

Commit: `docs(roadmap): close post-U8 strategic boundary gate`

## 完成定义

- 三个智能体的每个提交均可追到所属 checkpoint 公布的 base SHA 和精确文件白名单；同一波次共享 base，base lineage 完整记录；
- 0026 唯一 head，RBAC/审计/模块边界/前端入口和旧路由兼容全部有测试；
- U8/0024 可恢复且可无损升级到 0026；
- contracts 由最终 API 生成；
- S01 状态由主协调者一次性关闭；
- 公开 C 与内部工作台仍为 gated，不因本计划自动开工。
