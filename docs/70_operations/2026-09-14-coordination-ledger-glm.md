---
doc_id: FLOW-OPS-COORDINATION-GLM-002
title: 主协调者台账（GLM 5.3）：Task 6 集成线 CI 修复与基线登记（2026-09-14）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-14
updated_at: 2026-09-15
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

## 5. GPT 总审计回执与重定基（2026-09-14 追加）

GPT 独立审计产出（审计 worktree `s01-multi-agent-review-20260914`，冻结快照
2026-09-14 08:33 +08:00 ≈ b79bc64/9cfec8b 时代）：总报告 FLOW-REVIEW-S01-MULTI-AGENT-20260914、
三份车道修正单、修正矩阵、恢复 runbook（R0–R4）。协调者回执如下。

### 5.1 基线时差（最重要的事实修正）

审计快照早于协调者修复系列。真实时序（UTC）：b79bc64 红线（09-13 23:44）→
26a948f 认证配套（09-14 01:18）→ ff42c67 五路并合（02:09）→ c1510ce/3cccae8/
0d6644d/2570bf8 回落修复（03:20–03:35）→ **main 2570bf8 CI 17/17 全绿
（run 34803117958，rerun 过 analysis-invariants 的 Docker Hub 网络抖动）**
→ integration 同 commit 全绿（run 34803120095）→ ba5f34c 台账。因此：

- F1「主线无绿色基线」、矩阵 16/17 行 P0「frozen_red / not_checkpoint」**已被
  2570bf8/ba5f34c 事实闭合**；恢复 runbook 的 R0「记录红色快照」与 R1 的
  「恢复全绿」目标均已达成；
- **新的唯一恢复基线（recovery base）= `ba5f34c`**（main = integration 同树）。
  R1 安全修复分支应从该 SHA 切出，不再 BLOCKED_PENDING。

### 5.2 逐条裁决（对当前 HEAD 复核后）

| 审计发现 | 协调者裁决 |
|---|---|
| F1 主线红 / 文档门禁失败 | **已闭合**（26a948f 系列修复；legacy-exempt 改为生成器产 generated frontmatter）。审计证据链止于 run 34791653766，未覆盖 34803117958 |
| F2 安全骨架缺口（durable audit writer 缺失、authorization 非 action×resource 精确判定、identity JSON 未严格校验、legacy cutoff 误伤新 token） | **成立，Task 6 维持不关闭**。R1 security-contract-repair 自 ba5f34c 切出，owner=M3，白名单=security/auth/settings/main、0027、共享测试 helper；协调者已另行预警 2026-10-31 cutoff 启动炸弹（本台账 §1 遗留登记） |
| F3 route-policy 未接线真实路由 | **成立**。Kimi 自 R1 绿色 SHA 建 route-policy-v3；inventory 需先裁决 `/api/v1/metric-library/coverage` 的登记归属（P5 派生入口），协调者裁决：**作为 `metric_library.read` 正式登记**（已挂 require_bearer_auth，非匿名） |
| F4 module-ui 提前进 main | 事实成立但**归因更正**：进 main 走的是 ff42c67 五路并合（他方操作，非协调者合并序列；协调者当日已在本台账 §3 登记违规）。处置采纳审计方案「功能保留 + 补门禁」；Library commits（df11b44→e114ae3）系 Kimi 推入集成线、协调者 FF 携带，非协调者发起的功能合并 |
| F5 module-boundaries/Task 9 验证不足 | **成立**。module-boundaries-v2 / full-verification-v2 按 R3/R4 顺序执行，白名单与验收标准照单全收 |
| F6 范围污染（522fe6c 标题夹带；df11b44 种子暗写身份） | **成立**。522fe6c 已成历史（此后提交标题均如实）；`seed_p5_statements.sh` 的 RoleBinding 副作用已移除（身份引导单源化到 `seed_dev_principal.py`，fixed enterprise + 显式 actor） |
| F7 权威文档滞后 / 交付过度宣称 / 规格 §12 矛盾 | **成立，R0 名下三件已由协调者执行**：① 规格 §12 批准记录补全并与 frontmatter 对齐；② `GLM-S01-DELIVERY.md` 降为 `draft` 并加降级说明；③ 本台账作为取代性纠正记录。PROJECT_STATE / CURRENT_ROADMAP / HANDOFF 的统一重写排在 R2 后统一做，避免与进行中车道再次撞车 |

### 5.3 冻结令（自本节起生效）

1. 禁止向 main / integration 合并**业务代码**，直至 R1 安全修复 checkpoint 发布；
   文档/治理/审计类提交不受限，但须标题如实、不夹带；
2. 候选分支只读保存，不 rebase、不 force-push（GPT R0 原案采纳）；
3. M3 的 R1 白名单与验收标准、K3 的 v3 接线要求、GLM 的 v2 重建要求，
   分别以三份车道修正单为准；协调者按矩阵第 19 行承担全局 fixture 与 ci.yml；
4. 本台账 §2 中「M3 rebase 到 26a948f」的指令已被 ff42c67 事实取代，以本节为准。


## 6. R1 安全修复完成登记（2026-09-14 晚，单 Agent 接管执行）

用户拍板转交单一 Agent 后，R0+R1 已按本台账 §5 冻结令执行完毕：

**已完成（main bc62937，分支 CI 17/17 全绿，run 34889263972 重跑后）：**

- R0：GPT 审计七件套入库（59d7950→371b5f7）；14 worktree 清理至 1；
  12+12 个已并合分支删除；规格 §12 对齐；交付文档降级 draft；
- R1（分支 codex/s01-security-contract-repair，四 commit 4264cb8→bc62937）：
  1. durable AuditWriter（独立短事务、401/403/allow 三态、503 fail-closed、
     retention marker/legal hold、启动注册）；
  2. correlation 中间件（双 header 五处一致）；
  3. 认证收口：401 先 durable 审计（actor NULL + 指纹）再返回；identity JSON
     未知字段/重复 actor 拒绝；legacy 冻结身份精确匹配；
  4. cutoff 收窄：仅命中 legacy token 才应用截止（新 token 不误伤，§3.2 修正单）；
  5. require_action 接线全部 66 路由（共享会话 loader、§3.3 actor_conflict、
     blocked 条目占位）；TSV 重分类：metric-library 读=public、治理写 7 条
     维持 blocked、其余全解锁（0027 企业域引导回填）；
  6. 容器化修复：route_policy parents[5] 越界（smoke 崩溃根因）+ TSV 烤入镜像；
  7. 门禁：module-boundaries-e2e required job 接入 + 门禁清单测试同步；
  8. create_batch 引导自愈（固定 d001 企业，测试清理后自恢复）。

**本地验证：** 全量 pytest 721 passed（19 分钟）；ruff/mypy（185 files）/
check_docs m1/contracts-check 全绿；stack-up 容器链路实测
（health 200 / legacy bearer 403 按最小权限 / web-analyst 走 analyst 通量）。

**遗留（按 runbook 顺序，接手者下一步）：**

1. R2：route-policy-v3 完成剩余治理写的治理模式落地 + publishing/operations
   串行四阶段接线（pipeline 死代码按 Sol 处置单删除）；
2. R3：module-boundaries-v2（全树 AST + path-glob manifest）；
3. R4：full-verification-v2（动态隔离/真实 CA/sentinel/双证明）；
4. dashboard 当前 404 not-ready 属数据态（0027 批次转 internal 后需重新
   发布快照），非安全回归；
5. ~~main CI run 34895136484 盯绿后本台账登记最终 checkpoint SHA。~~ **已闭环
   （2026-09-15）**：run 34895136484（`bc62937`）与其后 34895309197（`4c02a3c`）
   均全绿；最终 checkpoint 登记为 **`640cfb8`**（CI run 34907918485，17/17 全绿，
   同树含 R1 代码 + 文档门禁修复 `docs(competitive)` 元数据补齐）。期间三个
   竞对文档提交（`1af369d`/`042d937`/`e2b51ac`）CI 红，根因为 frontmatter 缺
   `updated_at` 与未注册 doc_type，已由 `640cfb8` 修复（m1/m6 本地全绿，
   239 文档 0 错误）。PROJECT_STATE 已同步至 v1.6。

## 7. R2/R3/R4 交付与 S01 关闭登记（2026-09-15，单 Agent 串行）

分支 `codex/r2-route-policy-v3`（T00 DD0 基线：`361e4f0`，run 34913878637 全绿）：

- **R2/T02 治理写策略化**（`5d085b4`）：metric-library 7 条治理写解锁
  （entry/entry_proposer/events 三类新 loader；activate/retire 经 draft
  治理事件取 proposed_by，缺失即 PROPOSER_REQUIRED fail-closed）；
  operator/actor 全部取自 Principal（§3.3），body 身份字段冲突 → 409；
  statements corrections/publish 的硬编码/不可信 operator 一并收口。
- **R2/T03 四阶段接线**（`33870c3`+`3bb31f4`）：`flow_api/publication/
  four_stage.py` 按规格 §7.1–§7.5 精确实现；迁移 0028（publication_id/
  idempotency_key/source_payload_sha256/object_key/内容列 + 状态枚举扩展 +
  (parent,sequence,format) 唯一）；publishing/operations 发布路由 Idempotency-Key
  必填、两次 caller commit、intent/outcome 503 语义；`security/redaction.py`
  §8.3 确定性脱敏；按 Sol 处置单删除两条旁路 pipeline 与旧 publication
  service；`ObjectStore.read_by_key` 支撑 §7.4 五要素 key 下载。
- **T04 工程卫生**（`a16751e`）：ownership owner 职责域化；`var/` 运行产物
  移出版本控制；m6 入 CI 评估完成（单行改动待用户批准，红线不动手）。
- **R3/T06 module-boundaries-v2**（`fbfe7d8`）：manifest v2（managed_files +
  glob_rules first-match + catch-all 全树唯一 owner；Agent 代号禁用）；
  `scripts/check_module_boundaries.py` 全树 AST 扫描 + import_rules 禁止
  owner 对互导；合成违规 fixture 证明门禁能红；旧覆盖测试委托 v2 检查器。
- **R4/T07 full-verification-v2**（`2fa5f72`）：`infra/compose.r4.yaml` 隔离
  overlay（独立 project/卷、固定端口全收回、nginx 443 动态端口）+
  `scripts/r4_full_verification.sh`：U8 dump 恢复→基线合同四证（dump sha/
  0024 头/关键表/聚合哈希）→升级 0028→不变量保持→SQL marker==HTTPS marker
  （真实 CA `--cacert`，随机 id 非 200）→evidence（skipped=[]）→teardown
  down -v。**本地 PASS**（evidence `work/r4/evidence.json`）。同提交固定
  minio 镜像版本（上游 :latest 漂移为两轮 CI 红根因）。
- **§3.3 全链收口 + T09 前置**（`4179f53`）：intake/copilot/investigations
  的 actor/reviewer 改由 Principal 注入，前端全组件去硬编码身份（两轮 e2e
  失败根因）；`scripts/accuracy_benchmark.py` L0 入库保真基准 1454/1454
  全对；C 级出口协议与三个子工作包入库，路线图 v1.6 登记。
- **T08**（本次提交）：PROJECT_STATE v1.7、S01 工作包 status=completed、
  CURRENT_ROADMAP 同步、HANDOFF v3.1。

**S01 正式关闭；Task 6 关闭。**下一 Gate：公开模块 C 级出口（T09，gated）。

## 8. 阶段 3 基础交付登记：T09–T12（2026-09-15，分支 codex/t09-c-exit-foundations）

- **T09-L1**（`5a9e788`）：页级答案集 `config/statements/answer_set_l1.yaml`
  ——1775/1795 值带 PDF 页锚（98.9%；strong 972 / weak 803，跨语言招股书走
  仅数值弱锚并显式降级标注），10 行未定位显式列出不静默丢弃；
  `accuracy_benchmark.py --level L1` 双向验证：锚失效 0、值不一致 0、
  未入库 0；L0 保持 1454/1454。`answer_set_sources.yaml` 固定 sample→报告
  身份映射（BABA FY2019/20、菜鸟 FY2021–23 共用 PDF，键必须含报告身份）。
- **T10-B3/B4**（`c9dcd47`）：迁移 0029（statement_line_item.page_number/
  page_anchor + statement_report.supersedes_id）；导入器重述时写 supersedes
  链、按 L1 答案集认领页锚（95.5% 行项目带页锚：strong 516 / weak 471 /
  null 47，不伪造定位）；API/前端透出页码徽标；
  `statement_restatement_diff.py` 相邻版本 diff（验收：构造重述样本 →
  supersedes 链一致 + 恰好一处值变更断言通过）。
- **T10-B5/B6**（`dda978b`）：只读 MCP server（stdio JSON-RPC，stdlib 实现；
  get_facts/get_metric/get_provenance 三工具；FLOW_MCP_TOKEN fail-closed
  认证 + 结构化审计行）；`draft_restatement_commentary.py` 确定性重述差异
  说明起草（数字全部来自引擎，零模型生成，人工终审前置）。
- **T11-G2**（`8c479a1`）：`perf_baseline.py` 事务内 10× 合成放大
  （1034→10340 行，回滚无污染）：明细查询 P95 6.23ms、检索 P95 0.97ms、
  聚合 P95 1.11ms——10× 容量下全部远低于裁决阈值。
- **T12**（`ffef522`）：`ask_facts.py` 确定性问数 v1（检索引用 + 显式拒答，
  零模型调用、可复现）+ `generate_qa_eval.py` 评测集 94 问
  （60 数值 + 34 拒答陷阱），命中率 100%、拒答零误答。

**仍未关闭（外部依赖/需用户参与，不虚报）：**
- C 级出口 PASS 本身：独立盲评与 company-level holdout 抽签需用户/第三方；
  L1 答案集的独立 oracle 复核（U4 车道）待到料；
- C1 数据扩张：需 10 家公司真实财报 PDF 到料（不可合成）；
- m6 文档门禁入 CI：单行改动方案已备（红线待批）；
- T13 内部工作台：等 C 级出口 PASS + 企业数据授权；T14 各外部项同前。
