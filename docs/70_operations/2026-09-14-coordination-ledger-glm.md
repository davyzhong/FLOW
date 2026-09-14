---
doc_id: FLOW-OPS-COORDINATION-GLM-002
title: 主协调者台账（GLM 5.3）：Task 6 集成线 CI 修复与基线登记（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-14
owner: FLOW
applies_to: s01-parallel-agent-execution
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D049, D051, D052, D053, D054]
supersedes: [FLOW-OPS-COORDINATION-HANDOVER-001]
superseded_by: null
source_refs:
  - docs/70_operations/2026-09-13-coordination-handover-gpt-to-kimi.md
  - docs/70_operations/three-agent-parallel-execution-runbook.md
related_code:
  - scripts/seed_dev_principal.py
  - services/api/src/flow_api/api/auth.py
commit_refs: ["26a948f", "b79bc64", "ee184fb"]
evidence_refs: []
confidentiality: project-internal
---

# 主协调者台账（GLM 5.3，v1.0）

前任交接（FLOW-OPS-COORDINATION-HANDOVER-001 §8）登记：用户批准安全规格 V1.1、
主协调者改由 GLM 5.3 担任。本文件自此为协调权威记录。

> 用语更正：2A 执行者一律称 **Minimax M3**（此前台账中的「Mavis」为误记，指向同一执行方）。

## 1. 本期处置：Task 6 集成线 CI 全线 401 修复（26a948f）

### 根因

Minimax M3 的 2A 剩余段（`ee184fb` 井入集成线：0026 迁移 + RoleBinding + 四阶段 ABI +
`require_bearer_auth` 全量接线）把认证合同从「未配置 AUTH_TOKEN 即放行」升级为
S01 规格 §2.2/§3 的 dev principal 模式：`FLOW_DEV_ACTOR_ID` + DB active RoleBinding
缺一不可。实现本身符合已批准规格；缺口在**配套未铺**——CI 全部 job 与本地栈均未配置
dev actor、未播种 binding，导致：

| CI job（main @ b79bc64） | 失败形态 |
|---|---|
| unit | 5：旧契约测试断言 `unauthorized`、workspace 无 DB 打穿 |
| integration | 59+2：API 级测试全量 401 |
| intake / dashboard / investigation / user-closure / metrics / analysis 各 e2e | uvicorn 栈或 pytest 401 |
| static-python | 独立问题：Kimi 重生成 `metric_coverage_matrix.md` 触发 legacy-exempt 哈希锁 |

### 修复（单提交 `26a948f`，已推送 main + codex/s01-parallel-integration）

1. `scripts/seed_dev_principal.py`（新增）：幂等播种 dev analyst（`flow-dev-bp`）与
   legacy service_account（`local-dev-web`）两条 binding；库不可达/未迁移静默跳过。
   踩坑记录：psycopg 对同一参数在 SELECT/WHERE 双位置类型推导不一致
   （text vs varchar，`AmbiguousParameter`），须显式 `CAST(:actor AS varchar)`。
2. `tests/conftest.py`：注入 `FLOW_ENV=development` + `FLOW_DEV_ACTOR_ID`（与脚本同默认值），
   autouse fixture 进程内首次成功播种后不再重复。
3. `tests/api/test_auth_boundary.py` 重写到新契约：负路径无 DB 可判定
   （`authentication_required` / `credential_invalid` / 全未配置 fail-closed `unauthorized`）；
   legacy 正路径 DB 不可达时 skip（unit job 无 DB 设计不变）。
4. `tests/api/test_workspace.py`：以 `dependency_overrides[auth.get_session]` 提供 fake
   binding，unit job 继续 zero-DB 可跑。
5. uvicorn 型 e2e 脚本（dashboard / investigation / user-closure / statements）导出
   `FLOW_DEV_ACTOR_ID` 并在迁移后调用种子；compose api/worker 注入同变量；
   `make stack-up` 收尾 alembic upgrade + 播种；`.env.example` 补文档。
6. `scripts/p5_query_facts.py`：生成器直接产出 `doc_type: generated` 合同 frontmatter
   （doc_id / generator_ref / input_hash），`metric_coverage_matrix.md` 移出豁免清单——
   生成类文档的合规性由生成器保证，不再靠哈希锁续期。

### 验证

- 本地 unit 选择集 43/43；API + investigation + metrics + analysis + dashboard 144/144；
  intake/dashboard/copilot/overrides/template 28/29（唯一失败例为本地库历史数据污染，
  单跑通过；CI 每次全新库不受影响）；
- `ruff check src tests`、`mypy src` 干净；`check_docs --phase m1` PASS（210 docs, 0 errors）；
- 远端：`26a948f` 推送 main（b79bc64..26a948f fast-forward）与集成线（e114ae3..26a948f），
  双触发 FLOW CI，等待全绿。

## 2. 各执行方当前基线与指令

| 执行方 | 基线指令 |
|---|---|
| **Minimax M3**（Task 2A 余段 / route-policy-v2） | 分支 `codex/s01-route-policy-v2` @ `a49a10f` 基于旧 main（含 uuid_generate_v4 时代），CI 失败含已修复项。**指令：rebase 到 `26a948f`**；2A 已井入部分勿重做，只补路由层接线 + test_security_schema / test_audit_atomicity + main.py fail-fast |
| **Kimi K3**（Task 2B + library） | 集成线上其 library 提交（df11b44→e114ae3）已随 `26a948f` 线生效；其「dev auth binding seed」与本修复的种子脚本语义一致（legacy actor 同名 `local-dev-web`，幂等不冲突）。Task 2B 仍等 route policy 开工门禁（规格已 approved，可开工） |
| **GLM 5.3**（本协调者） | ① 盯 main CI 全绿；② Task 6 关闭核验（verify_workflow_jobs 17 job 清单）；③ Wave 2 合并（module-boundaries → module-ui → 6A runner 复跑） |

## 3. 共用检出纪律警告（再次）

本期实际发生：Kimi 会话在同一检出内后台 `git pull` 并向 `glm-coord` 分支直接推送
（「propagate report-grade visual system」）。结果未受损（零文件交集 + fast-forward），
但这正是交接记录 §6 登记过的事故模式。**重申：执行方一律独立 worktree；`glm-coord`
分支为协调者工作分支，执行方请勿直接推送。**

## 4. 任务完成清单（截至 26a948f）

**已完成并合入集成线/main：**

1. ✅ Task 2A 余段井入（ee184fb：0026 迁移 gen_random_uuid 化 + RoleBinding + 四阶段 ABI + 认证接线）；
2. ✅ CI 认证配套全链修复（26a948f，见 §1）；
3. ✅ static-python 文档合同修复（生成器 frontmatter + 豁免清单收缩）；
4. ✅ U8 关闭基线（u8-final-baseline 标签）与指标库 v1.1（64 条）此前已闭合；
5. ✅ Kimi library 静态站（offline site + coverage matrix + widget variant）随线生效。

**进行中 / 待办：**

1. ⏳ main + integration CI 全绿确认（运行中）；
2. ⏳ M3：rebase 后补路由层接线与安全集成测试（Task 6 关闭前置）；
3. ⏳ K3：Task 2B route policy 重做（TSV 64 条权威清单）；
4. ⬜ Task 6 关闭（2A+2B 合并后 verify_workflow_jobs 核验）；
5. ⬜ Wave 2：module-boundaries → module-ui → 6A runner 复跑；
6. ⬜ Wave 3：Task 9/10；
7. ⬜ U4 oracle（等用户独立会话）、rnd_exp 核验（等原文）、U9/O5（等数据授权）、U10 证据决策。
