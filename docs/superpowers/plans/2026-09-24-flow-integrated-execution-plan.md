---
doc_id: FLOW-PLAN-INTEGRATED-EXECUTION-20260924
title: FLOW 统一完整实施计划
doc_type: plan
status: active
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-PLAN-CURRENT, FLOW-SPEC-DAMAI-DEMO-001, FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
acceptance_refs: [roadmap-unique-invariant, damai-full-year-release, knowledge-release-gate, public-c-exit, internal-three-cycle-validation]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: repository-detailed-execution
supersedes: [FLOW-PLAN-POST-U8-BOUNDARY-001, FLOW-PLAN-THREE-AGENT-PARALLEL-001, FLOW-PLAN-FE-DESIGN-UPGRADE-20260915, FLOW-PLAN-FE-CONSISTENCY-REMEDIATION-20260916, FLOW-PLAN-KNOWLEDGE-REFRESH-002, FLOW-PLAN-DAMAI-DEMO-20260924, FLOW-PLAN-BASELINE-REPAIR-20260924]
superseded_by: null
---

# FLOW 统一完整实施计划

> **执行者要求：** 实施本计划时使用 `executing-plans`；代码任务使用
> `test-driven-development`，完成声明前使用 `verification-before-completion`。
> 本文件是唯一详细执行合同，`docs/50_plans/CURRENT_ROADMAP.md` 仍是唯一状态
> 真相。本文中的清单定义验收步骤，不替代路线图和工作包状态。

## 0. 为什么需要本计划

截至 2026-09-24，`docs/superpowers/plans/` 内共有十份计划。历史迁移、S01、
多 Agent 编排、前端整改、知识刷新、大麦数据和基线修复并存，其中六份仍错误地
标记为 `active`。部分计划的复选框从未随交付回填，不能据此判断完成度。

本计划执行三项治理裁决：

1. 只保留一个详细执行计划；旧计划保留为历史证据并禁止继续领取；
2. 完成事实只认 `CURRENT_ROADMAP`、工作包、提交、测试和交付证据；
3. 新计划、Roadmap、检查清单或 To-do 必须先落盘、进入索引、提交并推送，
   对话不能成为唯一载体。

## 1. 权威关系与使用方法

| 层级 | 权威文件 | 职责 |
|---|---|---|
| 当前事实 | `docs/00_start_here/PROJECT_STATE.md` | 已实现能力、当前阻塞和已验证基线 |
| 当前状态 | `docs/50_plans/CURRENT_ROADMAP.md` | 工作包顺序、状态、依赖和证据链接 |
| 详细执行 | 本文件 | 全部剩余任务、文件范围、命令、验收和停机条件 |
| 稳定工作包 | `docs/50_plans/work_items/*.md` | 可领取范围和外部门禁 |
| 历史证据 | 其余 `docs/superpowers/plans/*.md` | 过程、旧方案和历史验收，不再领取 |

执行前必须：

```bash
git pull --ff-only
git status --short --branch
python3 scripts/documentation/plan_views.py --check
python3 scripts/check_docs.py --phase m1
```

每个任务都遵循：红灯或失败验收 → 最小实现 → 定向验证 → 全局相关门禁 →
范围检查 → commit → 立即 push → 同 SHA CI。若计划发生变化，先修改本文件和
路线图，再开始实现。

## 2. 十份来源计划的处置

| 来源计划 | 真实结论 | 本计划处置 |
|---|---|---|
| `2026-09-07-unified-next-plan.md` | 历史 U1–U10；U1–U3、U5–U8 已关闭，U4/U9/U10 仍受外部门禁 | 保留历史；U4/U9/U10 合并至 E/I/F 轨 |
| `2026-09-09-operations-track-plan.md` | O1–O4 完成；O5 依赖内部授权 | O5 合并至 I 轨 |
| `2026-09-12-static-knowledge-and-document-migration.md` | M0–M6 已完成 | 仅保留治理和不可变档案纪律 |
| `2026-09-13-flow-post-u8-boundary-gate.md` | S01 已完成，旧空框失真 | 不再执行；回归门禁由各阶段复用 |
| `2026-09-13-flow-three-agent-parallel-restructuring.md` | 多 Agent 方案已结束，S01 已由串行修复关闭 | 取消执行，仅保留协作教训 |
| `2026-09-15-frontend-design-upgrade-proposal.md` | 基础组件大部完成；导出审计、真实溯源和工作流页仍有价值 | 剩余项合并至 U 轨 |
| `2026-09-16-frontend-consistency-remediation-plan.md` | Task 0–9 已关闭；状态矩阵和响应式门禁已建立 | 完成归档；仅继承外部依赖缺口 |
| `2026-09-18-static-knowledge-refresh-and-strategic-rebaseline-implementation-plan.md` | Task 0 完成，K0–K6 未完成 | 完整合并至 K 轨 |
| `2026-09-24-damai-logistics-demo-data-implementation-plan.md` | 已有半成品；A1–C3 仍需按批准规格修正 | 完整合并至 D 轨，当前第一主线 |
| `2026-09-24-project-baseline-repair-implementation-plan.md` | 文档门禁和权威状态待修 | 合并至 G0 与 D3 |

## 3. 当前基线与不可误判事项

- U8 已关闭并由 `u8-final-baseline`、数据库快照和 U8 验收脚本保护。
- S01、Facts V2、企业周期、RBAC/审计、模块边界和前端一致性整改已完成；
  不得因旧计划空复选框重做。
- 当前 Alembic 头、测试计数和 CI 结果必须在执行时实测，不引用旧文档数字。
- 大麦发行版已有画像、生成器、闭合财报、静态包和部分装载链，但当前数据仍有
  聚合维度、来源身份和审核旁路问题；不得直接作为最终验收数据。
- 正式知识 release 仍是 `flow-knowledge-2026-09-12.1`。第二代知识刷新只完成
  前置基线，不得提前切换 `CURRENT_RELEASE`。
- 公开模块 C 级仍缺独立 oracle、holdout 和盲评；合成大麦数据不能替代真实
  公开财报或真实企业三周期验证。

## 4. 总体依赖与执行顺序

```text
G0 文档基线修复
  └─ D1 大麦数据合同与静态发行包
       └─ D2 正式领域对象和分析工作流
            └─ D3 一键启动、八个主要页面（含 /data）E2E、全链关闭
                 └─ U 体验剩余项（用真实数据验收）

K1 Davybase/K0/K1 ─→ K2 稳定 15:00 截面 ─→ K3 FLOW 新 release candidate
                                                    └─ USER 战略裁决 ─→ K4 原子激活

E1 公开 C 级出口（外部 oracle/holdout/盲评）
  ├─ E2 真实公开数据扩张
  └─ I 授权内部工作台连续三周期验证（另需内部数据授权）
       └─ F U10 证据决策
```

D 轨是当前第一主线。K 轨可在独立仓库和不重叠文件上并行，但 K4 与 D3 都会改
README、PROJECT_STATE、ROADMAP 和 HANDOFF，必须由单一协调者串行合并。
E/I/F 受真实外部输入约束，不得用合成数据解除门禁。E1 完成后，E2 与 I 可
分别推进；E2 不是 I 的硬前置。

---

## 5. G0：恢复文档与计划基线

**Files:**

- Modify: `CODE_OF_CONDUCT.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SECURITY.md`
- Modify: `scripts/build_damai_demo.py`
- Modify: `services/api/tests/fixtures/test_damai_canonical.py`
- Generate: `fixtures/damai/README.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Generated: `docs/50_plans/views/{active,blocked,completed}.md`

### Task G0.1：修正文档元数据

- [ ] 为三份顶层文档补合法且唯一的元数据。
- [ ] 先写失败测试，证明生成的 `fixtures/damai/README.md` 缺 frontmatter；修改
      `scripts/build_damai_demo.py` 的模板后重建，禁止手改生成产物。
- [ ] 红灯与绿灯均运行 `cd services/api && uv run pytest tests/fixtures/test_damai_canonical.py -v`；
      随后运行 `cd ../.. && python3 scripts/build_damai_demo.py --output fixtures/damai --check`。
- [ ] 运行 `python3 scripts/check_docs.py --phase m6`，要求零失败。
- [ ] 运行 `git diff --check`，只提交本任务文件（生成器、测试、生成 README 与
      三份顶层文档）并推送。

### Task G0.2：校准权威状态

- [ ] 实测 Alembic head、当前分支、远端 CI 和现有大麦发行包计数。
- [ ] 更新 PROJECT_STATE/READING_ORDER，移除过时 S01 和前端进行中表述。
- [ ] 运行 `python3 scripts/documentation/plan_views.py --write` 与 `--check`。
- [ ] 不把计划值写成实测值，不覆盖历史交付记录。

**退出条件：** M6、链接、计划视图和 diff-check 全绿；当前入口无互相矛盾。

---

## 6. D1：大麦物流完整财年数据合同与静态发行包

**目标：** 建立 `damai-logistics-demo-v1` 的确定性全量发行版，覆盖 FY2025
同比期与 FY2026 分析期，不用聚合成员冒充明细。

### Task D1.1：先用红灯锁定全量合同

**Files:**

- Modify: `services/api/tests/fixtures/test_damai_profile.py`
- Modify: `services/api/tests/fixtures/test_damai_generator.py`
- Modify: `services/api/tests/fixtures/test_damai_canonical.py`
- Modify: `services/api/tests/fixtures/test_damai_statements.py`

- [ ] 断言 5 组织、4 客群、40 客户、8 产品、6 区域真实进入 canonical。
- [ ] 断言约 1,920 条经营明细、10,752 条预算和 4,800 条 AR 账龄明细。
- [ ] 断言逐月经营↔财务、预算恒等式、AR↔回款↔现金和两年四表闭合。
- [ ] 保存预期失败证据，失败原因必须指向当前聚合实现。

### Task D1.2：重构明细生成器和 canonical 投影

**Files:**

- Modify: `services/api/src/flow_api/fixtures/damai/{profile,generator,canonical,validation}.py`

- [ ] 用 UUID5、Decimal 和显式尾差分配生成“月×客户×活跃产品”明细。
- [ ] 固定客户客群/区域/信用期，固定产品业务族/业务单元。
- [ ] 预算覆盖收入、三类直接成本、期间费用、经营利润和经营现金流；引擎投影
      只写真实支持的四类原始行，不把毛利或期间费用伪装成已执行指标。
- [ ] 六类异常必须定位到客户、产品、区域和月份。
- [ ] 10,752 条细分原始预算完整保留，但不得伪造财务指标尚未支持的细分输出。
- [ ] 用真实 `MetricCalculator` 验证 `REVENUE`/`DIRECT_COST` 在 total、
      organization、segment、product、segment×product 五种粒度与 manifest
      一致；`OPERATING_PROFIT`/`OPERATING_CASH_FLOW` 只验证合同支持的
      total/organization 粒度，禁止重复或漏算三类成本。

Run:

```bash
cd services/api
uv run pytest tests/fixtures/test_damai_profile.py tests/fixtures/test_damai_generator.py tests/fixtures/test_damai_canonical.py -v
```

### Task D1.3：建立独立合成财报和正式审核链

**Files:**

- Modify: `services/api/src/flow_api/fixtures/damai/loader.py`
- Modify: `services/api/src/flow_api/statements/normalization.py`
- Modify: `config/statements/item_alias_map_v1.yaml`
- Modify: `services/api/src/flow_api/operations/engine.py`
- Modify: `services/api/tests/fixtures/test_damai_loader.py`
- Modify: `services/api/tests/statements/test_normalization.py`
- Modify: `services/api/tests/operations/test_operations_engine.py`

- [ ] 财报和 SHA 只来自 `fixtures/damai/statements/damai_fy*.yaml`。
- [ ] 公司身份固定为 `DAMAI.SYN`，不得读取或冒充 `9988.HK`。
- [ ] 运营事实和分部序列为大麦独立数据，不复用 Alibaba fixture。
- [ ] 必须调用 `ReviewService.publish`；任何直接改 `status` 的实现由测试拒绝。
- [ ] 走完 import → normalize → quality/review → publish → freeze。

### Task D1.4：重建零漂移发行包

**Files:**

- Modify: `scripts/build_damai_demo.py`
- Generated: `fixtures/damai/**`

- [ ] manifest 写入维度覆盖、财年汇总、异常可发现性和完整血缘。
- [ ] 临时目录连续构建两次，文本 SHA 和 XLSX 语义指纹一致。
- [ ] 正式重建后 `--check` 零漂移，README 通过文档元数据门禁。

**D1 退出条件：** 规格 §3.3 全部可机器对账；生成器、canonical、工作簿和
manifest 同源；现有公开财报 fixture 未被覆盖。

---

## 7. D2：贯通正式领域对象与分析工作流

### Task D2.1：事务化、幂等化整体 seed

**Files:**

- Modify: `services/api/src/flow_api/fixtures/damai/loader.py`
- Modify: `services/api/src/flow_api/intake/service.py`
- Create: `services/api/tests/fixtures/test_damai_loader_atomicity.py`
- Modify: `services/api/tests/fixtures/test_damai_loader_analytics.py`
- Modify: `services/api/tests/integration/test_intake_service.py`

- [ ] 复用唯一 bootstrap enterprise，建立/复用截止 `2026-08` 的唯一周期。
- [ ] `IntakeService.create_batch()` 可显式接收 cycle，同时保持旧调用兼容。
- [ ] 工作簿走 source、mapping、validate、warning acknowledgement、publish。
- [ ] 建立 12 个指标快照和 1 个 AnalysisRun，真实授权依赖可访问。
- [ ] 注入不变量、第二财报和 freeze 三类失败，全部验证整体回滚。
- [ ] seed 两次后所有领域对象计数零增长。

### Task D2.2：调查、证据、结论和冻结报告

**Files:**

- Modify: `services/api/src/flow_api/fixtures/damai/loader.py`
- Create: `services/api/tests/fixtures/test_damai_loader_workflow.py`

- [ ] 六个可追溯信号只由现有五个 playbook 产生最多五个系统 Finding。
- [ ] 状态覆盖 candidate/in_review/approved，只有 approved 进入正式结论。
- [ ] 冻结内部分析报告、两年客观财报快照和经营概览。
- [ ] 发布/下载 SHA 一致，结论可回链发行包 SHA 和 record_id。

### Task D2.3：独立 synthetic 指标覆盖矩阵

**Files:**

- Create: `config/metrics/damai_demo_metric_coverage_v1.yaml`
- Modify: `services/api/src/flow_api/api/schemas/metric_library.py`
- Modify: `services/api/src/flow_api/api/routes/metric_library.py`
- Modify: `apps/web/components/metric-library/metric-coverage-section.tsx`
- Test: `services/api/tests/api/test_metric_library.py`
- Test: `apps/web/tests/components/metric-library-coverage.test.tsx`

- [ ] 默认 public 矩阵保持不变，`dataset=damai` 返回独立 synthetic 矩阵。
- [ ] UI 永久展示“合成演示数据”；不可计算项保留 typed missing reason。
- [ ] 不以 0 补缺，不把大麦覆盖率写成真实公开模块准确率。

**D2 退出条件：** 全部写入通过正式服务；无直接状态旁路；失败原子回滚；二次
seed 幂等。

---

## 8. D3：一键启动、八个主要页面（含 `/data`）E2E 与关闭

### Task D3.1：四条可重现命令

**Files:**

- Create: `scripts/seed_damai_demo.py`
- Create: `scripts/verify_damai_demo.py`
- Create: `scripts/tests/test_verify_damai_demo.py`
- Modify: `Makefile`

- [ ] 提供 `damai-demo-build`、`damai-demo-seed`、`damai-demo-verify`、
      `damai-demo-up`；`stack-up` 保持空环境语义。
- [ ] receipt 对账发行包、数据库、API、冻结哈希和对象存储哈希。
- [ ] 在隔离 compose project 中 seed 两次并 verify，机器证据写 `work/damai-demo/`。

### Task D3.2：八个主要页面（含 `/data`）真实 E2E

**Files:**

- Create: `apps/web/e2e/damai-demo.spec.ts`
- Create: `scripts/test_damai_demo_e2e.sh`
- Modify: `Makefile`

- [ ] `/data` 真实上传 XLSX，完成映射、校验、warning 确认和发布。
- [ ] `/`、`/investigations`、`/reports`、`/statements`、`/analysis`、
      `/operations`、`/metric-library` 都显示大麦、期间和非空关键内容。
- [ ] 验证已支持的组织/客群/产品/区域粒度，不虚构 UI 尚不存在的四级下钻。
- [ ] 完成一次 Finding 审核和一次报告下载 SHA 校验。
- [ ] 动态端口、owned supervisor、cleanup trap；禁止 page mock。

### Task D3.3：全量回归和权威文档刷新

Run:

```bash
make contracts-check
make test-api
make test-web
make lint
make typecheck
python3 scripts/check_docs.py --phase m6
python3 scripts/documentation/plan_views.py --check
git diff --check
```

- [ ] 复跑 U8 非破坏回归和发行包零漂移检查。
- [ ] 用实测数字更新 README、PROJECT_STATE、READING_ORDER、ROADMAP、HANDOFF。
- [ ] 先以 active 状态提交实现关闭证据，再单独提交 completed 状态。
- [ ] 只有最终 completed SHA 的远端 required jobs 全绿才宣布完成。

---

## 9. U：真实数据驱动的剩余体验收口

此轨只处理前端两份计划未完成、且仍符合 D052–D054 的项目：

U 即使在 D3 完成后也保持 blocked；在转 active 前，必须先按当时代码基线把本节
补齐为精确 Files、红灯 selector、Run、预期输出和视觉证据路径，同步 UX 工作包
与路线图并 commit/push。依赖完成不等于自动授权实施。

### Task U1：导出审计与真实溯源

- [ ] 下载/导出事件写追加式审计；授权与审计语义分别测试。
- [ ] Provenance 由现有键盘/触控浮层跳转到真实来源记录或 PDF 页锚。
- [ ] 无页锚时显示 typed unavailable，不构造虚假链接。

### Task U2：经分专员工作流与渐进披露

- [ ] 首页按待审批草稿、异常指标和未完成构建组织，不退化为图表墙。
- [ ] 固定下钻为指标 → 行项目 → 原文；报告为结论 → 证据 → 原文。
- [ ] 治理操作默认折叠，但规则、指标、口径和配置保持高度可见。
- [ ] 复用现有三视口、五态和 60 图状态矩阵门禁。

### Task U3：明确继续暂缓的项目

- [ ] Recharts 只在交互式缩放/联动/多序列需求正式成立时重新评估。
- [ ] Excel 共生导出、复杂自由制表、多主题和打印样式进入 backlog，不自动立项。
- [ ] 不引入通用 BI 拖拽、自定义仪表盘或无证据的自由 NL2SQL。

**退出条件：** 大麦真实数据态和错误态均通过；不新增第二套组件系统；同 SHA
unit/e2e/视觉证据/CI 全绿。

---

## 10. K：第二代静态知识刷新与战略重基线

K 轨跨 FLOW、Davybase、ObsidianWiki 三仓库。每个仓库先 pull、独立提交并立即
push；敏感/排除目录 fail closed。详细 schema 和命令合同继承批准规格
`FLOW-DESIGN-KNOWLEDGE-REFRESH-002`，以下为唯一后续领取顺序。

### Task K1：Davybase K0/K1 审计与非微信图片覆盖

**Repositories:** `/Users/qiming/workspace/davybase`、`/Users/qiming/ObsidianWiki`

**Files:**

- Modify: `scripts/run/image_digest.py`
- Modify: `scripts/run/note_summary.py`
- Create: `scripts/run/knowledge_run_manifest.py`
- Create: `scripts/run/image_coverage.py`
- Create: `config/knowledge_enrichment_scope.yaml`
- Create/Modify: `tests/test_knowledge_run_manifest.py`、`tests/test_image_digest.py`、
  `tests/test_note_summary.py` 及 coverage tests
- Create: `docs/evidence/runs/<K0_RUN_ID>.jsonl`
- Create: `docs/evidence/2026-09-18-image-batch-acceptance.md`
- Create in FLOW: `docs/knowledge-base/02_research/synthesis/2026-09-18-davybase-image-batch-acceptance.md`

- [ ] 先运行 `.venv/bin/python -m pytest tests/test_knowledge_run_manifest.py -q`，
      用同名同大小异内容、附录剥离、缺 envelope 和互斥终态取得预期红灯。
- [ ] 建立 `davybase-knowledge-run/v1`，用正文/图片集合 SHA-256，不再使用名称
      和大小推导身份；dry-run 必须零写入。
- [ ] 机器复算既有 1,265 输入的互斥终态，验收 1,241 成功与 24 装饰图，
      无法恢复的旧字段标 `nonconformant`，不得伪造 provenance。
- [ ] allowlist 覆盖企业管理、财务与会计、跨境物流；拒绝绝对路径、`..`、
      symlink 逃逸和敏感目录。
- [ ] coverage、run manifest、异常清单和 Obsidian pathspec 对账后，才允许受控
      apply、提交和推送。

Run：

```bash
cd /Users/qiming/workspace/davybase
.venv/bin/python scripts/run/knowledge_run_manifest.py retrospective \
  --vault /Users/qiming/ObsidianWiki --scope processed/微信知识库 \
  --pre-k1-commit <PRE_K1_COMMIT> --pre-k1-tree <PRE_K1_TREE> \
  --batch-code-commit <ORIGINAL_BATCH_COMMIT> \
  --expected-inputs 1265 --expected-success 1241 --expected-filtered 24 \
  --output docs/evidence/runs/<K0_RUN_ID>.jsonl
.venv/bin/python scripts/run/knowledge_run_manifest.py verify \
  --manifest docs/evidence/runs/<K0_RUN_ID>.jsonl --strict
.venv/bin/python scripts/run/image_coverage.py scan \
  --vault /Users/qiming/ObsidianWiki \
  --scope processed/02_企业管理 --scope processed/03_财务与会计 \
  --scope processed/04_跨境物流 \
  --output .davybase/progress/<K1_RUN_ID>/coverage-before.json
.venv/bin/python scripts/run/image_digest.py --vault /Users/qiming/ObsidianWiki \
  --dir processed/02_企业管理 --dir processed/03_财务与会计 \
  --dir processed/04_跨境物流 --dry-run --run-id <K1_RUN_ID> \
  --manifest .davybase/progress/<K1_RUN_ID>/run.jsonl
.venv/bin/python scripts/run/image_digest.py --vault /Users/qiming/ObsidianWiki \
  --dir processed/02_企业管理 --dir processed/03_财务与会计 \
  --dir processed/04_跨境物流 --apply --run-id <K1_RUN_ID> \
  --manifest .davybase/progress/<K1_RUN_ID>/run.jsonl
.venv/bin/python scripts/run/image_digest.py \
  --vault /Users/qiming/ObsidianWiki \
  --retry-from .davybase/progress/<K1_RUN_ID>/run.jsonl \
  --apply --run-id <K1_RETRY_RUN_ID> \
  --manifest .davybase/progress/<K1_RETRY_RUN_ID>/run.jsonl
.venv/bin/python scripts/run/image_coverage.py scope-check \
  --vault /Users/qiming/ObsidianWiki \
  --run-manifest .davybase/progress/<K1_RUN_ID>/run.jsonl \
  --pathspec .davybase/progress/<K1_RUN_ID>/obsidian-pathspec.txt
.venv/bin/python -m pytest tests -q
```

成功输出必须包含 `retrospective manifest: PASS`、`coverage scan: PASS`、
`image digest dry-run: PASS`、`image digest apply: PASS`、
`image digest retry: PASS`、`scope check: PASS`。
Obsidian 只按已验证 pathspec 暂存；Davybase 与 Obsidian 分别 commit/push，任一失败
则 K1 未完成。FLOW 只登记汇总、定位符和哈希，不复制原始图片或全文。

### Task K2：首个稳定 15:00 Git 截面

**Repositories:** Davybase + ObsidianWiki

**Files:**

- Create: `scripts/run/freeze_snapshot.py`
- Create: `tests/test_freeze_snapshot.py`
- Create: `docs/evidence/snapshots/<SNAPSHOT_ID>.json`

- [ ] 先写红灯：缺锁、tree 漂移、dirty、远端不可获取必须失败；accepted manifest
      必须包含锁身份、三个时间点、writer、两次 HEAD/tree/status 和计数。
- [ ] 14:30 Asia/Shanghai 取得排他锁并停止所有 writer。
- [ ] 15:00 记录候选，15:30 复验 HEAD/tree/clean/锁/远端可获取性。
- [ ] 任一漂移写 committed `rejected` manifest 并顺延，不伪造时间点。
- [ ] accepted manifest 是 snapshot date、ID 和 release ID 的唯一来源。

Run（脚本必须核对本机实际时钟，不能只相信 `--at` 文本）：

```bash
cd /Users/qiming/workspace/davybase
.venv/bin/python -m pytest tests/test_freeze_snapshot.py -q
.venv/bin/python scripts/run/freeze_snapshot.py acquire \
  --vault /Users/qiming/ObsidianWiki --timezone Asia/Shanghai \
  --lock-id <FREEZE_LOCK_ID> --manifest <FREEZE_MANIFEST>
.venv/bin/python scripts/run/freeze_snapshot.py candidate \
  --vault /Users/qiming/ObsidianWiki --at 15:00 --manifest <FREEZE_MANIFEST>
.venv/bin/python scripts/run/freeze_snapshot.py verify \
  --vault /Users/qiming/ObsidianWiki --at 15:30 --canonical-remote origin \
  --manifest <FREEZE_MANIFEST>
git add <FREEZE_MANIFEST>
git commit -m 'docs: freeze <SNAPSHOT_ID> evidence'
git push origin main
.venv/bin/python scripts/run/freeze_snapshot.py release \
  --lock-id <FREEZE_LOCK_ID> --manifest <FREEZE_MANIFEST>
```

成功必须输出 ACQUIRED/RECORDED/ACCEPTED/RELEASED。accepted/rejected manifest
都必须严格按 `verify/reject → git add → commit → push → release` 持久化；push
失败时保持锁并停止，不得先 release。不得自动提交未知 Obsidian 修改来制造 clean。

### Task K3：FLOW 来源基线、知识综合和 sealed candidate

**Repository:** FLOW

**Files:**

- Modify: `scripts/documentation/source_baseline.py`
- Create/Modify: `scripts/documentation/coverage_validator.py`、
  `scripts/documentation/knowledge_release.py`、`scripts/documentation/reader_rubric.py`
- Create/Modify: 对应 `scripts/tests/test_*.py`
- Create: `docs/knowledge-base/00_governance/migration/source-inputs-<SNAPSHOT_DATE>.yaml`
- Create: `docs/knowledge-base/00_governance/migration/source-id-registry-<SNAPSHOT_DATE>.tsv`
- Create: `docs/knowledge-base/10_sources/{source-baseline,source-diff,coverage,image-exceptions}-<SNAPSHOT_DATE>.tsv`
- Create: `docs/knowledge-base/00_governance/change-manifests/<SNAPSHOT_ID>-l2.tsv`
- Create: `docs/knowledge-base/00_governance/releases/<RELEASE_ID>/**`
- Create: `docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/**`
- Create: `docs/knowledge-base/02_research/synthesis/<SNAPSHOT_DATE>-obsidian-refresh-final-report.md`
- Create: `docs/knowledge-base/30_domain_handbooks/product_experience/README--v1.0.md`
- Create: `docs/knowledge-base/30_domain_handbooks/knowledge_ai_engineering/README--v1.0.md`
- Modify: `docs/knowledge-base/50_product_mappings/FLOW-PRODUCT-MAPPING--v1.0.md`
- Create: `docs/knowledge-base/50_product_mappings/adoption-register-<SNAPSHOT_DATE>.tsv`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`

- [ ] 为 source baseline、coverage validator、release seal 和 reader rubric 分别先写
      最小红灯，再实现到目标 selector 和完整模块全绿。
- [ ] 从旧 tree `36274b2463aad9eae069af805e53e937c704c381` 到 accepted tree
      生成 NFC/LF、附录剥离、跨改名 registry 和四维 diff；同 tree 重跑字节一致。
- [ ] 完成 allowlist 全量路由、HIGH 全量精读、MED/LOW 双审和错误集中度审查。
- [ ] HIGH 漏检率 >5%、核心不可读 >1%、系统性误分或敏感泄漏均阻断 seal。
- [ ] 构建 `flow-knowledge-<SNAPSHOT_DATE>.N`，独立 reader 达到可回答率 100%、
      来源链 100%、unsupported=0、P1/P2=0；seal 后内容不可变。
- [ ] `CURRENT_RELEASE` 保持旧值，直到用户完成战略裁决。

Run：

```bash
python3 -m unittest scripts.tests.test_source_baseline
python3 scripts/documentation/source_baseline.py build-v2 \
  --snapshot-manifest <K2_ACCEPTED_MANIFEST> \
  --previous-tree 36274b2463aad9eae069af805e53e937c704c381 \
  --input-manifest docs/knowledge-base/00_governance/migration/source-inputs-<SNAPSHOT_DATE>.yaml \
  --registry docs/knowledge-base/00_governance/migration/source-id-registry-<SNAPSHOT_DATE>.tsv \
  --baseline docs/knowledge-base/10_sources/source-baseline-<SNAPSHOT_DATE>.tsv \
  --diff docs/knowledge-base/10_sources/source-diff-<SNAPSHOT_DATE>.tsv
python3 scripts/documentation/coverage_validator.py \
  --coverage docs/knowledge-base/10_sources/coverage-<SNAPSHOT_DATE>.tsv \
  --exceptions docs/knowledge-base/10_sources/image-exceptions-<SNAPSHOT_DATE>.tsv \
  --change-manifest docs/knowledge-base/00_governance/change-manifests/<SNAPSHOT_ID>-l2.tsv --strict
python3 scripts/documentation/knowledge_release.py build \
  --config docs/knowledge-base/00_governance/releases/<RELEASE_ID>/release.yaml
git add --pathspec-from-file=<TASK_5_TO_7_DRAFT_PATHSPEC>
git commit -m 'docs: build <RELEASE_ID> draft candidate'
git push origin HEAD
git worktree add --detach ../FLOW-reader-<RELEASE_ID> HEAD
cd ../FLOW-reader-<RELEASE_ID>
python3 scripts/documentation/reader_rubric.py run \
  --questions docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/questions.yaml \
  --expected docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/expected.yaml \
  --rubric docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/rubric.yaml \
  --answers <INDEPENDENT_READER_ANSWERS> \
  --results docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/results.yaml \
  --reader-id <INDEPENDENT_READER_ID> --attest-independent-from 5,6
cd <ORIGINAL_FLOW_WORKTREE>
# 使用 apply_patch 将独立 reader 返回的 results 内容写入固定 results.yaml；
# 不从 detached worktree 直接提交或覆盖原工作树。
python3 scripts/documentation/knowledge_release.py seal --release <RELEASE_ID>
python3 scripts/documentation/knowledge_release.py verify --release <RELEASE_ID>
git add docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/results.yaml \
  docs/knowledge-base/00_governance/releases/<RELEASE_ID>
git commit -m 'docs: seal <RELEASE_ID> candidate'
git push origin HEAD
```

预期包含 `source baseline v2: PASS`、`coverage: PASS`、
`reader gate: PASS (answerable=100%, sources=100%, unsupported=0, p1=0, p2=0)`、
`seal <RELEASE_ID>: PASS` 和 `verify <RELEASE_ID>: PASS`。独立 reader 在 detached
clean checkout 执行；draft 先持久化，再由独立 reader 产出结果，结果经受控补丁写回
原工作树后才能 seal。任何 commit/push、reader、结果写回或 verify 失败均不得 seal。

### Task K4：战略影响、用户裁决和原子激活

**Repository:** FLOW

**Files:**

- Create: `docs/knowledge-base/04_decisions/<SNAPSHOT_DATE>-strategic-impact-assessment.md`
- Create: `docs/knowledge-base/04_decisions/<SNAPSHOT_DATE>-strategic-decision-proposal.md`
- Create: `docs/80_reviews/knowledge-refresh/<RELEASE_ID>/activation-file-manifest.tsv`
- Modify after user decision only: `README.md`、PROJECT_STATE、READING_ORDER、
  DECISION_INDEX、CHANGE_IMPACT_MAP、CURRENT_ROADMAP、两个 HANDOFF、
  `CURRENT_RELEASE` 及 activation manifest 中批准的精确路径

- [ ] 以 keep/amend/add/remove/defer 逐项评估 D052–D054、产品文档和路线图。
- [ ] 只提交提案；用户逐项 accepted/amended/rejected/deferred 是硬门。
- [ ] 只修改 activation manifest 中获批的精确路径；sealed 目录零 diff。
- [ ] 新 release 指针、正式决策、产品文档、README、ROADMAP 和 HANDOFF 在同一
      activation commit 生效；detached clean checkout 独立复验后再 push。
- [ ] 远端 CI 失败时用普通 revert 恢复完整一致性集合，不改写历史。

S0 影响评估先 commit/push，再停止等待用户 S1 逐项裁决。获批后创建 activation
commit A 和外置验证证据 commit E；sealed release/reader 目录在 A/E 中必须零
diff。对 E 的 `FINAL_SHA` 在 detached clean worktree 执行：

```bash
python3 scripts/documentation/source_baseline.py check-v2 \
  --snapshot-manifest <K2_ACCEPTED_MANIFEST> \
  --baseline docs/knowledge-base/10_sources/source-baseline-<SNAPSHOT_DATE>.tsv \
  --diff docs/knowledge-base/10_sources/source-diff-<SNAPSHOT_DATE>.tsv
python3 scripts/documentation/knowledge_release.py verify --release <RELEASE_ID>
python3 scripts/documentation/reader_rubric.py verify \
  --questions docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/questions.yaml \
  --expected docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/expected.yaml \
  --rubric docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/rubric.yaml \
  --results docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/results.yaml
python3 scripts/check_docs.py --phase m6
python3 scripts/documentation/links.py --check
python3 scripts/documentation/kb_manifest.py --check
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
git status --porcelain=v1 --untracked-files=all
```

最后一条必须为空，其余返回 0；随后 push 并等待同 SHA CI。

---

## 11. E：公开财报模块 C 级出口与真实数据扩张

E 当前保持 blocked。外部 oracle/holdout/盲评到料后，必须先在本计划补齐当批
精确 Files、红灯 selector、Run、预期输出和交付路径，同步工作包与路线图并
commit/push；完成这一步后才可把 E1 改为 active 或开始实现。

### Task E1：完成 C 级出口外部门禁

- [ ] L0 1454/1454 基准进入 required CI job。
- [ ] 独立 oracle 对 L1 答案集复核；补齐当前未定位值，不静默缩小分母。
- [ ] 由用户按预注册规则抽取整公司 holdout，代码在启封前不得专项适配。
- [ ] 使用不同厂商模型完成独立盲评；零严重事实错误。
- [ ] 全量准确率阈值保持用户已裁决的 100%；失败逐项归因。

### Task E2：真实公开数据扩张

- [ ] 按物流 → 电商 → SaaS，每批五家公司扩到至少 15 家/80 份报告。
- [ ] 每批执行 L0、每家至少 20 点 L1、发布冻结和快照。
- [ ] 行业基准必须记录来源、期间和样本集合；无来源数值不得进入正式通道。
- [ ] 10× 性能已有基线继续作为回归约束；阈值变化需用户裁决。

**停机条件：** oracle/holdout/盲评未到料时保持 blocked；不得由实现 Agent 自评
解除独立性门槛。

---

## 12. I：授权内部工作台与真实企业验证

I 当前保持 gated。获得内部数据授权且 E1 关闭后，必须先在本计划补齐实际数据
合同、Files、TDD/Run、脱敏与回滚方案、三周期验收命令，同步工作包与路线图并
commit/push；E2 数据扩张不是 I 的硬前置。

### Task I1：内部数据合同与接入

- [ ] 获得内部数据授权后，冻结主数据、字段映射、版本身份和事件簿合同。
- [ ] 接入实际、预算、同比/环比、应收/回款/现金及经营事件；禁止年度数据摊月。
- [ ] O5 六主题闭环、多维盈利守恒和一报一会记录复用共享事实底座。

### Task I2：双 AI 与人工发布边界

- [ ] 分析 AI 生成大部分事实、证据、结论和报告草稿；CFO AI 做角色化复核。
- [ ] 经分专员统一审核发布；Finance BP 只提供和确认数据，不承担报告制作。
- [ ] 规则、制度、指标、科目定义和配置中心对用户高度可见。

### Task I3：四级真实验证

- [ ] 连续三个完整月度周期与同输入人工基准逐周期比较。
- [ ] 逐周期盲评准确性、可追溯性、遗漏、复核量和失败样本。
- [ ] 达成批准的质量门槛和至少 20% 工时改善后，才可宣称内部工作台验证完成。

---

## 13. F：U10 证据决策与下一版本

F 当前保持 blocked。依赖证据齐备后，必须先在本计划补齐证据包文件、决策模板、
校验命令和正式 decision 路径，同步 U10 工作包与路线图并 commit/push；之后才
可开始 go/hold/drop 裁决。

- [ ] 汇总 U4/C 级出口、U8 和内部三周期证据；D/K 证据若已完成可作为补充，
      但不是 U10 的硬依赖。
- [ ] 对指标默认展示、预算预测、量价桥、多维盈利、行动闭环、Copilot/LLM
      通道逐项作 go/hold/drop；无证据默认 hold。
- [ ] 输出正式 D 系列决策、新版本范围、迁移/兼容影响、验收门禁和不做清单。
- [ ] 新一轮计划先落盘、索引、commit、push，再开始任何 V1.1/V2 实现。

## 14. 全局停机条件

以下任一情况必须停止当前任务并先修根因：

- 需要删除文件、修改 schema/migration、`.env`、CI/CD 或强推，但没有用户授权；
- 工作区出现来源不明或范围外修改；
- 为过测试而直接改状态、吞错误、补 0、伪造来源、页面 mock 或弱化断言；
- 生成器、静态发行包、数据库、API 和 UI 无法对账；
- 知识截面漂移、敏感内容泄漏、coverage 分母不闭合；
- 测试、截图、交付证据和 CI 不是同一提交；
- 用户或第三方门禁尚未完成，却准备把 gated/blocked 写成 completed。

## 15. 每个阶段的统一交付格式

每次交付必须记录：

1. `base_sha`、分支和最终 commit；
2. 计划任务 ID 与精确文件清单；
3. 红灯、绿灯、全局门禁和返回码；
4. 数据/迁移/契约/知识 release 是否变化；
5. 范围检查与已知残余风险；
6. push 和同 SHA CI 结果；
7. `CURRENT_ROADMAP`/工作包状态是否需要更新。

## 16. 总完成定义

FLOW 下一阶段只有在以下全部成立时才能关闭：

- 大麦完整财年数据可重建、幂等装载并填满八个页面；
- 文档、前端、API、发布下载和 U8 回归在同一最终 SHA 全绿；
- 第二代知识 release 经稳定 Git 截面、覆盖门禁、独立 reader 和用户裁决后激活；
- 公开 C 级独立验证完成，真实数据扩张通过；
- 授权企业连续三个周期达到质量和工时门槛；
- U10 对下一版本能力逐项形成正式证据决策；
- 仓库只剩 `CURRENT_ROADMAP` 一份状态真相和本文件一份详细执行合同。
