---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目交接文档
doc_type: navigation
status: current
version: 17.12
created_at: 2026-09-12
updated_at: 2026-10-28
owner: FLOW
applies_to: repository
---

# FLOW 项目交接文档

> 本文档是下一位 Agent 接手的唯一入口。项目唯一权威状态以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准；本文档提供接手上下文、踩坑记录和下一步操作指引。

---

## 一、当前任务

**2026-10-27 分支合并与环境清理（用户指令「干净清爽的环境」）：** 全部活动分支已合并进 main 并删除，**远端现仅剩 `main` 一个分支**。合并序列：① `flow/roadmap-cleanup-20261027`（含 PR #5 视觉语言/K3 批次 129–133 + 路线图规整 v17.17 + publishing-golden 修复 `775f283a`）合入 main（merge `5d2b77f6`）；② PR #6 `codex/metric-system-reference-20261025` union 合入（merge `b70de445`：保留 main 最新状态 + METRIC_SYSTEM_GOALS/20 图核读报告/产品文档增量，「指标体系资料增量」节归档进路线图历史 details）。**publishing-golden CI 失败已修复**（`775f283a`）：`test_visual_export_theme` 硬编码 macOS 字体名而生成器按 `platform.system()` 选择字体，断言改为跟随 `_primary_font()`；本地 5/5 通过，Linux CI 将走 Noto 路径。合并后 main 准确基线 `b70de445`；PR #5 自动标记 MERGED，PR #6 因先删分支记为 CLOSED、已留评论说明内容经 `b70de445` 合入。已删远端分支：`codex/flow-visual-language`、`codex/metric-system-reference-20261025`、`flow/roadmap-cleanup-20261027`、`wip/zto-integration-20260929`（内容早已全在 main）。本地删除 17 个已合并分支并移除 6 个干净 worktree；**保留 3 项**：`.worktrees/readme-visual-main`（11 个 staged 的 10-18 D055 文档暂存，内容均已有 main 更新版，可安全清理但留待用户确认）、`.worktrees/cockpit-visual-completion`（含用户要求保留的 `services/api/flow.sqlite3` 未跟踪文件）、`codex/frontend-consistency-remediation` 本地分支（9-18 的 wip 保存，未全在 main）。主 checkout 仍在 `flow/u04-closeout-20261016`（已全在 main），其 4 个未提交驾驶舱文件保持原样；切回 main 由用户决定。队列状态不变：下一单一动作 = **K3 第 134 批**。

**2026-10-27 路线图结构性规整（v17.17）：** 用户要求对任务/目标/待验证清单做删减规整。路线图已重组为四层结构——**战略目标（G1 单机原型已交付 / G2 知识刷新 K3 进行中 / G3 公开 C 级 No-Go 维持 / G4 内部工作台 gated）→ 唯一执行队列（16 项编号不变）→ 工作包登记表（21 包每包一行）→ 待验证清单（活跃仅 4 项，其余显式关闭）**；原 60 行裸历史段落、7a 收尾执行卡和历史队列全部折进 `<details>` 只读归档，内容未删减；纪律节两条 2026-09-26 过时补记并入正文。规整不改变任何队列状态或下一动作（仍为 K3 第 134 批），plan_views PASS。

**2026-10-27 当前交接：** 路线图共 16 项：完成 10、实际执行中 0、队首待启动 1（K 轨 K3）、排队 3、暂停 1、外部条件受限 1。视觉语言包及全项目视觉统一已结案，准确证据见[覆盖报告](docs/60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)：隔离 manifest `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed` 下验证器 19/19、可见性矩阵 164/164（154 HTTP 200、10 预期拒绝、0 失败）、Playwright 17/17；应用 SHA `01e8e25dd426ed43ad6a2cad76544bbbe623eb99` 的 20×3 矩阵 60/60、Axe 桌面 20 路由零违规。E2E 断言修正 `d01daa11` 独立复核无 P1/P2。原生浏览器 200% 缩放因 Mac 锁屏及工具能力限制未直接验收，待设备解锁且有可操作原生缩放工具时补验；390/360 CSS px 不是替代。当前分支 `codex/flow-visual-language`，PR #5。K3 最新 accepted snapshot 为 `obsidianwiki-20261026T005516+0800-d601b4d5`（Davybase commit `110fe57`，manifest SHA `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`）；完整内容 SHA 与先前 K3 baseline 输入一致，写句柄 0。registry/baseline/delta 已重新绑定最新 snapshot ID 并重复生成一致，批次001–025登记的76条HIGH来源及后续HIGH全文审阅、W1/W3 MED/LOW双审和错误集中度复核均已完成。**K3 已挂起（用户裁决 2026-10-28）：** 批次 134–162 共 29 批 2,928 条审阅完毕并推送（routed 1,200 / filtered 660 / pending 7,813 挂起）；`CURRENT_RELEASE` 不变，ObsidianWiki 只读未动。恢复条件：用户重新指令或按缩减策略重启；恢复点=第 163 批（`SRC-LOCAL-v1-40251d629ebbd4f57558` 之后）。用户已确认新队首 = **真实数据导入**（工作包 FLOW-WI-REAL-DATA-IMPORT-20261028-001，分支 flow/real-data-import-20261028）：R1 模板与校验引擎（科目余额表/利润表 Excel 模板+Decimal 平衡校验+逐行错误报告）→ R2 导入 API 与账套装载（按 dataset_id 与演示数据隔离）→ R3 导入向导 UI（/data/import + 导航 + e2e）→ R4 端到端验收，**R1–R4 已全部交付**（main `4f633a24` CI run 40627155163 全绿）+ 追加派生指标端点（d4c03829）。**R5 已交付（本地全绿）：** 九页接线实现=CanonicalPackage 桥接→load_canonical_package 直写→勾稽 ReconciliationResult→IntakeService 发布门禁→trial_balance_v1 逐期间快照→AnalysisRun，九页经 get_latest 自动切换；实施修正两处（canonical record_id 需 UUID→uuid5 确定性生成；playbook 输入 source_record_count gt=0→ge=0 + DSO 零分母守卫，空经营行走既有 degraded 分支）；flow_v1 指纹经 stash 对比确认不变（4214ae85339e）；集成测试 4/4（进 CI core 分片）+ 回归 106 项 + 六门禁 PASS。**工作包已关闭（2026-10-28）：准确 SHA `a2510344` CI run `40651999130` 全绿**（contracts 两连挂根因=d4c03829 加 metrics 端点未再生成契约，本轮修复）。**用户已裁决新队首 = 导入账套指标补厚**（FLOW-WI-IMPORTER-RICH-METRICS-20261028-001：M1 科目级映射→M2 利润表接线→M3 银行流水接线，串行）。**M1–M3 已全部交付**（M1 `082f2f94` 科目级映射/结构指标、M2 `f6a52467` 利润表接线/毛利率/净利润勾稽门禁、M3 `715a2d6d` 银行流水/现金口径指标/余额连续性门禁）；导入链指标 7→22。实施关键修正：空映射组不写 0 金额事实（缺席≠零，0 会让环比 0/0 硬崩）。**准确 SHA CI 已核验全绿**（`90dce69e` run `40665135693`；`715a2d6d` 的 run 被同分支并发取消，由其后继同码提交核验）。**下一单一动作 = 队首裁决（下一产品方向，待用户拍板）。**红线全部兑现：未改 dashboard service；损益明细只来自利润表（不双源）；现金口径未绑 operating_cash_flow。红线兑现：未改 dashboard service；未重复造业务事实源。五个locator-only例外为 `SRC-LOCAL-v1-00625bae4e08042539d1`、`SRC-LOCAL-v1-0428a240b0361157ffa1`、`SRC-LOCAL-v1-057cabfb9baca9f47c44`、`SRC-LOCAL-v1-0bd79ce2c2d600301852`、`SRC-LOCAL-v1-0de553da4d8d857b90d3`；不使用范围外正文或链接标题推断替代。旧 10-19 结果是历史截面。ObsidianWiki 严格只读，`CURRENT_RELEASE` 不变。用户选择保留 `/Users/qiming/.flow/flow.sqlite3` 零字节文件；其他未跟踪数据库文件保持原样。

**2026-10-25 指标资料学习补记（独立文档分支）：** 已直接核读“数研复盘狮”《经营驾驶舱分析指标库》20 张原图，完成来源指纹/逐图采用映射与现有指标库查重；补入 [METRIC_SYSTEM_GOALS](docs/20_product/METRIC_SYSTEM_GOALS.md)、愿景/范围和路线图既有事项 7 的来源评审/影响范围。本轮不改运行公式/数据/阈值/数据库或 CURRENT_RELEASE，也不写视觉任务活动工作树；视觉事项 12 继续由原任务执行，队列数量不变。后续应从本路线图资料增量进入既有来源与产品影响评审，再安排代码切片；不能从文章截图直接发布公式或通用阈值。图片抽取进程的完成状态未被本次独立核读替代，Obsidian/原图未修改。本分支文档已通过独立新上下文复核（无必要 P1/P2）和 M1/M6、计划视图、链接/差异检查，集成时保留视觉分支更新后的当前状态，不把本文快照覆盖为新状态。完整依据见[二十图核读报告](docs/60_delivery/verification/2026-10-25--business-metric-library-reference-review-v1.md)。


### 2026-10-27 会话结束交接

**当前任务与状态。** 唯一主线仍是 K3 全量逐条语义路由与 coverage 闭合，权威队列以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准。本会话结束时没有正在运行的审阅或验证进程；第133批已提交推送，下一单一动作是第134批。路线图总计16项：完成10、实际执行中0、K3队首待启动1、后续排队3、暂停1、外部条件受限1。当前分支为 `codex/flow-visual-language`，PR #5；2026-10-27 开工前 `git pull --ff-only origin codex/flow-visual-language` 已确认远端无新提交，工作区干净，HEAD `75ae401c03013009306cd1640a6dd8f472b66ba7`。

**已完成。** 2026-10-26 连续完成第129–133批，共120条 accepted 来源的逐 ID 审阅与文件/规范化正文 SHA 核对：新增 routed 62、filtered 58；全量9,673条目前为 routed 755、filtered 412、pending_review 8,506。每批均更新来源基线、coverage、change manifest、批次审阅表、路线图、项目状态、来源 README、工作包、知识库 inventory/SHA 清单和本交接；M1、M6、coverage validator、链接、KB manifest 与 diff 检查通过，独立只读复核均无剩余 P1/P2。五批提交依次为 `45e0357e`、`46e3b774`、`9c667d6c`、`f436ec0a`、`75ae401c`，均已推送 GitHub。视觉语言包与全项目页面、图表、报告及 README 的视觉统一此前已结案，证据见上方当前交接段及[覆盖报告](docs/60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。

**限制与未满足验收。** K3 尚有8,506条待审，五个 locator-only 例外缺可用 accepted 正文，不能按标题或范围外文件补全；后续还需 coverage 终态闭合、知识综合和独立 reader，`CURRENT_RELEASE` 尚未 seal/激活。部分来源的图片引用按基线解析规则未解析，不能推断附件不存在：第132批的34个同名附件实际位于 accepted vault tree 其他路径；关联的27张截图在当前 accepted 工作区但未进入 Git tree；第133批有28个本地引用未按规则解析及18个未归档外链图像。这些批次只根据已读文字路由，未审图，付费 Word/Excel 模板未取得。原生浏览器200%缩放的外部条件受限项仍按既有视觉验收结案记录保留，不能将 CSS 窄屏测试说成原生缩放通过。前一轮连续执行因系统用量限制停止；这不是来源审阅本身的技术阻塞，也不构成 K3 完成。

**下一单一动作。** 下一会话先核验仓库/分支及可见在途工作，拉取 GitHub 最新提交；从 accepted baseline 中第133批末尾 `SRC-LOCAL-v1-25f831bfad9d00b1f553` 之后的首个未审 source_id 开始第134批，继续逐条读 accepted 正文、复算 file/body SHA、核对图片实际位置与敏感边界。完成一批后同步唯一路线图及交接，通过文档门禁、独立复核、提交并立即推送，再开始下一批；不得跳过 K3 去做排队项。五个 locator-only 例外保留 pending_review，直到取得同一 accepted 范围内的可验证正文或按工作包给出有依据处置。

**踩坑与恢复要点。** ① `source_baseline.py` 的图片解析只查源文件目录和 vault 根目录，按该规则未解析不等于快照缺图；须区分 Git tree、accepted 工作区、外链未归档和本批未审图四种情况。② ObsidianWiki accepted snapshot 是 working-tree 快照，个别来源或附件不在 Git tree；以登记的文件 SHA 核对当前只读工作区，不能仅用 `git show HEAD` 取证。③ 自动生成摘要、AI图注、二次人工摘述和付费模板各有不同证据层级，不能冒充原件或将来源数值写成产品事实。④ 企业内部架构、运营指标和规划资料只登记过滤理由，不在 FLOW 审阅表复述细节。⑤ 每次提交后立即推送；M1/M6 通过只代表该次提交前的本地门禁，报告远端 CI 时须核其准确提交 SHA。主 checkout 的用户改动及 `/Users/qiming/.flow/flow.sqlite3` 零字节文件均保持原样。


**历史操作记录（2026-10-26视觉结案时点；当前K3状态以上方交接段落为准）：** 最终隔离验收为 19/19、164/164、17/17；独立代码复核无 P1/P2。最后 E2E 断言修复已提交 `d01daa11` 并推送。视觉工作包正式结案，队首转到 K3；当时第一步为只读复核 accepted manifest 与 vault 状态，不触碰常驻知识库。

<details>
<summary>2026-10-21 及以前的状态快照（历史，不代表当前执行）</summary>

**当前执行项：7a 全视图视觉收敛、门禁分片与项目文档治理。** 已完成总览与主题页报告层级、移动导航、数据工作台报告式布局；本轮修补 390px 费用页五项 KPI 三列挤压，改为两列，并将驾驶舱费用结构图升级为已披露两年的堆叠对比及双期原值表，显式说明不含营业成本。前端 199/199、typecheck/生产 build 通过；lint 零错误、3 条既有 warning。费用页 KPI 修复 SHA `87e1829d32d6281fe1dad7ee978f39e0c1b4e5f2` 对应准确 SHA CI run `39451521454` 已因后续提交取消；堆叠费用图提交 SHA `65d7dc61d18e0ebe2f2bc582c3f99e4bbe3e4d5d` 的 run `39453419044` 因后续文档提交取消，汇总失败由分片取消导致、非断言失败；状态提交 `a71cb28eedc6bca8019e7552fe7b2348f28f1239` 的准确 SHA run `39453752316` 已 28/28 jobs success；最新文档 SHA `21b650a108e7d906338454d661b7cfe178e13487` / run `39457446117` 也已 28/28 success。上一文档 SHA `4073d511` / run `39447663998` 28/28 jobs success。六个主题模块 390px 实测 ready、有图表且无横向溢出；费用 KPI 栅格回归通过。SQLite + 本地文件、同步处理和一键启动保持不变；本轮没有新增依赖/服务或数据库改动。运行架构文档已校准备份恢复验收状态和 SQLite JSON / PostgreSQL JSONB 差异。继续完成文档现状与清理候选审计、最终复核和新 SHA CI；任何文件删除仍需逐项授权。验收顺序见[7a 工作包第 9 节](docs/50_plans/work_items/FLOW--single-machine-visual-prototype.md#9-概念图视觉差距门禁负载与文档治理)，唯一队列见[CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md)。

</details>

<details>
<summary>2026-10-20 main 接手核验快照（历史）</summary>

- 当时 main HEAD `5ed61af91ea4c1c2a2078fd654accf671ba805ba` 对应 CI run `39119888132`，18/18 jobs success；该结果仅代表当时 SHA。
- 当时唯一队列为 14 项：完成 7、执行中 0、队首待启动 1、排队 4、暂停 1、外部材料受限 1；队首是 D055 单机原型架构简化与全视图视觉升级。
- 当时主 checkout 有 4 个修改文件及 1 个未跟踪 YAML，均未触碰；该历史快照不替代本文顶部的 2026-10-24 当前状态。

</details>

### 本会话交接补记（2026-10-20）

- 用户要求合入整个视觉分支；PR [#2](https://github.com/davyzhong/FLOW/pull/2) 已合并至 GitHub `main`，merge commit `5ed61af91ea4c1c2a2078fd654accf671ba805ba`，feature head 为 `27d8f566d7d130f67fa19ad2f745632f07b5d34c`。合并范围包括已提交的 SQLite/架构实现、README 视觉更新及相关文档；未提交改动未纳入。
- 该 feature head 的 CI 为 17/18 jobs 成功；`intake-e2e` 达到 GitHub 45 分钟上限并被取消。取消前日志显示 intake 测试 41+2+11+133 项、Ruff/mypy 与迁移往返检查通过，但后续步骤没有跑完。因此不得将这次 CI 描述为全绿；用户已明确选择按现有通过日志合并。此为历史合并验收限制，不替代 7a 当前工作所需的准确 SHA 完整验证。
- 接手时优先按本节“当前任务”和[唯一队列](docs/50_plans/CURRENT_ROADMAP.md)续做；本次合并已完成，不要重复合并 PR #2。主 checkout `/Users/qiming/workspace/FLOW` 有未提交用户改动，必须保留原样。

下方为 K2 执行前形成的架构工作包摘要，当前状态以本段和 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准。

**历史统计已由 2026-10-24 更正：14 个唯一事项，完成 7、执行中 0、队首待启动 1、排队 4、暂停 1、外部条件受限 1。逐项状态只以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为准。**

**历史交接快照（K2 阶段）：以下为阶段 5 重开前的上下文记录，当前执行项和队列以本文件首段及 CURRENT_ROADMAP 为准；本段不得作为当前状态读取。** 用户已选择单机单用户、SQLite 单文件 + 本地文件目录、移除 Redis/Celery/MinIO，并批准 A「高管编辑部」+ C「财务报告画布」。第 1–3 阶段完成；第 3 阶段最终状态 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 CI run `39125304357` 18/18 jobs success。首轮 CI 曾发现大麦 reset SQL 的发行包 manifest 哈希未同步；在 `4c3e87e05ae9fe380abb7002ba260de6d654d15c` 只更新对应清单，未改业务数据；脚本 155/155、清单专项 6/6、Ruff/mypy 和 M1/M6 均通过。正式验收见[阶段 3 记录](docs/60_delivery/verification/2026-10-18--single-machine-runtime-convergence-v1.md)。参考文章 10 模块的映射报告已写入[覆盖矩阵](docs/60_delivery/verification/2026-10-18--cfo-reference-module-data-coverage-v1.md)，覆盖页面/API/指标/事实类型/粒度/图表与交互缺口。准确 SHA `d8f2ae8d617914fcd05cfd21d8484154b1411a65` 的 CI run `39128676851` 中 `data-contract` 两次均约 40 分钟触限取消；隔离数据库执行原脚本全通过（133+3 tests、Ruff、mypy 213 files、契约摘要），M1/M6 和链接检查通过，详细结果及限制见[4.1 验收记录](docs/60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)。4.2 已完成 14 视图图表/数据盘点，识别合成账龄/预算可用而未展示、订单数小数数据语义问题和不能宣称的预测/风险/合并能力；报告见[4.2盘点](docs/60_delivery/verification/2026-10-18--cfo-chart-and-data-availability-v1.md)。4.3 已完成并形成[组件复用与交互方案](docs/60_delivery/verification/2026-10-18--cfo-chart-component-and-interaction-design-v1.md)：继续复用 ECharts 6.1，接通已有但未被分发器使用的构建器；修复图表语义并配同值表格、事实来源标签和深链。第 4 阶段 4.1–4.7 已结案，代码 SHA `65a08706` 与最终文档 SHA `a1fe50ef` 对应 GitHub CI 均 18/18 成功。截图采集/自动生成继续暂停。审计包含 19 个页面路由、32 个 PostgreSQL revisions、SQLite 方言与金额精度风险、S3/Redis/Celery 调用点及主 checkout 四处未提交更改；README 视觉同步完成。主 checkout 的四处改动仍原位，本 worktree 未触碰。当前分支为 `codex/single-machine-runtime-convergence`，原未提交实现仍保存在 stash 备份中。范围见[唯一工作包](docs/50_plans/work_items/FLOW--single-machine-visual-prototype.md)、[设计规格](docs/superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)和[路线图](docs/50_plans/CURRENT_ROADMAP.md)。

此前全视图驾驶舱工作包作为回归基线归档：九页 25 个 ECharts 画布、桌面/手机 18 组视口验收、API/页面数据对账、来源深链与缺数态等本地证据保留。真实 CI 状态：`39042517573`（SHA `e6b68c8a`）和 `39041228479`（SHA `0b9b12f3`）均 cancelled；`39040652008`（SHA `b2ee0373`）和 `39038535194`（SHA `df5c338b`）均 failure；不能说旧全视图任务准确 SHA CI 已通过。阶段 2 准确 SHA `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` 的 run `39035163288` 为 18/18 成功。相关[旧工作包](docs/50_plans/work_items/COCKPIT--all-views-data-and-visual-completion.md)已 archived 且禁止继续执行；[浏览器验证报告](docs/60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)仅作为回归基线。

发现主 checkout `/Users/qiming/workspace/FLOW` 保留四处 2026-10-16 未提交驾驶舱修改：`cockpit.css`、`kpi-card.tsx`、`module-page.tsx`、`cockpit/modules.py`。本 worktree 没有覆盖或暂存它们；在最终集成前核实这些更改的归属和是否已被新实现取代。未搜索或连接常驻业务库。

**CFO 驾驶舱盈利分析与图表缺口补全已完成**。本分支新增盈利能力页面 `/cockpit/profitability`、只读 API 与冻结时杜邦指标载荷；提供净利率、ROE、总资产周转率、权益乘数、两期比较、勾稽提示、指标/报告/来源财报行深链。图表复用 ECharts；旧快照或缺少期初数据时明确显示 unavailable。前端 36 个测试文件/184 项通过、typecheck/build 通过；lint 零错误，有一条既有 TanStack Table 警告；后端隔离定向测试 12 项、Ruff、mypy 通过；隔离账套核验 19/19、可见性矩阵 162 项无失败、浏览器全旅程 16/16 通过，真实页面截图见[浏览器验收记录](docs/60_delivery/verification/2026-10-17--cockpit-profitability-browser-verification-v1.md)。CI 首轮发现重复 seed 会新增两份 Objective 快照；修复归一化行 UUID 不稳定性后，回归测试 10 项通过，准确 SHA `08aa4cd02247f995bc990d92c8f34f5a1829afa1` 的 GitHub CI run `38996089002` 为 18/18 job success。contracts、plan views、links 与 M1 通过。代码与修复提交分别为 `5817efcf`、`08aa4cd0`，均已推送。工作包/设计/计划见 [工作包](docs/50_plans/work_items/COCKPIT--visual-analysis-expansion.md)、[设计规格](docs/superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)、[实施计划](docs/superpowers/plans/2026-10-17-cockpit-visual-analysis-expansion.md)。独立审查发现的单位误标和来源行下钻缺口均已修复。

前序交接快照（已由本页最新队列更新）：K2 冻结器曾受墙上时间和 clean-only 条件限制；详情见[知识刷新工作包](docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md)。

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
| **PR #2 的 intake-e2e job 触及 45 分钟上限** | feature SHA `27d8f566d7d130f67fa19ad2f745632f07b5d34c` 的 GitHub CI 为 17/18 jobs success，`intake-e2e` cancelled | 用户依据可见通过日志批准合并；测试子步骤日志通过，但 job 后续步骤未完整执行。记录为限制，不称全 CI 通过；7a 仍须验证自己的最终准确 SHA |
| **route_policy 测试本地失败** | `test_openapi_probe_matches_tsv_two_way` 在本地 main 也失败（CI 通过） | 本地环境项（缺 S3 环境变量时 `create_app` 设置校验失败）；带完整 env 跑即绿。不阻塞 |
| **C 级条件 2（独立 oracle 0/14）** | 14 份报告无完整独立 oracle | 用户裁决 3A：如实 No-Go，后续迭代补 |
| **C 级条件 4（泛化留出全败）** | 小米 0/25、阿里 0/15、yunda 0/20、jdl 0/25 | 用户裁决 2A：不扩大盲评范围；适配器开发列后续迭代 |
| **P5 capex 符号** | `cainiao_private` 段 capex 映射与 damai_syn 同型问题（披露负值应 abs:true） | 登记为公开矩阵治理事项，本轮不动 |
| **rnd_exp 官方依据** | 原文不可得 | 外部材料受限结案；穷尽搜索后重启条件已列 |

---

## 四、下一步计划

### 历史交接快照：K2 即时稳定工作区快照（已由当前状态段替代）

第 3 阶段已正式关闭：最终状态 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 CI run `39125304357` 18/18 success。阶段 4 子步 4.1 已按工作包 §4.1 完成静态核查并生成[覆盖矩阵](docs/60_delivery/verification/2026-10-18--cfo-reference-module-data-coverage-v1.md)：10 模块逐项登记路由/API、指标字典、来源类别、期间粒度、图表交互和缺失字段，并发现 `/` 与 `/cockpit` 的经营分析入口割裂。准确 SHA 的 CI `data-contract` 两次触及 40 分钟上限取消，其余 jobs 成功；隔离 Compose/数据库执行同一完整脚本后 133+3 测试、Ruff、mypy 213 文件、摘要检查均通过，M1/M6 与链接检查通过。详见[4.1 验收记录](docs/60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)。4.2 已产出[14 视图数据与图表可用性盘点](docs/60_delivery/verification/2026-10-18--cfo-chart-and-data-availability-v1.md)：大麦演示包账龄/预算等数据存在但页面未消费，公开年度与 synthetic 月度必须分层，订单数分配明细存在小数；无数据支持的 13 周现金预测、风险矩阵和合并抵销继续视为受限。4.3 已完成并通过 M1/M6，组件与逐页方案见[设计记录](docs/60_delivery/verification/2026-10-18--cfo-chart-component-and-interaction-design-v1.md)。4.4 已结案，验收记录见[报告](docs/60_delivery/verification/2026-10-18--cfo-module-chart-adapter-acceptance-v1.md)。已接通单期分类柱图至排名横条 builder，把两期资产结构从 treemap 改为并列柱图，修复标量系列值表缺少当前期间列的问题，并将图表指标代码链接至指标库定义。前端全量单测 189/189、typecheck、生产 build 通过，API cockpit route 9/9 通过；M1 通过。一处旧 cockpit 测试 fixture 已补齐 `objective.v3` 快照结构；cockpit 领域/API 测试合计 14/14 通过。准确 SHA `31f84fec8e2a37349dd85d1ff1a230d2dd8364b8` 的 GitHub run `39137734822` 当时仍运行，未宣称全绿。严守公开/演示隔离，不新增依赖。4.5 已完成：`data/enterprise/damai-logistics/v2` 已由正式生成器从 `fixtures/damai` 重建；verify 新增源 manifest 指纹与五类业务目录逐文件一致性校验。31 个文件通过发行验证，经营实际 1,920 行与源文件逐字节一致，订单/件量均无小数语义异常；发行包及演示清单测试 14 项通过、Ruff 通过、重复构建的全目录摘要一致。证据见[验收记录](docs/60_delivery/verification/2026-10-18--cfo-enterprise-package-lineage-and-integer-counts-v1.md)。未连接或写入任何数据库。账龄与预算可用的是明确标注的合成演示事实，公开月度数据仍缺失；13 周现金预测/风险矩阵/合并抵销继续受数据限制，不把文章摘要或演示数字写成公开事实。4.6 指标展示修复及 4.7 浏览器验收均已完成：真实数据 9 页和 165 项浏览器回归通过；验收见[4.6记录](docs/60_delivery/verification/2026-10-18--cfo-metric-display-and-traceability-v1.md)和[4.7记录](docs/60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)。独立审查无 P1/P2。代码 SHA `65a087063ad67702172430702590083f8991a884` 的 CI run `39139310634` 与最终文档 SHA `a1fe50ef4e71298767b4fe8e22ab47d780f28552` 的 run `39140563811` 均为 18/18 success，7a 正式关闭。最新验收见[浏览器记录](docs/60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)。只读预检已完成：ObsidianWiki main@`e04d6833`，HEAD tree `aa7d84d3`；1,377 条 dirty 路径（545 tracked、832 untracked、0 staged），K0 为 1,365 条。工作区指纹 `6b277aca…`；微信知识库范围 32,637 文件/3,952,541,809 字节，指纹 `afd7ccf2…`，与 K0 的 32,625 文件/`0a42346d…` 不同。冻结器发现 TimeMachine/系统服务候选 writer，未检出活动 Obsidian/Davybase pipeline。证据见[K2 预检记录](docs/60_delivery/verification/2026-10-19--k2-obsidian-readonly-preflight-v1.md)。不得 pull 覆盖、清理、暂存、提交或写入 vault。固定时间门禁已由 D056 和知识刷新设计 v1.2 取代；当前改造目标是随时启动、dirty 内容纳入指纹、双次完整指纹一致且无实际写句柄后接受。实现及 CI 通过后立即执行 K2；漂移时 rejected，vault 保持原样。截图采集工作流继续暂停。本轮未使用独立 Agent，不将作者自查表述为独立复核。

### 后续队列项：知识刷新 K0–K6

工作包：`docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md`
规格：`docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md`
旧实施计划（archived，仅历史参考；K2 时间门禁命令已被设计 v1.2 取代）：`docs/superpowers/plans/2026-09-18-static-knowledge-refresh-and-strategic-rebaseline-implementation-plan.md`

**K0–K6 步骤概要**（状态以路线图和工作包为准；下表是阶段划分，不是第二份待办）：
1. **K0 已完成**：Davybase 运行清单实现、微信历史批次严格验收和证据归档已推送。
2. **K1 已完成**：只读 allowlist scanner 已扫描三个非微信范围；566 篇需人工 triage，可执行候选 0，证据见工作包。
3. **K2 已完成**：即时稳定工作区快照，验收见知识刷新设计 v1.2。
4. **K3 当前执行**：registry/baseline/diff 已按 10-26 accepted manifest 重建；当前进行逐条语义路由与 HIGH 精读。
5. **K4** MED/LOW 双审抽样、错误集中度与 coverage 闭合
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
26. **CI 中测试日志通过不代表 job 完成**：PR #2 的 `intake-e2e` 日志中主要测试命令和迁移往返显示通过，但 job 因 45 分钟上限取消，后续步骤未执行。交接时同时记 job 总状态、准确 SHA 和未运行步骤，不把局部通过写成整项 CI 通过。

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
| `docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md` | 知识刷新工作包（K0/K1/K2 完成，当前执行 K3） |
| `docs/60_delivery/verification/2026-10-16--u04-blind-review-rerun-v1.md` | 盲评复评验证文档 |
| `docs/60_delivery/verification/2026-10-16--cockpit-51-chart-coverage-mapping-v1.md` | 51 图覆盖映射 |
| `docs/60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md` | 来源基线审计 |
| `config/damai/source_facts_v1.yaml` | 来源事实登记（325 条） |
| `config/metrics/damai_demo_metric_coverage_v1.yaml` | 指标覆盖矩阵（32/50×2） |
| `config/statements/item_alias_map_v1.yaml` | 报表行名别名映射（damai_syn 段） |
| `services/api/src/flow_api/cockpit/modules.py` | 模块构建器（8 个 build_* 函数） |
| `services/api/src/flow_api/cockpit/service.py` | 投影服务（KPI/趋势/结论/行动项） |


2026-10-26 K3 接续：语义审阅批次 001–025 共 76 条 HIGH 候选，62 篇本地正文已读、14 条仅元数据筛查；60 条 pending-verification，2 条同源副本 duplicate，14 条内部敏感来源 rejected 并排除产品候选，来源原文尚未独立核验。第二十三批将核算粒度、经营思维和降本增效文章作为待验证框架；第二十四批发现闭环案例笔记与已审文章内容高度相似但出处未核，保留待核；第二十五批将 3 条余下的内部业财规划/规则材料仅做元数据筛查并排除候选。旧 HIGH 清单中的 AI 财务专题经 Git 元数据追溯到 2026-09-26 去重提交：旧财务路径被删除，同一 Git blob 保留在系统架构路径；该路径不在当前 accepted baseline，故记为基线外迁移并排除本轮候选，不打开正文、不计入已审候选。第二十六至三十一批已双审 W1 MED 18/18 条（旧清单标17篇，末行合并两篇）；第二十九批发现盈利分析公式错误（毛利率量纲、有效税率、ROE拆解），以及酒店案例指标口径和无来源效果数字；禁止直接作为定义或事实。Power BI 操作/AI路线和AI财务观点均保留背景级，不采纳宣传性能力、时点价格或替代就业预测。第二十七批发现流程分类过于绝对、数据看板计数与总数不符（28,155 vs. 26,935，占比约 104.6%），均不作事实。京东分部列值较合计收入高 181.5 亿元，须核原始季报。coverage 台账 9,673 条中 routed 168、filtered 19、pending_review 9,486；W1 MED 已完成18/18（旧清单标17篇，末行合并两篇）；W3 MED有效范围完成；W3 LOW分层样本首批12/12完成（10待核、2敏感来源拒绝）。第三十九批发现财务BP脱敏数据中实际销售额公式差204.85元且经营公式不能替代会计定义、渠道专案结果无对照不能确证因果、模型阈值/性能缺实证且正文标题分类不一致；第四十批补充供应链成熟度及ROI数据无权威/独立来源、财务BI附录为AI生成且指标定义不足、电商退款订单率与金额率混用；第四十一批发现渠道同比计算错误、金融指标监管定义缺位、RFM/购物篮阈值须本地验证；第四十二批记录BI收益和效率分无测量基线、对账关系需核查粒度/唯一键并保留账务审批闭环；第四十三批发现校服年度数据覆盖待核、财务BP成效无量化基线、竞品第三方数据及归因不可复核；第四十四批记录盈亏平衡公式转录歧义、Altman模型变量不一致和AI效率/就业主张无量化证据；第四十五批记录AI因果/效率主张及电商风险指标缺乏可核口径；第四十六批记录财务看板比较、渠道ROI和电商成本率的证据边界；第四十七批记录敏感人效数据、转型失败比例和电商利润统计出处待核；第四十八批记录马斯克审计效率/预算/岗位说法无来源、附录分析数据和LTV/CAC阈值证据不足；第四十九批记录BI渗透率来源缺失、流程控制与分析方法适用边界；第五十批记录母婴销售看板与波士顿矩阵案例证据不足、同题版本单独保留；第五十一批记录模型数量冲突、RFM阈值依赖样本、疑似羊毛党规则需人工复核；第五十二批记录旧人货场案例及618指标的口径/因果限制；第五十三批记录思维系列“4+4=7”算术冲突、相关不等于因果及战略钟案例不可外推；第五十四批记录门店指标/图示缺验证、模型合集仅作索引、报告规范案例来源边界；第五十五批完成W3 MED收尾，区分同题不同版本并标记公式与绩效主张待核；第五十六批完成W3 LOW六层抽样12条，发现公式、因果、宣传证据问题并拒绝2条敏感数据来源。10 条保留 pending-verification、2 条因敏感内容 rejected 并计入 filtered。第三十八批竞品看板非实数、财务BI供应商案例、库存阈值及库龄数据条件和此前各批证据边界继续保留。MED/LOW 分层抽审及错误集中度复核已完成，未触发扩样（见 `docs/60_delivery/verification/2026-10-26--k3-error-concentration-v1.md`）；全量路由批次057处理12条中的11条并发现1条baseline元数据空壳及allowlist外同标题全文，关联未核；下一步按baseline ID升序继续路由；`CURRENT_RELEASE` 未变，ObsidianWiki 只读。


2026-10-26 K3 接续（批次058）：在批次057已登记的更小ID locator-only例外 `SRC-LOCAL-v1-00625bae4e08042539d1`（全文位于allowlist外）保持待审的前提下，按accepted baseline ID顺序全文审阅12条，9条 routed / pending-verification，3条内部组织/经营来源 project-internal / rejected；未将未核原始出处、产品版本、方法或经营主张写成事实。coverage 9,673 条更新为 routed 177、filtered 22、pending_review 9,474；ObsidianWiki 保持只读，`CURRENT_RELEASE` 不变。下一步继续 K3 全量路由批次059，按 baseline ID 升序，随后完成 coverage 闭合、知识综合与 independent reader。


2026-10-26 K3 接续（批次059）：按baseline ID升序核对12条可读全文及原始 SHA。6条保留待核（资金预算、系统架构、监管互操作、概率决策、AI工具、指标体系）；6条涉及个人隐私或内部企业规划/会议资料而拒绝，未复制敏感细节。coverage 为 routed 183、filtered 28、pending_review 9,462；`CURRENT_RELEASE` 不变，ObsidianWiki 只读。下一步继续全量路由批次060，然后完成coverage闭合、知识综合和independent reader。


2026-10-26 K3 接续（批次060）：按baseline ID升序核验12条全文SHA，9条保留待核、3条企业内部Copilot/运营/物流架构材料拒绝且不复述内容。coverage 当前 routed 192、filtered 31、pending_review 9,450。`CURRENT_RELEASE` 不变，ObsidianWiki 只读。下一步继续K3全量路由批次061；随后闭合coverage、知识综合与independent reader。


2026-10-26 K3 接续（批次061）：按baseline ID升序核对12条可读全文SHA。6条低/中优先级主题保留待核；6条涉及个人健康场景或企业采购/战略/团队/产品架构/仓库元数据，已拒绝且未复制具体敏感内容。coverage 为 routed 198、filtered 37、pending_review 9,438。`CURRENT_RELEASE` 不变，ObsidianWiki只读。下一步继续批次062，再完成coverage闭合、知识综合与independent reader。


2026-10-26 K3 接续（批次062）：按baseline ID升序核对12条全文SHA，7条主题索引保留待核，5条企业内部运营指标、物流/安全架构、身份权限或数据产品设计资料拒绝，不复制细节。coverage 为 routed 205、filtered 42、pending_review 9,426。`CURRENT_RELEASE` 未变，ObsidianWiki只读。下一步继续批次063，继而完成coverage闭合、知识综合与independent reader。


2026-10-26 K3 接续（批次067）：按accepted baseline ID顺序审阅12条，9条完成主题路由并保留 pending-verification，涉及组织管理、应收协同、检索、决策、指令配置、Go性能分析、AI资本叙述、程序化工具调用及注意力架构；原始出处、案例、效果与技术版本未独立核验。3条企业内部系统/产品资料标 project-internal / rejected，不复制细节。正文和文件哈希均与accepted snapshot基线相符。coverage为 routed 245、filtered 61、pending_review 9,367；两个locator-only例外继续待审。ObsidianWiki只读、`CURRENT_RELEASE`不变。下一步立即执行批次068。


2026-10-26 K3 接续（批次068）：按accepted baseline ID顺序审阅12条，10条完成主题路由并保留 pending-verification，涉及AI工程工作流、ERP、Odoo、模型对比、财务职业习惯、RAG、AI编程工具、ReAct与经济租理论；来源、版本、案例与效果未独立核验。一篇财务文章引用的16个图像附件在accepted working tree中均存在，但本轮未审阅图像内容，未据图推断。2条企业内部物流结算和跨境通关方案资料设 project-internal / rejected，不复制系统或指标细节。正文和文件哈希均与accepted snapshot基线相符。coverage为 routed 255、filtered 63、pending_review 9,355；两个locator-only例外继续待审。ObsidianWiki只读、`CURRENT_RELEASE`不变。下一步立即执行批次069。


2026-10-26 K3 接续（批次069）：按accepted baseline ID顺序审阅12条，10条完成主题路由并保留 pending-verification；附件存在但未审阅图像内容的来源仅作正文主题索引，不据图下结论。1条未说明数据主体/底稿的企业月度经营报告标 project-internal / rejected，不复制经营数据。另1条是自动生成目录页，正文记录关联文章元数据缺失且抓取受阻，保持 locator-only / pending-review；新增 locator-only source `SRC-LOCAL-v1-057cabfb9baca9f47c44`，不按链接标题分类。哈希与accepted snapshot基线相符。coverage为 routed 265、filtered 64、pending_review 9,344；三个locator-only来源继续待审。ObsidianWiki只读、`CURRENT_RELEASE`不变。下一步立即执行批次070。


2026-10-26 K3 接续（批次070）：按accepted baseline ID顺序审阅12条，8条完成主题路由并保留 pending-verification；经营指标文章的51张附件在accepted working tree中存在但本轮未审阅图像内容，不据图下结论。3条企业内部Copilot、HR应用与产品规划资料设 project-internal / rejected，不复制内部细节；1条消费品建议与FLOW范围无关而拒绝。所有来源文件与正文哈希均与accepted snapshot基线相符。coverage为 routed 273、filtered 68、pending_review 9,332；三个locator-only例外继续待审。ObsidianWiki只读、`CURRENT_RELEASE`不变。下一步立即执行批次071。
