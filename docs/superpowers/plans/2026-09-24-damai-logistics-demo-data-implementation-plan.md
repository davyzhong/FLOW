---
doc_id: FLOW-PLAN-DAMAI-DEMO-20260924
title: 大麦物流完整财年演示数据实施计划
doc_type: plan
status: archived
version: 2.5
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-SPEC-DAMAI-DEMO-001, FLOW-REV-DAMAI-PARTIAL-20260924]
acceptance_refs: [FLOW-SPEC-DAMAI-DEMO-001]
applies_to: repository
superseded_by: FLOW-PLAN-INTEGRATED-EXECUTION-20260924
do_not_execute: true
---

# 大麦物流完整财年演示数据实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:test-driven-development`, `superpowers:executing-plans` and
> `superpowers:verification-before-completion`. 每个任务先红后绿，每次 commit 后立即 push。


## 0. 执行进度总览（2026-09-24 晚，ZCode 会话登记）

> 本节是执行状态对照（单一事实源仍为下方 §3–§5 的任务清单）；每完成一个任务，在此表与对应 checkbox 双向登记。

**基线现状**：`codex/damai-logistics-implementation@fc3f6a7`。已完成 Task 1–3（画像/生成器/闭合财报）、发行版首版（`690ad5e`）、装载器 slice-1 财报子链（`b5b3354`）与分析链 slice-2a（`cd9c4b4`：工作簿 IntakeService 全链 → 12 快照 → AnalysisRun，批次幂等；fixtures 全量 45 测试绿）。

**顺序裁决**：按 §3 阶段 A → §4 阶段 B → §5 阶段 C 严格串行执行。已完成的 slice-2a 定位为「贯通性验证」（证明领域服务链可走通），其聚合粒度与 9988.HK 复用被 A2/A3 的明细化与独立身份取代——先按 A 系列重构数据合同，再灌库，避免对半成品数据做页面验收。**在 A4 完成（发行包重建）之前不执行任何正式灌库。**

| 任务 | 内容 | 状态 | 产出/接续点 |
|---|---|---|---|
| A1 | 失败测试锁定全量数据合同（明细级 1,920/10,752/4,800） | done（`ece11d2`） | 红灯证据 `work/damai-demo/a1_red_evidence.txt`（不入 git） |
| A2 | 重构明细生成器与 canonical 投影（40 客户×8 产品×6 区域，无聚合成员） | done（`4950e73`） | 取代 slice-2a 的聚合方案；fixtures 58+4 全绿、ruff 净 |
| A3 | 修正财报来源（DAMAI.SYN 独立身份）与正式审核链（禁直改 status） | done（`1052ea6`） | 报表升级为合并报表范式（勾稽门禁真实生效）；发行版同步重建 |
| A4 | 重建静态发行包 + 消除漂移（manifest 血缘字段、README frontmatter） | done（见本次提交） | manifest 新增 lineage/dimension_coverage/fiscal_year_summary/planted_events；--check PASS |
| B1 | 事务化整体 seed（AnalysisCycle 绑定 + 三类回滚注入 + 全对象幂等） | done（见本次提交） | 扩展 slice-2a 的 loader；freeze 注入随 B2 冻结实现补测 |
| B2 | 调查/证据/结论/冻结报告（candidate/in_review/approved 混合 + 冻结 SHA） | done（见本次提交） | = 原 slice-2b；实际产出 2 个 Finding（5 playbook 中 2 个过阈值），6 信号映射入 receipt；freeze 故障注入已补测 |
| B3 | 指标覆盖投影（damai 数据集 + 前端切换 + synthetic 标识） | done（见本次提交） | damai_demo_metric_coverage_v1.yaml + dataset 参数 + 前端 tab/合成标识；A2 五粒度对账一并验收 |
| C1 | `damai-demo-build/seed/verify/up` 四命令 + 机器可读 receipt | done（见本次提交） | 隔离 compose project（15432/16379/19000）双 seed 幂等 + verify 17/17，证据 work/damai-demo/ |
| C2 | 八页面真实 E2E（含 /data 页面上传旅程） | done | 「菜单全满」的验收关 |
| C3 | 完整回归 + 文档刷新 + 最终 CI 闭环（completed SHA 全绿才算完成） | pending | 交付关闭 |

**明确不做**：不新增 migration、不改 CI/.env、forecast 保持 static-only、不覆盖既有非大麦 fixture（§2 约束不变）。

## 1. 目标与成功标准

建立 `damai-logistics-demo-v1`：一套确定性、可重建、可幂等装载的合成数据发行版。
它包含 FY2025 同比期和 FY2026 完整分析财年，并用同一份发行包证明数据导入、
经营分析、财务分析、指标、Finding、审核、冻结、发布和下载链可用。

完成不以“页面有字”判定，而以下列全部成立判定：

1. 全维度数据达到规格 §3.3，不用聚合客户/产品/区域冒充明细；
2. 全部对账和财务恒等式通过，故意植入的 6 类异常能被系统发现；
3. 只有一个 enterprise_id，所有数据可通过真实授权依赖访问；
4. 导入、审核、发布都调用正式领域服务，不手改状态、不直接造最终对象；
5. 二次 seed 零增长，三类故障注入均整体回滚；
6. 八个主页面和 `/data` 真实上传旅程通过；
7. 发行包零漂移、文档门禁、全量回归和同一最终 SHA 的 CI 全绿。

## 2. 当前基线与执行约束

- 实现基线：`codex/damai-logistics-implementation@cd9c4b4`；
- 已通过：6 个大麦定向测试文件、36 项测试；
- 未通过验收：见 `FLOW-REV-DAMAI-PARTIAL-20260924`；
- 不新增 Alembic migration，不修改 `.env` 或 CI/CD，不部署生产；
- forecast 继续为 `static-only` sidecar，不冒充已上线数据库能力；
- 现有非大麦公开财报 fixture 不得被覆盖或改名；
- 一个任务一个可审查 commit，提交前运行定向验证，提交后立即 push。

## 3. 阶段 A：先修正当前半成品

### Task A1：用失败测试锁定全量数据合同

**Files:**
- Modify: `services/api/tests/fixtures/test_damai_profile.py`
- Modify: `services/api/tests/fixtures/test_damai_generator.py`
- Modify: `services/api/tests/fixtures/test_damai_canonical.py`
- Modify: `services/api/tests/fixtures/test_damai_statements.py`

- [x] 断言 1+4 组织、4 客群、40 客户、8 产品、6 区域均实际进入 canonical。
- [x] 断言每个分析月均覆盖全部客户、产品、区域和业务单元，且无 `*-AGG`/`R-ALL`。
- [x] 断言 AR 是 24×40×5 账龄粒度，预算覆盖收入、三类直接成本、期间费用、经营利润和经营现金流原始行。
- [x] 断言经营↔财务对账、实际与预算具有同期间/维度可比性（不断言数值相等）、AR↔回款↔现金流以及两个财年的四表恒等式。
- [x] 断言预算逐月/组织/客群/产品的收入-三成本-期间费用=经营利润，并验证经营现金流调节表闭合。
- [x] 先运行并保存红灯证据；不允许先改实现后补断言。（红灯证据 `work/damai-demo/a1_red_evidence.txt`）

### Task A2：重构明细生成器与 canonical 投影

**Files:**
- Modify: `services/api/src/flow_api/fixtures/damai/profile.py`
- Modify: `services/api/src/flow_api/fixtures/damai/generator.py`
- Modify: `services/api/src/flow_api/fixtures/damai/canonical.py`
- Modify: `services/api/src/flow_api/fixtures/damai/validation.py`

- [x] 为 40 客户固定客群、主区域、信用期；为 8 产品固定业务族和业务单元。
- [x] 以“月×客户×2 个活跃产品”产生约 1,920 条经营明细，使用 UUID5、Decimal 和显式尾差分配。
- [x] 生成 24 月×4 业务单元×核心科目财务实际，逐月对账经营明细。
- [x] 生成 12 月×4 业务单元×4 客群×8 产品×7 类原始预算行，以及 24×40×5 账龄数据。
- [x] 预算引擎投影只使用 `REVENUE`/`DIRECT_COST`/`OPERATING_PROFIT`/`OPERATING_CASH_FLOW`；3 类成本汇总为 `DIRECT_COST`，毛利由引擎派生，期间费用标记为未执行的明细 coverage gap。
- [x] 用真实 `MetricCalculator`/快照断言 `REVENUE`/`DIRECT_COST` 在 total、organization、segment、product、segment×product 五种粒度与 manifest 一致；`OPERATING_PROFIT`/`OPERATING_CASH_FLOW` 仅在合同支持的 total/organization 粒度对账；三成本不漏算/重算。（已在 B3 验收：tests/fixtures/test_damai_metric_grain.py 五粒度对账全绿；OCF actual 因工作簿合同仅 7 科目如实缺席，budget 侧对账）
- [x] 保留六类故意事件，但影响必须能追溯到具体客户/产品/区域/月。
- [x] 运行 A1 和既有 data-contract/metrics 测试，提交 `fix(fixtures): expand damai canonical detail coverage` 并 push。

### Task A3：修正财报来源和正式审核链

**Files:**
- Modify: `services/api/src/flow_api/fixtures/damai/loader.py`
- Modify: `services/api/src/flow_api/statements/normalization.py`
- Modify: `config/statements/item_alias_map_v1.yaml`
- Modify: `services/api/src/flow_api/operations/engine.py`
- Modify: `services/api/tests/fixtures/test_damai_loader.py`
- Modify: `services/api/tests/statements/test_normalization.py`
- Modify: `services/api/tests/operations/test_operations_engine.py`

- [x] 先写红灯：导入 payload 和 SHA 必须来自 `fixtures/damai/statements/damai_fy*.yaml`，股票代码必须是独立 `DAMAI.SYN`，不得读取或冒充阿里巴巴原始 fixture。
- [x] 为 `DAMAI.SYN` 建立独立 company key 与归一化映射，断言不与 `9988.HK` 的唯一身份/重述链重叠。
- [x] 生成并加载 `DAMAI.SYN` 独立运营事实与分部序列，断言 `/operations` 不读取 Alibaba segment/operating fixture。
- [x] 先写红灯：监视 `ReviewService.publish` 必须被调用，直接改 `report.status` 必须失败。（篡改财报被 ReviewBlockedError 阻断，证明门禁有牙）
- [x] 执行 import → normalize → quality/review publish；检查 source SHA、normalized rows、published。（freeze 归属 B2；报表范式升级为合并报表+CAS 规范行名，使勾稽门禁真实生效——对计划 Files 的扩充：statements.py 与其测试）
- [x] 运行 statements/review/publishing 定向测试，提交 `fix(demo): use synthetic statements and governed review` 并 push。

### Task A4：重建静态发行包并消除漂移

**Files:**
- Modify: `scripts/build_damai_demo.py`
- Modify: `services/api/tests/fixtures/test_damai_canonical.py`
- Generate: `fixtures/damai/**`

- [x] manifest 增加规格 §3.3 的维度覆盖、财年汇总、事件可发现性和数据血缘字段。
- [x] 生成的 `fixtures/damai/README.md` 携带合法 frontmatter，不得破坏 M6 文档门禁。
- [x] 在临时目录连续构建两次，文本 SHA 与 XLSX 语义指纹一致。
- [x] 重建正式 `fixtures/damai/**`，运行 `--check` 和 `git diff --check`。
- [x] 提交生成器与全部同源产物 `feat(fixtures): rebuild complete damai fiscal-year release` 并 push。

## 4. 阶段 B：贯通全部领域对象

### Task B1：事务化、幂等化整体 seed

**Files:**
- Modify: `services/api/src/flow_api/fixtures/damai/loader.py`
- Modify: `services/api/src/flow_api/intake/service.py`
- Create: `services/api/tests/fixtures/test_damai_loader_atomicity.py`
- Modify: `services/api/tests/fixtures/test_damai_loader_analytics.py`
- Modify: `services/api/tests/integration/test_intake_service.py`

- [x] seed 起点复用唯一 bootstrap enterprise，建立/复用一个截止月 `2026-08` 的 AnalysisCycle，并明确将大麦 AnalysisBatch 绑定该周期；24 个历史月份由 Period/事实表表达。
- [x] 扩展 `IntakeService.create_batch()` 使其可选显式接收 analysis_cycle_id，保留现有调用默认语义；用兼容测试证明旧调用不变，大麦装载不依赖“全库最早周期”选择。
- [x] 工作簿必须经 IntakeService 的 source、mapping、validate、warning acknowledgement、publish 链。
- [x] 建立 12 个指标快照和 1 个 AnalysisRun，通过真实 API 依赖验证单企业授权。
- [x] 整个装载器只在顶层提交；注入不变量、第二份财报、intake publish 三类失败，都断言零部分数据。（freeze 注入随 B2 冻结实现补测）
- [x] 二次 seed 后 batch/import/snapshot/run/report/normalized rows/source object 计数不增长（ReviewEvent 表不存在，发布动作幂等跳过）。
- [x] 提交 `feat(demo): make damai seed atomic and idempotent` 并 push。

### Task B2：生成调查、证据、结论和冻结报告

**Files:**
- Modify: `services/api/src/flow_api/fixtures/damai/loader.py`
- Create: `services/api/tests/fixtures/test_damai_loader_workflow.py`

- [x] 将植入事件表达为至少 6 个可追溯分析信号；只由现有 5 个 playbook 生成最多 5 个系统 Finding，业务单元预算差异/产品组合信号作为证据或次级解释，不伪造第 6 个 playbook。（实际 2 个 Finding 过阈值；E1–E6 六信号入 receipt.signals，E4 预算差异/E5 现金流收窄作结论次级解释与未决问题）
- [x] 落库状态覆盖 candidate/in_review/approved；通过 `submitted` decision 从 candidate 进入 in_review，只有 approved Finding 可进入正式结论。（首个 Finding submitted→approved，其余停在 in_review；冻结报告只含 approved）
- [x] 冻结内部分析报告、两年客观财报快照和经营概览，并验证发布/下载 SHA。（digest_view / payload_hash 均由载荷重算验证）
- [x] 断言所有结论都能追溯到发行包 SHA 和 canonical record_id。（verified_facts 含 manifest sha256 + import-version 引用，测试断言）
- [x] 提交 `feat(demo): seed damai evidence and report workflow` 并 push。

### Task B3：建立大麦 synthetic 指标覆盖投影

**Files:**
- Create: `config/metrics/damai_demo_metric_coverage_v1.yaml`
- Modify: `services/api/src/flow_api/api/schemas/metric_library.py`
- Modify: `services/api/src/flow_api/api/routes/metric_library.py`
- Modify: `apps/web/components/metric-library/metric-coverage-section.tsx`
- Test: `services/api/tests/api/test_metric_library.py`
- Test: `apps/web/components/metric-library/metric-coverage-section.test.tsx`

- [x] API 默认保持 public 真实财报矩阵，`dataset=damai` 返回独立 synthetic 矩阵。（未知 dataset → 400 coverage_dataset_unknown）
- [x] 前端可切换两个数据集，大麦始终显示“合成演示数据”标识。（tab 切换 + synthetic badge，组件测试锁定）
- [x] 覆盖矩阵只展示真实可计算项；其余保留结构化 missing reason，不用 0 补值。（FY2025 22/40、FY2026 25/40，缺口即 bs./is./cf./mpm. 取数原因；引擎毛利率与 manifest 两路径自检一致）
- [x] 提交 `feat(metrics): expose damai synthetic coverage dataset` 并 push。

## 5. 阶段 C：一键启动和系统级验收

### Task C1：增加可重现命令与机器可读 receipt

**Files:**
- Create: `scripts/seed_damai_demo.py`
- Create: `scripts/verify_damai_demo.py`
- Create: `scripts/tests/test_verify_damai_demo.py`
- Modify: `Makefile`

- [x] 实现 `damai-demo-build/seed/verify/up`；`stack-up` 继续保持空环境语义。
- [x] verify 同时对账 manifest、数据库计数、API 响应、冻结哈希和对象存储哈希。（manifest 含 xlsx 语义指纹；对象存储读回按语义指纹比对；API 对账双数据集 coverage）
- [x] receipt 至少包含 release SHA、enterprise/cycle、batch/import、snapshots/run、findings、reports/freezes/publications 和验收结果。（seed receipt schema damai-demo-seed-receipt/v1 全覆盖；verify receipt 含 17 项验收结果）
- [x] 在干净隔离 compose project 中 seed 两次并 verify；证据写入 `work/damai-demo/`（不入 git）。（damai-demo-iso project，双 seed 幂等、verify 17/17；修复发现：seed 链补齐对象存储真实上传）
- [x] 提交 `feat(demo): add damai startup and verification commands` 并 push。

### Task C2：八页面真实 E2E

**Files:**
- Create: `apps/web/e2e/damai-demo.spec.ts`
- Create: `scripts/test_damai_demo_e2e.sh`
- Modify: `Makefile`

- [x] `/data` 从页面上传生成 XLSX，完成映射、校验、warning 确认和发布，验证质量/对账。（damai_logistics_full_v1.xlsx 全程 UI 旅程，阻断 0、对账失败 0、发布成功）
- [x] `/`、`/investigations`、`/reports`、`/statements`、`/analysis`、`/operations`、`/metric-library` 断言大麦名称、期间和关键内容非空。
- [x] 页面分别验证现有支持的 organization/customer segment/product/region 粒度，并通过 metric API 验证 customer 粒度；不宣称 UI 已支持不存在的四级组合下钻。（驾驶舱四粒度筛选 + dashboard API customer_segment 过滤断言子集关系；OCF actual 缺失如实断言 unavailable）
- [x] 走通一次 Finding 审核和一次报告下载 SHA 校验。（收入增长 复核中→批准签发；XLSX 产物下载字节 SHA-256 === attempt.stored_sha256）
- [x] 使用动态端口、owned supervisor 和 cleanup trap；不使用 page mock 或弱化空态断言。（scripts/test_damai_demo_e2e.sh：隔离栈 15432/16379/19000 + 动态 API/Web 端口 + trap 双 down -v）
- [x] 运行大麦 E2E、既有 Web unit、lint、typecheck，提交 `test(e2e): verify damai full product journey` 并 push。（E2E 9/9 通过×2（直跑 38s + 编排脚本全程绿）；Web unit 89/89；tsc、eslint 0 error。红灯修复两处真实缺陷：reports-center 发布未带 Idempotency-Key（§7.1）、API 代理丢弃 Idempotency-Key 头）

### Task C3：完整回归、文档和最终 CI 闭环

**Files:**
- Modify: `fixtures/damai/README.md`
- Modify: `CODE_OF_CONDUCT.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SECURITY.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/50_plans/CURRENT_ROADMAP.md`
- Modify: `README.md`
- Modify: `HANDOFF.md`
- Modify: `docs/README.md`

- [ ] 先执行 `FLOW-PLAN-BASELINE-REPAIR-20260924` Task 1，使 M6 全量零失败。
- [ ] 执行 API unit/integration、contracts、metrics、statements、publishing、Web unit/E2E、lint、typecheck、docs M6、release 零漂移与 U8 非破坏回归。
- [ ] 以 `git merge-base origin/main HEAD` 核对全部变更，断言没有 migration、`.env`、CI/CD 或范围外文件，且 Alembic head 未改变。
- [ ] 用实测计数和命令刷新 README、PROJECT_STATE、ROADMAP、HANDOFF 与导航；不把计划值当成实测值。
- [ ] 保持工作包 active 提交实现关闭文档并 push，验证该 head；随后另一提交改为 completed 并 push。
- [ ] 只有最终 completed SHA 的 required jobs 全绿才宣布完成；若失败，以新提交恢复 active/阻塞并重新验证。

## 6. 预期数据量级（验收下限）

| 对象 | 下限/期望 |
|---|---:|
| 期间 | 24 月（12 分析 + 12 同比） |
| 组织 | 5（1 集团 + 4 业务单元） |
| 客群/客户 | 4 / 40 |
| 产品/区域 | 8 / 6 |
| 经营实际 | 约 1,920 条，分析期每月全维覆盖 |
| 预算 | 10,752 条（12×4×4×8×7） |
| AR/回款 | 4,800 条（24×40×5） |
| 指标快照 | 12 个月，每月实际可算项非空 |
| AnalysisCycle | 1 个，截止月 `2026-08`，大麦批次显式绑定 |
| 分析事件 | 至少 6 个可追溯信号，现有 5 个 playbook 产生的 Finding 全部可验收 |
| 财报 | 2 个财年、4 张表+附注索引，全部通过审核服务 |
| 冻结对象 | 内部分析报告 ≥1，客观财报快照 ≥2，经营概览 ≥2 |

## 7. 停机条件

出现以下任一情况时不得继续堆叠功能，必须先修正：

- 需要新增 schema/migration 或修改 CI/.env；
- 为了让测试绿而直接改发布/审核状态；
- 生成器、静态发行包和数据库三者不能对账；
- 任一失败路径留下部分数据；
- 用页面 mock、固定文字或人工直接插入最终对象替代真实链路。
