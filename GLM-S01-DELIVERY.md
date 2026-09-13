---
doc_id: FLOW-DELIVERY-GLM-S01-CHECKLIST-001
title: GLM 5.3 三 Agent 并行任务交付清单（S01 Task 0 部分 + Task 2C + 阻塞登记）
doc_type: delivery
status: verified
version: 1.0
created_at: 2026-09-13
updated_at: 2026-09-13
last_reviewed_at: 2026-09-13
owner: FLOW
applies_to: s01-parallel-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D049, D051]
supersedes: []
superseded_by: null
source_refs: [docs/superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md]
related_code: [scripts/ci/verify_workflow_jobs.py, apps/web/components/modules/module-landing.tsx, scripts/test_module_boundaries_e2e.sh]
commit_refs: [b8a3edd, 07d82f2]
evidence_refs: [docs/70_operations/three-agent-parallel-execution-runbook.md]
confidentiality: project-internal
---

# GLM 5.3 任务交付清单（供主协调者验收）

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

## 二、阻塞登记（按计划波次门禁，非执行者可解）

| 任务 | 阻塞原因 | 解锁条件 | 解锁后动作 |
|---|---|---|---|
| Task 4（S01 Task 7 模块边界后端） | 需要 Task 6 关闭后的 integration 绿 SHA（Sol 2A 审计/0026 与 Kimi 2B 路由接线合并完成） | 主协调者完成 Task 3 合并序列并推送 task6 checkpoint | 从该 SHA 建 `codex/s01-module-boundaries`，按计划 TDD 交付 registry/ownership/AST 守护/`/api/v1/modules` + 契约重生成 |
| Task 6A（S01 Task 9 全链验证） | 需要 Wave 2 绿色 SHA（Task 7+8 集成完成） | 主协调者完成 Task 5 集成并核验 | 从该 SHA 建 `codex/s01-full-verification`，交付独立验收 compose + `verify_s01_upgrade_from_u8.sh`（U8 dump 恢复→0026 升级→HTTPS 三方对账） |

说明：Task 4/6A 的红灯测试可在解锁后立即编写；Task 4 的 ownership manifest 必须覆盖 Task 6 新增的 security 文件，提前编写会违反「不猜测接口」纪律（Sol 的 ABI 已冻结部分可预填，但不抢先提交）。

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
