---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目交接文档
doc_type: navigation
status: current
version: 9.3
created_at: 2026-09-12
updated_at: 2026-10-19
owner: FLOW
applies_to: repository
---

# FLOW 项目交接文档

> 本文档是下一位 Agent 接手的唯一入口。项目唯一权威状态以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准；本文档提供接手上下文、踩坑记录和下一步操作指引。

---

## 一、当前任务

**当前任务：单机原型架构简化与全视图视觉升级，第 4 阶段 4.1–4.7、准确 SHA CI 与最终集成门禁已全部关闭；当前唯一队首为知识刷新 K2 的 ObsidianWiki 只读预检。** 用户已选择单机单用户、SQLite 单文件 + 本地文件目录、移除 Redis/Celery/MinIO，并批准 A「高管编辑部」+ C「财务报告画布」。第 1–3 阶段完成；第 3 阶段最终状态 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 CI run `39125304357` 18/18 jobs success。首轮 CI 曾发现大麦 reset SQL 的发行包 manifest 哈希未同步；在 `4c3e87e05ae9fe380abb7002ba260de6d654d15c` 只更新对应清单，未改业务数据；脚本 155/155、清单专项 6/6、Ruff/mypy 和 M1/M6 均通过。正式验收见[阶段 3 记录](docs/60_delivery/verification/2026-10-18--single-machine-runtime-convergence-v1.md)。参考文章 10 模块的映射报告已写入[覆盖矩阵](docs/60_delivery/verification/2026-10-18--cfo-reference-module-data-coverage-v1.md)，覆盖页面/API/指标/事实类型/粒度/图表与交互缺口。准确 SHA `d8f2ae8d617914fcd05cfd21d8484154b1411a65` 的 CI run `39128676851` 中 `data-contract` 两次均约 40 分钟触限取消；隔离数据库执行原脚本全通过（133+3 tests、Ruff、mypy 213 files、契约摘要），M1/M6 和链接检查通过，详细结果及限制见[4.1 验收记录](docs/60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)。4.2 已完成 14 视图图表/数据盘点，识别合成账龄/预算可用而未展示、订单数小数数据语义问题和不能宣称的预测/风险/合并能力；报告见[4.2盘点](docs/60_delivery/verification/2026-10-18--cfo-chart-and-data-availability-v1.md)。4.3 已完成并形成[组件复用与交互方案](docs/60_delivery/verification/2026-10-18--cfo-chart-component-and-interaction-design-v1.md)：继续复用 ECharts 6.1，接通已有但未被分发器使用的构建器；修复图表语义并配同值表格、事实来源标签和深链。第 4 阶段 4.1–4.7 已结案，代码 SHA `65a08706` 与最终文档 SHA `a1fe50ef` 对应 GitHub CI 均 18/18 成功。截图采集/自动生成继续暂停。审计包含 19 个页面路由、32 个 PostgreSQL revisions、SQLite 方言与金额精度风险、S3/Redis/Celery 调用点及主 checkout 四处未提交更改；README 视觉同步完成。主 checkout 的四处改动仍原位，本 worktree 未触碰。当前分支为 `codex/single-machine-runtime-convergence`，原未提交实现仍保存在 stash 备份中。范围见[唯一工作包](docs/50_plans/work_items/FLOW--single-machine-visual-prototype.md)、[设计规格](docs/superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)和[路线图](docs/50_plans/CURRENT_ROADMAP.md)。

此前全视图驾驶舱工作包作为回归基线归档：九页 25 个 ECharts 画布、桌面/手机 18 组视口验收、API/页面数据对账、来源深链与缺数态等本地证据保留。真实 CI 状态：`39042517573`（SHA `e6b68c8a`）和 `39041228479`（SHA `0b9b12f3`）均 cancelled；`39040652008`（SHA `b2ee0373`）和 `39038535194`（SHA `df5c338b`）均 failure；不能说旧全视图任务准确 SHA CI 已通过。阶段 2 准确 SHA `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` 的 run `39035163288` 为 18/18 成功。相关[旧工作包](docs/50_plans/work_items/COCKPIT--all-views-data-and-visual-completion.md)已 archived 且禁止继续执行；[浏览器验证报告](docs/60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)仅作为回归基线。

发现主 checkout `/Users/qiming/workspace/FLOW` 保留四处 2026-10-16 未提交驾驶舱修改：`cockpit.css`、`kpi-card.tsx`、`module-page.tsx`、`cockpit/modules.py`。本 worktree 没有覆盖或暂存它们；在最终集成前核实这些更改的归属和是否已被新实现取代。未搜索或连接常驻业务库。

**CFO 驾驶舱盈利分析与图表缺口补全已完成**。本分支新增盈利能力页面 `/cockpit/profitability`、只读 API 与冻结时杜邦指标载荷；提供净利率、ROE、总资产周转率、权益乘数、两期比较、勾稽提示、指标/报告/来源财报行深链。图表复用 ECharts；旧快照或缺少期初数据时明确显示 unavailable。前端 36 个测试文件/184 项通过、typecheck/build 通过；lint 零错误，有一条既有 TanStack Table 警告；后端隔离定向测试 12 项、Ruff、mypy 通过；隔离账套核验 19/19、可见性矩阵 162 项无失败、浏览器全旅程 16/16 通过，真实页面截图见[浏览器验收记录](docs/60_delivery/verification/2026-10-17--cockpit-profitability-browser-verification-v1.md)。CI 首轮发现重复 seed 会新增两份 Objective 快照；修复归一化行 UUID 不稳定性后，回归测试 10 项通过，准确 SHA `08aa4cd02247f995bc990d92c8f34f5a1829afa1` 的 GitHub CI run `38996089002` 为 18/18 job success。contracts、plan views、links 与 M1 通过。代码与修复提交分别为 `5817efcf`、`08aa4cd0`，均已推送。工作包/设计/计划见 [工作包](docs/50_plans/work_items/COCKPIT--visual-analysis-expansion.md)、[设计规格](docs/superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)、[实施计划](docs/superpowers/plans/2026-10-17-cockpit-visual-analysis-expansion.md)。独立审查发现的单位误标和来源行下钻缺口均已修复。

**当前唯一队列：14 项，已完成 8、实际执行中 0、队首待启动 1（K2 只读预检）、排队 3、暂停 1、外部材料受限 1。** 7a 已关闭，K2 已转为当前队首；执行前只读核验 ObsidianWiki 状态。K0/K1/K2 的已完成证据、dirty vault 保护与来源说明见[知识刷新工作包](docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md)。

用户四项裁决（2026-10-16）：
1. **L0 挂 CI（选项 C）**：非阻断 `l0-baseline` job（continue-on-error: true），失败仅作信号灯。
2. **盲评复评范围（选项 A）**：仅旧三样本（顺丰/腾讯/中通）。
3. **C 级维持 6 条件不变（选项 A）**：诚实标准，做不到如实 No-Go。
4. **ZTO 立即恢复（选项 C）**：`wip/zto-integration-20260929` 已解封合并。

---

## 二、已完成的内容

### 前序驾驶舱交付清单（2026-10-17，历史基线）

| 交付 | 提交 | 验证/状态 | 要点 |
|---|---|---|---|
| CFO 全视图页面、来源联动和完整浏览器验收 | `b2ee037375ff0949a1dec442bd3ac4feb6bb078d` | 本地通过；CI run `39040652008` 的 M6 因报告状态 `active` 失败，已在下一提交修正 | 九视图 25 个 canvas；桌面/手机 18 组通过；18 张截图；所有模块 series/waterfall/formula-card 与盈利明细逐项核对 API；截图报告见下方索引 |
| 验收报告状态修正 | `0b9b12f3e0138898ff719d2f1db378cd793b9d5f` | 已推送；CI run `39041228479` cancelled | verification 状态改为 `draft` 以满足 M6；本包被新工作包接替，准确 SHA 全 CI 未通过 |
| 独立复核 | — | 已完成，无 P1/P2 | 复核覆盖所有 module chart、waterfall steps、公式卡 DSO/DIO/DPO/CCC、盈利能力所有明细行 |

本地验收：`pnpm -r lint && pnpm -r typecheck` 通过（3 条既有 warning）；`pnpm --filter @flow/web build` 通过；相关 Vitest 10/10；目标 Playwright 18/18 路由×视口通过（在现有隔离服务上设置 `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3461`）；`make contracts-check`、文档 M1/M6、`git diff --check` 通过。浏览器报告及全部截图：[全视图浏览器核验报告](docs/60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)。

### 前序批次（2026-10-13 ~ 10-16）交付清单

| 交付 | 分支 | main 合并 | CI | 要点 |
|---|---|---|---|---|
| **Codex 分支合并** | codex/damai-logistics-data-audit | `3b5c82b8` | ✅ | 28+ 提交（驾驶舱批次 A + ECharts + F1/F2 + 来源审计 + 驾驶舱批次 A 门禁），60 文件 +5552 行 |
| **来源事实登记** | flow/source-registry-20261013 | `d9a99ece` | ✅ | 325 条 disclosed_fact + 页锚机械核验 + 7 项假设处置；13 项 pytest |
| **运营披露层重建** | 同上 | `e5d8d2c6` | ✅ | 分部序列/件量改用菜鸟披露值（FY2023 国际 1,519 百万件）；废弃收入推导件量 |
| **时间线迁移** | flow/timeline-migration-20261013 | `c824f55f` | 17/17 ✅ | FY2022/FY2023 真实财年；明细↔披露年度聚合零差异；IFRS 三表过发布门禁；ORG-LEDGER v2 |
| **F3** | flow/finmetric-f3-20261014 | `4951fcfb` | ✅ | capex 符号修复（FCF −37.3 亿）；18 项缺口族裁决测试 |
| **F4** | 同上 | `732d1dcd` | ✅ | 环比 prior_month 窗口 + MetricCard.mom 契约 |
| **批次 B** | 同上 | `5421f01a` | 17/17 ✅ | 安全规格 V1.1.1 + cfo 角色 + 行动项闭环 + 独立审查 |
| **C-2** | flow/cockpit-c2-20261014 | `07a07b7c` | 17/17 ✅ | 资产负债/营运资金模块页 |
| **C-3/C-4/C-5** | flow/cockpit-c3-20261014 | `95427ae4` | 17/17 ✅ | 费用/现金流/风险/合并四模块 |
| **批次 D** | flow/cockpit-d-20261015 | `14016297` | 17/17 ✅ | 问数入口嵌入 |
| **51 图验收** | flow/cockpit-acceptance-20261016 | `df6073a8` | 17/17 ✅ | 10 模块×51 图覆盖映射文档 + 全链门禁绿 |
| **U04 盲评复评** | flow/u04-blind-review-20261016 | `707733dd` | 17/17 ✅ | **199/199 全绿**（顺丰 137 + 腾讯 32 + 中通 30）；C 级条件 5 通过 |
| **ZTO 解封** | 同上 | `ad255d3d` | ✅ | 合并 `wip/zto-integration-20260929`（+18506 行） |
| **L0 挂 CI** | 同上 | `b5c58c59` | ✅ | `l0-baseline` CI job（非阻断）+ `l0_baseline_check.py` |
| **路线图 v5.52** | 同上 | `08dfdfae` | ✅ | U04 → completed；队列 12 项：完成 6 / 执行中 0 / 排队 4 / 暂停 1 / 外部受限 1 |

### 更早交付（已在 main，本轮验证不回退）

| 内容 | 要点 |
|---|---|
| 来源事实登记 `config/damai/source_facts_v1.yaml` | 325 条、四分型、页锚对 PDF 机械核验 |
| 来源基线审计 | `docs/60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md` |
| 驾驶舱批次 A（总览页） | `ae56e96f`/`b7dc4983`，CI 17/17 |
| ECharts 6.1.0 + 10 类构建器 | `d563b8dc` |
| FINMETRIC F1/F2 | 指标引擎类型扩展 + 字典对齐 |

---

## 三、待处理事项与限制

| 问题 | 影响 | 当前处置 |
|---|---|---|
| **旧驾驶舱全视图 CI 未通过** | `39042517573`、`39041228479` cancelled；`39040652008`、`39038535194` failure | 旧包已归档；不反复重跑旧 SHA。新范围最终以本工作包的准确 SHA 做完整 CI 验收 |
| **主 checkout 有 4 处未提交驾驶舱修改** | 4 个文件最后修改时间为 2026-10-16；改动内容与驾驶舱 UI/API 有交集 | 保持原位、不覆盖、不暂存；最终集成前对照新实现和 owner 信息，决定保留或确认已被取代 |
| **SQLite 兼容与迁移成本未验证** | 现有 32 个 PostgreSQL Alembic revisions 含 JSONB、UUID 与 Postgres SQL；存储接口被多个流程调用 | 首先在隔离库做 schema、Decimal、事务、导入、来源追溯、报告和备份恢复验证；通过前不移除现有实现 |
| **历史 CI 曾受长测超时取消** | README SHA `d51af7ad` 的 run `39087270646` cancelled；同代码 docs-only SHA `a331f03075c95f3b371b5a0ebd0fd91cac9dfeae` 的 run `39090417203` 为 success | 超时未复现；不增超时、不减覆盖、不改 CI 配置。以成功 run 为本阶段起始门禁证据，后续实现 SHA 仍各自核对准确 CI |
| **route_policy 测试本地失败** | `test_openapi_probe_matches_tsv_two_way` 在本地 main 也失败（CI 通过） | 本地环境项（缺 S3 环境变量时 `create_app` 设置校验失败）；带完整 env 跑即绿。不阻塞 |
| **C 级条件 2（独立 oracle 0/14）** | 14 份报告无完整独立 oracle | 用户裁决 3A：如实 No-Go，后续迭代补 |
| **C 级条件 4（泛化留出全败）** | 小米 0/25、阿里 0/15、yunda 0/20、jdl 0/25 | 用户裁决 2A：不扩大盲评范围；适配器开发列后续迭代 |
| **P5 capex 符号** | `cainiao_private` 段 capex 映射与 damai_syn 同型问题（披露负值应 abs:true） | 登记为公开矩阵治理事项，本轮不动 |
| **rnd_exp 官方依据** | 原文不可得 | 外部材料受限结案；穷尽搜索后重启条件已列 |

---

## 四、下一步计划

### 当前唯一任务：K2 ObsidianWiki 只读预检（7a 已关闭）

第 3 阶段已正式关闭：最终状态 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 CI run `39125304357` 18/18 success。阶段 4 子步 4.1 已按工作包 §4.1 完成静态核查并生成[覆盖矩阵](docs/60_delivery/verification/2026-10-18--cfo-reference-module-data-coverage-v1.md)：10 模块逐项登记路由/API、指标字典、来源类别、期间粒度、图表交互和缺失字段，并发现 `/` 与 `/cockpit` 的经营分析入口割裂。准确 SHA 的 CI `data-contract` 两次触及 40 分钟上限取消，其余 jobs 成功；隔离 Compose/数据库执行同一完整脚本后 133+3 测试、Ruff、mypy 213 文件、摘要检查均通过，M1/M6 与链接检查通过。详见[4.1 验收记录](docs/60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)。4.2 已产出[14 视图数据与图表可用性盘点](docs/60_delivery/verification/2026-10-18--cfo-chart-and-data-availability-v1.md)：大麦演示包账龄/预算等数据存在但页面未消费，公开年度与 synthetic 月度必须分层，订单数分配明细存在小数；无数据支持的 13 周现金预测、风险矩阵和合并抵销继续视为受限。4.3 已完成并通过 M1/M6，组件与逐页方案见[设计记录](docs/60_delivery/verification/2026-10-18--cfo-chart-component-and-interaction-design-v1.md)。4.4 已结案，验收记录见[报告](docs/60_delivery/verification/2026-10-18--cfo-module-chart-adapter-acceptance-v1.md)。已接通单期分类柱图至排名横条 builder，把两期资产结构从 treemap 改为并列柱图，修复标量系列值表缺少当前期间列的问题，并将图表指标代码链接至指标库定义。前端全量单测 189/189、typecheck、生产 build 通过，API cockpit route 9/9 通过；M1 通过。一处旧 cockpit 测试 fixture 已补齐 `objective.v3` 快照结构；cockpit 领域/API 测试合计 14/14 通过。准确 SHA `31f84fec8e2a37349dd85d1ff1a230d2dd8364b8` 的 GitHub run `39137734822` 当时仍运行，未宣称全绿。严守公开/演示隔离，不新增依赖。4.5 已完成：`data/enterprise/damai-logistics/v2` 已由正式生成器从 `fixtures/damai` 重建；verify 新增源 manifest 指纹与五类业务目录逐文件一致性校验。31 个文件通过发行验证，经营实际 1,920 行与源文件逐字节一致，订单/件量均无小数语义异常；发行包及演示清单测试 14 项通过、Ruff 通过、重复构建的全目录摘要一致。证据见[验收记录](docs/60_delivery/verification/2026-10-18--cfo-enterprise-package-lineage-and-integer-counts-v1.md)。未连接或写入任何数据库。账龄与预算可用的是明确标注的合成演示事实，公开月度数据仍缺失；13 周现金预测/风险矩阵/合并抵销继续受数据限制，不把文章摘要或演示数字写成公开事实。4.6 指标展示修复及 4.7 浏览器验收均已完成：真实数据 9 页和 165 项浏览器回归通过；验收见[4.6记录](docs/60_delivery/verification/2026-10-18--cfo-metric-display-and-traceability-v1.md)和[4.7记录](docs/60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)。独立审查无 P1/P2。代码 SHA `65a087063ad67702172430702590083f8991a884` 的 CI run `39139310634` 与最终文档 SHA `a1fe50ef4e71298767b4fe8e22ab47d780f28552` 的 run `39140563811` 均为 18/18 success，7a 正式关闭。最新验收见[浏览器记录](docs/60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)。当前只读检查 ObsidianWiki 分支、工作区变更、相关日志和既存 1,365 条 dirty 指纹；不得 pull 覆盖、清理、暂存、提交或写入 vault。K2 要求上海时间 14:30/15:00/15:30 的稳定快照，窗口未到则先完成只读预检并按计划等候；截图采集工作流继续暂停。本轮未使用独立 Agent，不将作者自查表述为独立复核。

### 后续队列项：知识刷新 K0–K6

工作包：`docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md`
规格：`docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md`
实施计划（archived，取方法/命令）：`docs/superpowers/plans/2026-09-18-static-knowledge-refresh-and-strategic-rebaseline-implementation-plan.md`

**K0–K6 步骤概要**（状态以路线图和工作包为准）：
1. **K0 已完成**：Davybase 运行清单实现、微信历史批次严格验收和证据归档已推送。
2. **K1 已完成**：只读 allowlist scanner 已扫描三个非微信范围；566 篇需人工 triage，可执行候选 0，证据见工作包。
3. **K2 队首待启动**：Obsidian Git 冻结（14:30 锁定、15:00 候选、15:30 复验）
4. **K3** 用 accepted manifest 重建来源 registry/baseline/diff
5. **K4** 全量路由 + HIGH 精读
6. **K5** 构建 candidate + seal
7. **K6/战略裁决** 原子激活 release（须用户裁决，Agent 不可代签）

### 驾驶舱参考增强（并入 D055 工作包第 4 阶段）

不建立第二份 cockpit To-do。实施轮到后按工作包完成模块覆盖映射、来源/粒度核查、图表选型、跨指标下钻和状态验收。已有杜邦页、数据中心不重复建设；预算、账龄、13 周预测、合并抵销及行业分位等缺少来源的数据要明确标为缺口。文章演示数字与未经原图核验的 AI 摘要不得进入事实层。README 截图采集工作流保持暂停，浏览器视口检查不生成新截图。

---

## 五、踩过的坑（重要——新会话必读）

### 多 worktree / cwd 漂移

1. **shell cwd 持久化跨命令**：上一条命令 `cd` 到了哪里，下一条命令就在哪里执行。**对策：每条 git 命令前自校验 `git branch --show-current`；多 worktree 场景用绝对路径 `git -C <path>`。**
2. **两个工作区同时操作导致文件版本错位**：worktree 里的文件和主工作区的文件是独立 checkout。曾在 worktree 里跑 `ruff check --fix` 但编辑了主工作区的文件（或反过来）。**对策：确定一个工作区作为本轮的唯一工作区，不混用。**
3. **分支误建到 worktree**：`git switch -c` 在 cwd 所在仓库执行，如果 cwd 在 worktree 里就建到 worktree 了。**对策：切分支前先 `pwd` 确认。**

### 测试与环境

4. **S3 环境变量**：`create_app()` 启动时校验 `s3_access_key`/`s3_secret_key` 等。本地跑测试必须设置：
   ```bash
   export DATABASE_URL='postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow_test'
   export REDIS_URL='redis://localhost:6379/0'
   export S3_ENDPOINT_URL='http://127.0.0.1:9000'
   export S3_BUCKET='flow' S3_ACCESS_KEY='flow' S3_SECRET_KEY='flow_dev_only'
   export FLOW_DEV_ACTOR_ID='flow-dev-bp'
   ```
5. **测试连常驻库事故已修**（`b60c51b`）：conftest 默认切 `flow_test`；但如果 Docker 不在线（`docker info` 失败），PostgreSQL 5432 拒连，需要先 `open -a Docker` + `make infra-up`。
6. **测试文件多轮字符串手术易留残留**：本次 C-3 的 `test_cockpit_modules.py` 经多轮 sed 后留下 `-> SimpleNamespace: -> SimpleNamespace:` 语法错误。**对策：复杂改动直接重写整个文件而非增量 patch。**
7. **CI ruff 与本地 ruff 版本可能不同**：本地 `uv run ruff check` 全绿但 CI 报 `E501`（行长度）。**对策：提交前在 `services/api/` 目录下跑 `uv run ruff check src tests migrations`（CI 的确切命令）。**

### 数据一致性

8. **canonical 月份常量**：`canonical.py` 曾本地复制月份常量导致批次窗口错位。已改为从 `profile.py` 唯一导入。**教训：月度合同只在 profile 定义一次，别处 import。**
9. **发行版工作簿语义指纹**：重刷发行版后 xlsx 的语义指纹会真实变化（数值变了），**不可**习惯性 `git checkout` 回退——只有 zip 容器噪音（时间戳）才该回退。
10. **毛利校准基准行**：行间相对结构按比例缩放后，尾差并入校准基准行。基准行选择错误会导致年度合计偏差——基准行必须在循环外确定（如最大毛利行），且在循环内 `continue` 跳过常规缩放。
11. **`_family_month_revenues` 尾差**：三业务族分摊后族之和可能偏差 0.0002——需在最大族吸收尾差保证月度目标精确闭合。

### 前端 / Next.js

12. **Server Component 不能传函数 prop 给 Client Component**：page.tsx（server）向 module-page.tsx（client）传 `fetcher` 函数会触发 Next.js SSR 错误。**对策：client 组件自己 import flowApi 取数，page 只传数据属性（moduleId/title）。**
13. **`const module = ...` 触发 `@next/next/no-assign-module-variable`**：ESLint 规则禁止赋值给变量名 `module`。**对策：改名为 `data` 或 `mod`。**
14. **`"use client"` 页面不能导出 `metadata`**：Next.js 要求 metadata 只在 Server Component 导出。**对策：page.tsx 保持 server component，client 逻辑放独立组件文件。**
15. **ECharts 是独立依赖**：worktree 的 node_modules 可能缺 echarts（早期 lockfile 未含）。**对策：worktree 里先 `pnpm install --frozen-lockfile`。**

### CI / 构建

16. **CI ruff 版本 / 规则集与本地可能不同**：本地全绿但 CI 报错。**对策：提交前跑 CI 的确切命令：`cd services/api && uv run ruff check src tests migrations && uv run mypy src`。**
17. **新增 CI job 必须同步 `test_ci_gate_inventory.py`**：`EXPECTED_GATES` 集合和 `test_every_ci_gate_has_an_explicit_timeout`（timeout-minutes 必填）都要更新。
18. **CI 失败时先拉日志定位根因再修**：`gh api repos/davyzhong/FLOW/actions/jobs/<jobId>/logs --allow-escape-sequences | grep -a 'error\|FAILED'`。不要凭 job 名猜测。
23. **FLOW verification 文档状态受 M6 校验**：合法状态为 `draft`、`verified`、`superseded`、`archived`；`active` 会让 M6 失败。CI 最终结案前用 `draft`，全验收通过后才改 `verified`。
24. **契约升级要同步更新强类型 fixture**：`CockpitModuleChart` 新增必填字段后，组件测试 fixture 若未同步会导致 `pnpm -r typecheck`、Next production build、依赖该构建的 smoke 全失败；本轮补上 `analysis_question`、`fact_classes`、`snapshot_id` 等字段后 static-web/smoke/module-boundaries E2E 通过。
25. **Playwright 默认地址不是当前隔离浏览器端口**：项目配置默认 `127.0.0.1:13100`；本轮现成隔离服务的 Web 在 `3461`。复跑目标全视图用例需显式 `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3461`，先核实端口对应当前 worktree 和隔离账套，不能退回常驻数据库。

### Git / 文档

19. **`git push -q` 静默失败**：如果远端有新提交（如截图 bot），push 会 rejected 但 `-q` 吞掉输出。**对策：push 后 `git fetch && git rev-parse origin/<branch>` 确认远端 SHA 与本地一致。**
20. **docs/ 新增 .md 必须 unique doc_id**：复制文件改内容但忘改 `doc_id` 会触发 m1 重复检查。
21. **worktree 的 `node_modules` 可能过时**：worktree 共享代码但不共享 `node_modules`。在 worktree 里跑前端测试前先 `pnpm install --frozen-lockfile`。
22. **管道 `| tail -N` 会吃掉前置命令的退出码**：`cmd | tail` 永远返回 tail 的退出码（0）。**对策：需要检查退出码时不用管道，或用 `set -o pipefail`。**

---

## 六、关键命令速查

```bash
# 环境启动
open -a Docker && make infra-up

# 后端测试（必须从 repo 根或 services/api 运行）
cd services/api
export DATABASE_URL='postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow_test'
export REDIS_URL='redis://localhost:6379/0'
export S3_ENDPOINT_URL='http://127.0.0.1:9000' S3_BUCKET='flow'
export S3_ACCESS_KEY='flow' S3_SECRET_KEY='flow_dev_only'
export FLOW_DEV_ACTOR_ID='flow-dev-bp'
uv run pytest -q tests/ --ignore=tests/e2e

# 静态检查（CI 确切命令）
uv run ruff check src tests migrations && uv run mypy src

# 前端
cd apps/web && pnpm typecheck && pnpm test && pnpm lint && pnpm build

# 契约再生
cd /Users/qiming/workspace/FLOW && make contracts && make contracts-check

# 文档门禁
python3 scripts/check_docs.py --phase m1

# 计划视图再生（路线图改动后必须跑）
python3 -c "
import sys; sys.path.insert(0, '.')
from scripts.documentation.plan_views import write_views, check
from pathlib import Path
write_views(Path('.'))
print(check(Path('.')) or 'OK')
"

# 发行版重建
uv run --project services/api python scripts/build_damai_demo.py --output fixtures/damai
uv run --project services/api python scripts/build_enterprise_data_package.py build
uv run --project services/api python scripts/build_enterprise_data_package.py verify

# 来源登记重建
uv run --project services/api python scripts/build_damai_source_registry.py
uv run --project services/api python scripts/build_damai_source_registry.py --check

# 盲评复跑
FLOW_HOLDOUT_RUN_ID=<run-id> uv run --project services/api python scripts/holdout_u4_run.py

# e2e
bash scripts/test_damai_demo_e2e.sh
```

---

## 七、权威文件索引

| 文件 | 作用 |
|---|---|
| `docs/50_plans/CURRENT_ROADMAP.md` | **唯一主线**（状态 + 队列） |
| `docs/00_start_here/PROJECT_STATE.md` | 唯一 current state |
| `docs/50_plans/work_items/COCKPIT--cfo-dashboard-implementation.md` | 驾驶舱工作包（completed） |
| `docs/50_plans/work_items/FINMETRIC--financial-metric-catalog.md` | 指标目录工作包（completed） |
| `docs/50_plans/work_items/U04--independent-oracle.md` | U04 工作包（completed） |
| `docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md` | 知识刷新工作包（K0/K1 完成，K2 队首待启动） |
| `docs/60_delivery/verification/2026-10-16--u04-blind-review-rerun-v1.md` | 盲评复评验证文档 |
| `docs/60_delivery/verification/2026-10-16--cockpit-51-chart-coverage-mapping-v1.md` | 51 图覆盖映射 |
| `docs/60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md` | 来源基线审计 |
| `config/damai/source_facts_v1.yaml` | 来源事实登记（325 条） |
| `config/metrics/damai_demo_metric_coverage_v1.yaml` | 指标覆盖矩阵（32/50×2） |
| `config/statements/item_alias_map_v1.yaml` | 报表行名别名映射（damai_syn 段） |
| `services/api/src/flow_api/cockpit/modules.py` | 模块构建器（8 个 build_* 函数） |
| `services/api/src/flow_api/cockpit/service.py` | 投影服务（KPI/趋势/结论/行动项） |
