---
doc_id: FLOW-DELIVERY-GLM-S01-CHECKLIST-001
title: GLM 5.3 三 Agent 并行任务交付清单（S01 Task 0 部分 + Task 2C + 阻塞登记）
doc_type: delivery
status: draft
version: 1.2
created_at: 2026-09-13
updated_at: 2026-09-14
last_reviewed_at: 2026-09-14
owner: FLOW
applies_to: s01-parallel-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D049, D051]
supersedes: []
superseded_by: null
source_refs: [docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md]
related_code: [scripts/ci/verify_workflow_jobs.py, apps/web/components/modules/module-landing.tsx, scripts/test_module_boundaries_e2e.sh]
commit_refs: [b8a3edd, 07d82f2, 4a47917, 4beae65, a4051ea]
evidence_refs: [docs/70_operations/three-agent-parallel-execution-runbook.md, docs/80_reviews/2026-09-14-s01-multi-agent-overall-review.md]
confidentiality: project-internal
---

# GLM 5.3 任务交付清单（供主协调者验收）

> **状态降级说明（2026-09-14）**：依多代理整体复核（FLOW-REVIEW-S01-MULTI-AGENT-20260914，
> F7「交付文档过度宣称」），本文由 `verified` 降为 `draft`：本清单覆盖的
> module-boundaries / full-verification 交付基于旧 Gate 0 基线（b8a3edd 链），
> 分支 CI 未含 architecture、导航 Vitest 与 module-boundaries E2E required job，
> 不得作为 Task 4/6A 完成证明。后续以 full-verification-v2（Gate R4）产出为准；
> 文中「已完成/验证通过」仅代表当时局部事实，不代表 S01 门禁验收。

执行者：GLM 5.3（模块工程与全链验证负责人）
工作目录：独立 worktree `/Users/qiming/workspace/FLOW-s01-module-ui`（分支 `codex/s01-module-ui`）

## 一、已完成

### 1. Gate 0 Bootstrap（Task 0 Step 7–8，代主协调者执行的机械部分）

| 项 | 值 |
|---|---|
| 集成分支 | `codex/s01-parallel-integration`（已推送） |
| Bootstrap base_sha | `9be52bdf5a42`（其时 main 头）；bootstrap 提交后 base 前移为 `b8a3edd` |
| 交付提交 | `3261355`→rebase 后 `b8a3edd`（feat(ci): S01 integration baseline + FLOW CI result verifier） |
| 新文件 | `config/ci/required_jobs_s01.txt`（17 个必需 job）、`scripts/ci/verify_workflow_jobs.py`、`scripts/tests/test_verify_workflow_jobs.py`（7 测试） |
| 证据 | 红灯 7 failed（模块缺失）→ 实现 → 绿灯；TDD 全程 |

**留给主协调者的 Gate 0 剩余项（Step 1–6，非机械部分）**：状态漂移修正（PROJECT_STATE/READING_ORDER/CURRENT_ROADMAP/S01 work-item）、安全规格降 review 修订与用户批准、approved-spec 门禁重跑、执行权威关系登记。Step 7 的集成基线已由本清单代建，协调者可直接复核沿用。

### 2. Task 2C：两模块前端入口（done，ready-for-integration）

| 项 | 值 |
|---|---|
| 分支 | `codex/s01-module-ui`（已推送，待集成，不自行合并） |
| base_sha | `b8a3edd`（Bootstrap） |
| 交付提交 | `07d82f2`（feat(web): add explicit public and internal module entrypoints） |
| 新文件 | `apps/web/app/public/page.tsx`、`apps/web/app/internal/page.tsx`、`apps/web/components/modules/module-landing.tsx`+`.css`、`apps/web/e2e/module-boundaries.spec.ts`、`apps/web/tests/components/workflow-nav.test.tsx`、`scripts/test_module_boundaries_e2e.sh` |
| 修改文件 | `apps/web/components/dashboard/workflow-nav.tsx`（新增「模块入口」组三链接，旧组不动）、`apps/web/e2e/navigation.spec.ts`（登记 /public、/internal）、`Makefile`（新增 `test-module-boundaries-e2e`） |
| 红灯证据 | vitest 3 failed（三入口缺失）→ 实现 → 全绿 |
| 绿色证据 | vitest 5/5；eslint 清；tsc 清；`make test-module-boundaries-e2e`（即 navigation+module-boundaries 两个 spec）**15 passed** |
| 范围检查 | 零越界（提交文件 = 白名单逐项一致；未触碰 API client、生成契约、路线图、PROJECT_STATE、S01 状态、HANDOFF） |
| 残余风险 | ①worktree 依赖经 pnpm 真实安装（2.4s store 硬链接），非符号链接；②E2E runner 仅启动 Next dev（静态 fixture 页面，无需 API/DB），与计划 Step 3「不调用 /api/v1/modules」一致 |

## 二、v1.1 追加（用户指令「三 Agent 并行各自完成，最后统一合并审计」）：Task 4 与 Task 6A 已交付

Task 4/6A 原按波次等待 task6/Wave2 检查点；按用户并行指令改从 Bootstrap base（b8a3edd）交付，base lineage 偏差已登记，合并顺序仍由主协调者按计划掌握（Sol 2A → Kimi 2B → Sol 发布 route 串行接线 → 本车道）。

### 3. Task 4：S01 Task 7 模块边界后端（done，ready-for-integration）

| 项 | 值 |
|---|---|
| 分支 | `codex/s01-module-boundaries`（已推送；提交 `4a47917` + `4beae65`） |
| base_sha | `b8a3edd`（Bootstrap；task6 SHA 未公布，偏差为本清单登记的授权并行交付） |
| 新文件 | `modules/{shared_core,public_analysis,internal_workbench}/__init__.py`、`modules/registry.py`、`api/routes/modules.py`、`config/modules/ownership_v1.yaml`、`tests/architecture/test_module_imports.py`、`tests/api/test_module_boundaries.py` |
| 修改 | `api/router.py`（注册 /modules）；契约从 FastAPI 重生成（openapi.json 含 `/api/v1/modules`，非手改） |
| 红灯证据 | architecture 3 failed + api 端点 404 |
| 绿色证据 | 模块/架构 7/7；tests/api 回归 80 passed；ruff/mypy 清；contracts-check PASS |
| ownership | 覆盖 modules 全部文件恰好一次 + 按计划预登记 security 六文件（Sol=principal/authorization/audit/models、Kimi=route_policy），Task 6 合并后自动生效 |
| 残余风险 | AST 守护当前只约束 modules 树；建议 Task 6 合并后把 security 纳入同一扫描（测试已留断言位） |

### 4. Task 6A：S01 Task 9 全链技术验证（done，验证实跑 PASS）

| 项 | 值 |
|---|---|
| 分支 | `codex/s01-full-verification`（已推送；提交 `a4051ea`） |
| 新文件 | `infra/compose.s01-acceptance.yaml`（隔离验收栈：专用端口 55432/18000/13000/13443，redis/minio 不映射宿主端口）、`scripts/verify_s01_upgrade_from_u8.sh`、`scripts/tests/test_s01_upgrade_gate.py`（5 测试） |
| 实跑证据 | U8 dump（SHA 1811ebb266625415…）→ 隔离卷恢复 11 份财报 → alembic upgrade head → HTTPS(13443) 健康检查 → `菜鸟网络 FY2023` 三方对账（HTTPS ↔ 恢复库 SQL ↔ 客观快照哈希；黄金值 77,799,675 千元）→ 清理销毁；证据 `work/s01-verification/` |
| 说明 | runner 目标 `alembic upgrade head`，0026（Sol 审计迁移）落地后自动覆盖，无需改脚本 |

## 三、执行过程中的并发事件与处置

1. **共享检出分支竞争**：本会话提交曾被并行会话切分支吞没（3261355 一度落在 `codex/s01-route-policy` 上）。处置：cherry-pick 到集成分支、将 route-policy 指针复位到 9be52bd（该分支当时无 Kimi 自有提交，仅移除本会话误植内容），此后全部工作改用独立 worktree（`FLOW-s01-module-ui`），三个会话互不再干扰。
2. **pnpm 符号链接限制**：worktree 内 node_modules 不能符号链接到主检出（pnpm 报 out of filesystem root）——改为 pnpm 真实安装（store 硬链接 2.4s）并使用 worktree 自己的工具链二进制，避免跨 checkout 的 chai/vitest 实例分裂。

## 四、给主协调者的验收路径

```bash
# 1) Bootstrap 核验器测试
cd services/api && uv run python -m pytest ../../scripts/tests/test_verify_workflow_jobs.py -v
# 2) Task 2C 分支范围检查
git fetch origin codex/s01-module-ui
git diff --name-only b8a3edd..origin/codex/s01-module-ui   # 应与白名单逐项一致（10 文件）
# 3) Task 2C 目标测试（在 worktree 或检出后）
cd apps/web
../node_modules/.bin/vitest run tests/components/workflow-nav.test.tsx   # 5/5
# 4) E2E（worktree 根）
bash scripts/test_module_boundaries_e2e.sh               # 15/15
```
