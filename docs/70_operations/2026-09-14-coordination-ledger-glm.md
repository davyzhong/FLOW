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

### 二次修复（c806033，26a948f 之上）

26a948f 后 CI 仍有两类残留失败：

1. **根目录 uv 环境无 psycopg**：seed 脚本从仓库根 `uv run` 调用必然
   `ModuleNotFoundError` → smoke（stack-up）与 dashboard/investigation/user-closure/
   statements 四个 e2e job 失败。改为经 `services/api` 的 uv 环境调用
   （psycopg 在该环境），脚本与 Makefile alembic 行补本地开发库默认 DATABASE_URL。
2. **conftest 播种不能做进程内缓存**：`tests/integration/test_migrations.py` 的
   0025 downgrade→upgrade 往返会**删表重建 role_binding**，缓存导致后续全部
   tests/api 401（integration job 57 例失败）。该修复落在 c1510ce（见下）。

### 三次处置：ff42c67 五路并合的回落修复（c1510ce 起本系列）

2026-09-14 02:09，他方（非经协调者合并序列）将 5 个车道分支直接合入 main
（ff42c67：main.py fail-fast、route policy 2B、module boundaries、module-ui、
audit schema/atomicity 测试）。合并以旧基线解析 conftest/auth.py，**语义回退**
了本系列两项修复，CI 7 job 失败。已修复：

1. **conftest 回退**→ c1510ce 重新落每用例补种（原修复当时未及提交）；
2. **auth.get_session 连接泄漏**→ 3cccae8：普通返回型依赖 FastAPI 不做收尾，
   require_bearer_auth 挂在全部 /api/v1 路由，每请求泄漏一个池连接，压满
   QueuePool(5+10) 后全站 500——生产同险，已改 yield + finally close；
3. **audit schema/atomicity 测试不可运行**→ 0d6644d + 本系列后续提交：
   audit_event INSERT 列重复/缺非空列；audit_atomicity 三用例对 pipeline
   真实合同（store 协议、execute 不上抛、finalize 收 PublicationResult）
   全部错位，重写为可执行版本并补最小真实快照种子；
4. **prepare_intent 企业域不可满足**→ ReportSnapshot 全链无 enterprise 列，
   原检查恒失败（四阶段发布死锁）。改为「显式参数（路由层从 Principal 取）
   优先、快照字段后备、皆缺 fail-closed」——参数化不降低安全语义；
5. static-python ruff：audit_atomicity E402、security_schema F401/B017 清零。

### 遗留登记

- **2026-10-31 截止炸弹**：main.py 启动 fail-fast 校验 flow_legacy_bearer_cutoff
  （默认 2026-10-31T15:59:59Z），到期后**所有**环境（含 development）启动即
  SystemExit(2)。S01 车道须在该日前完成 identity bindings 迁移或调整默认；
- smoke 在 ff42c67 的失败为 Docker Hub 网络抖动（auth.docker.io reset），非代码；
- tests/api 在残留库上仍有顺序敏感用例（intake_overrides identity 系列），
  CI 全新库不触发；已在 ledger 记录，留 K3 2B 后统一治理测试隔离。

### 验证（截至本系列）

- 本地：unit 选择集 43/43、metrics/analysis/data-contract 145/145、
  security_schema+audit_atomicity 11/11、intake/dashboard/copilot/overrides/
  template、investigation、dashboard、publishing 各文件子集全绿；
- `ruff check src tests`、`mypy src`（184 files）干净；`check_docs --phase m1`
  PASS；contracts-check 无漂移；
- 远端待验：本系列推送后 main CI 全绿为 Task 6 关闭前置。

## 2. 各执行方当前基线与指令（ff42c67 后更新）

| 执行方 | 当前状态与指令 |
|---|---|
| **Minimax M3**（Task 2A 余段） | 其 route-policy-v2 车道已于 ff42c67 链并合 main（含 main.py fail-fast、audit schema/atomicity 测试）。并合内容存在两类缺陷，已由协调者代修（3cccae8 连接泄漏、0d6644d/2570bf8 测试修复 + prepare_intent 参数化）。**指令：复审 2570bf8 对 pipeline.py 的签名变更与 auth.py 的 yield 修复；后续工作基于 `2570bf8`** |
| **Kimi K3**（Task 2B + library） | 2B route policy（997c1ab）已随 ff42c67 落地 main；library 线（df11b44→e114ae3）随 26a948f 生效。**指令：2B 路由接线若引用 prepare_intent，enterprise_id 必须从 Principal 取（2570bf8 签名）** |
| **GLM 5.3**（本协调者） | ① 盯 2570bf8 起 main CI 全绿；② Task 6 关闭核验（verify_workflow_jobs 17 job 清单）；③ Wave 2 合并（module-boundaries → module-ui → 6A runner 复跑） |

## 3. 共用检出纪律警告（再次）

本期实际发生：① Kimi 会话在同一检出内后台 `git pull` 并向 `glm-coord` 分支直接推送；
② 他方绕过协调者合并序列把 5 个车道分支直接合入 main（ff42c67），合并基线陈旧，
语义回退了协调者两项未及提交的修复并带入不可运行测试。结果虽已代修，但
**集成纪律失效两次**。重申：执行方一律独立 worktree；进 main 的合并必须经
协调者按 runbook §7 执行（base lineage + diff 审阅 + 分步门禁）。

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
