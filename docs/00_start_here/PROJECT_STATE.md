---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 5.29
created_at: 2026-09-12
updated_at: 2026-09-29
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

2026-09-29 当前状态（优先于下方较早快照）：14份公开财报样本及 PDF/活动 YAML/报告身份/答案集/行身份映射/实现 SHA 已冻结；L0 1532 项、L1 1776/1776 页锚可重建。行身份实现准确 SHA CI `36478301484` 17/17 success。冻结与 oracle 盘点的定向测试6/6通过；登记清单、5份 oracle YAML 均可解析，当前5份哈希与文件一致，其中小米/阿里 FY2027Q1 两条旧声明已原样保留到 `oracle_sha256_previous_claim` 并以当前实测 SHA 订正。C 级本轮证据审计结论为 No-Go（0/14完整逐行独立 oracle；旧首跑199/199不可比较；两个新 holdout 无首跑 artifact；现有交叉评不是成品盲评），不是数据准确率判负，更不是 C 级通过。详见[冻结与 oracle 审计](../60_delivery/verification/2026-09-29--public-sample-freeze-oracle-audit-v1.md)和[机器可读冻结清单](../../validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml)。

2026-09-29 深夜二段（接手会话·第5项裁决）：隔离栈 `flowcgo` 在 HEAD `3b2d130f` 重跑 C 级两级基准：L0 1532/1532、L1 1776/1776（锚失效/值不一致/未入库均 0，退出码 0）。§3 六条件逐项对账后裁决 **C 级 No-Go**：条件 3（L1 100%）与 6（溯源/supersedes）达成；条件 1（L0 未进 CI，挂载方案待用户批准红线）、2（完整独立 oracle 0/14）、4（泛化层留出 yunda/jdl 未通过）、5（修复后盲评复评未做）未满足。裁决文档：docs/60_delivery/verification/2026-09-29--c-level-benchmark-rerun-gonogo-v1.md（四步解锁路径已列）。唯一队首=第 6 项数据扩张/来源接入。

2026-09-29 深夜（接手会话·U4 关单）：①小米/阿里适配器（hk_interim_english/hk_quarterly_highlights）开发完成，两样本按 §4.5 降级回归集；适配后回归小米 24/25、阿里 15/15（+各 2 勾稽一致），旧三样本 adapter-v5 回归 199/199 零退化；测试 19/19、ruff/mypy 通过。②备选 yunda/jdl 首跑如实失败（yunda 0/20 A股适配器缺口、jdl 0/25 显式降级），身份保持留出。③oracle v2 修订（值零变更）登记。④泛化缺口作为第5项 C 级 Go/No-Go 裁决输入；唯一队首=第5项。

2026-09-29 晚（接手会话）：用户批准两处最小 CI 变更（intake-e2e 超时 40→45、module-boundaries-e2e 关闭未使用的 uv 缓存），提交 `229069ca` 准确 SHA CI run `36511316012` 17/17 success。**小米/阿里未调参首跑已执行**（run ID `2026-09-29-holdout-first-run`，人工介入 0，原始产物全量保留）：小米 0/25（UnsupportedLayoutError，得分 0/1/1，英文版身份正确，真实版式泛化失败）、阿里 0/15（hk_traditional_text 硬编码京东物流年报页锚对 26 页简体公告必然失效）；40 行 oracle 全部 not_comparable、零伪造输出。归因与协议处置（§4.5 降级/备选路径）登记于 holdout-results.md §4。另：常驻 flow 库两个测试偏差批次（`01a0dcdd`、`01a0e22c`）已获用户授权清理——备份 `work/backups/flow-pre-deviation-cleanup-20260929.dump`（SHA-256 `fc06fb58…0737`）后事务删除（24 快照、100,800 指标值、11,088 事实行、2 运行、8 findings、2 导入版本、1 孤儿对象含 MinIO 键），大麦 `damai-demo-v1` 批次完整性核验无损、零孤儿行。

**2026-09-29 U04 执行增量**：旧三样本适配器回归已过：顺丰137/137、腾讯32/32、中通30/30，共199/199匹配、0错配、0不可比较（`validation/financial_reports/holdout_runs/2026-09-29-adapter-v4/`）。Statements 83项、脚本155项、Ruff、mypy 203文件、plan-view、链接门禁通过，M1通过。提交`1b313cb`准确SHA CI run `36494934044` 中 smoke、data-contract、integration及其余功能job通过；`module-boundaries-e2e` Playwright测试通过，但uv post-cleanup因未创建缓存目录而失败。修正 `.github/workflows/ci.yml` 属全局CI/CD配置红线，等待用户批准；准确SHA CI全绿前解析器不冻结，也未读取小米/阿里首跑结果。运行器默认只回归旧样本，新候选须显式指定。当前唯一执行项仍是路线图第4项U04；常驻`flow`、旧`flow_test`均未连接或写入。

历史进度快照（已由本页顶部当前更新覆盖）：公开财报 C 级出口当时仍未通过。JDL v3/L1 v3 `db646f45`（CI run `36427598983` 17/17）、菜鸟19条审定 `279d5e46`（run `36441076686` 17/17）、BABA FY2023 比较期与 P5 派生事实修订 `7735f273168d70e03a4b8ec43e83abd78546446e`（准确 SHA CI run `36463457793` success）均已完成。隔离`flow_test`装载14份报告，L0 1514/1514、L1 1776/1776，锚失效/值不一致/缺库均0；P5事实键670保持不变，14个值变更均为阿里FY2023比较期，JDL无映射明细经分类为旧18条移除（7条旧综合收益错误归类、11条权益变动表页界外项目）与当前9条“合并综合收益表”新增，并非一一替换。109疑点已完成逐格语义裁决：111格台账中109格归入可重建主集、2格真实流动证券投资候选单列为原摘要分母未决；主集未发现数值错误，问题属于现金流合并范围标签、流动/非流动限定、BABA FY2020评审bundle重复current别名及JDL表身份误标。原摘要组计数仍有BABA FY2020 +8、阿里股权组 +1 无法从冻结逐格底稿复原，已明确登记，不将不可复现摘要伪装成准确计数。版本化裁决见`validation/financial_reports/review-ledgers/suspected-109-cell-adjudications-v2.csv`及组表。该阶段唯一子步为把已证实的源行范围/身份修正写入版本化映射并接入种子、L1和派生事实核验；现已由后续提交完成。常驻`flow`数据库/服务未触碰。

2026-09-28 较早状态记录（已由本页首段覆盖）：逐格台账首版及109候选重建状态见下方历史更新；勿据此将JDL 200格视为未核验或将其摘要计数当作当前进展。

本次更新后复验：脚本测试114/114通过（其中本项新增4项），Ruff通过，文档M1通过（299份文档，0错误），全库链接检查0错误，暂存差异检查通过。提交推送及该提交准确SHA的CI仍待完成。

更新：上述台账切片已提交推送 `cbe11d6c405e0b9a23353d63b264fc57e8a360c9`，准确SHA CI run `36391911442` 17/17 success。继续追溯109疑点时，从冻结评审bundle逐项枚举出112条组成员、去重111格（BABA28、阿里现金56、阿里股权14、菜鸟10、JDL4），与109摘要差2，尚无证据判断排除哪两格。该候选集是下一提交内容，全部保持未裁定。

候选审计补充：逐材料汇总中仅 BABA FY2020 36格与候选表38格差2，超出项已定位到股权投资行`value_begin=9,927`、`value_end=4,234`；BABA原件物理41/印刷39证实流动证券投资与非流动同名行并存。两格是否计入109分母仍无原评审底稿依据，不擅自裁决。本轮脚本全量115项、Ruff通过；M1/链接门禁与提交推送后同SHA CI待完成。之后进入JDL原200格逐页核验。

2026-09-28 最新更正（优先于下方历史快照）：UX Gate1/Gate5已完成。提交`0144bad4be1a869a5a4073c516d78b4bf333cbee`对应CI run `36371507389`准确SHA 17/17 success；隔离Dashboard7/7，大麦旅程verify19/19、GET矩阵159项零意外、Playwright15/15，生产E2E157/157、Web143/143、mypy203文件、typecheck/lint、文档M1和链接门禁通过。常驻`flow`未触碰。唯一执行项为公开财报C级收口：只读基线复核提交`f1ab428343e809364c2fd519497c56b4ac7c53bf`对应CI run `36375305428`准确SHA 17/17 success；JDL页界限修复提交`5c84c81fdd3c0908891d16f8dcfe05e1d2e64b6c`对应CI run `36382657675`准确SHA17/17 success。新抽取v2为107行、24/24勾稽，L1 v2有1775/1775页锚；隔离0031栈装载14份报告后L0 1508/1508、L1 1775锚零失配；财报模块76项、脚本110项测试及M1/链接门禁通过。常驻栈未用于测试或修改。下一子步建立逐格对账台账并复核42异常、109口径疑点及JDL原200格。全局队列见 CURRENT_ROADMAP 第3项。

2026-09-28 最新更正（优先于下方历史快照）：利润桥目标映射修复提交`87be90041c477d53f0cabc6718d504d190481103`由GitHub Actions run `36330119396`同SHA **17/17 jobs success**。`bash scripts/test_damai_demo_e2e.sh` fresh `damai-demo-iso`验收seed19/19、只读矩阵159项（149×200、10×422、零意外）、Playwright14/14；`bash scripts/test_module_boundaries_e2e.sh`94/94；`make test-web`143/143、typecheck通过、lint零错误/一条既有TanStack warning。实点修复driver_code到真实指标的映射；期间费用缺少独立指标时显示为非链接。当前唯一下一步继续Operations/Investigation、指标依赖与治理图谱等安全真实下钻，再做全交互路由状态×390/1024/1440视口及Gate5。常驻`flow`禁止重启、重建、迁移、写入。

历史接续快照：UX八个业务页值级子项及159项安全GET基线已完成；Dashboard下钻`e03a1755`与Analysis/Investigation身份下钻`d19a7ff7`均已同SHA CI 17/17关闭。后续进度以本页首段和 CURRENT_ROADMAP 为准。UX仍active；常驻`flow` Compose标签来源混杂，禁止重启、重建、迁移或写入。

2026-09-27 偏差登记：接手会话在本地复现 user-closure E2E 失败时，`scripts/test_user_closure_e2e.sh` 的历史默认 `DATABASE_URL` 将 `alembic upgrade head` 与 `seed_dashboard_demo.py --fresh-batch` 指向了常驻 `flow` 库，在常驻库新增种子批次 `01a0e22c-…`（"FLOW Finance BP dashboard demo"，2026-09-27 17:23:04 +08，与既有偏差批次 `01a0dcdd-8245-7c17-99aa-fce91a8a7a57` 同类；上传旅程测试失败，未产生 intake 写入）。按既有纪律未清理/回滚/切 latest，待用户授权处置。根因已修复（`2117d837`）：脚本对非 CI 环境改为 fail-closed 拦截常驻库连接（`FLOW_USER_CLOSURE_ALLOW_RESIDENT_DB=1` 显式逃逸），并修复该测试的水合竞态（等历史区出现再上传、映射阶段等确认按钮）；隔离库 `flow_user_closure` 复跑 4/4 passed。

截至 2026-09-27：唯一队列共11项，已完成1项、实际执行中1项、排队8项、外部材料受限1项。ORG-LEDGER `2c7d6eb4` 同SHA CI17/17 success。UX Dashboard、`/statements`、`/analysis`、`/operations`、`/metric-library`页面子项均已完成且相应同SHA CI成功；`/metric-library`全页API/配置/UI值级审计通过（隔离verify19/19、GET矩阵159项零意外、浏览器E2E、Web143/143、生产构建UX套件93/93、typecheck/lint通过），代码提交`71ea2dc9`同SHA CI run`36299600894` 17/17 success，子项关闭。唯一执行子步骤转入`/reports`逐值审计：只读值级E2E已交付并隔离复跑全绿（Playwright 10/10、verify19/19、typecheck/lint通过），代码提交后核验同SHA CI即关页；随后`/data`、`/investigations`。UX全站Gate1/Gate5仍未完成。旧影响分析单例失败在隔离批次267 passed及前后单跑未复现，根因未知。其余页面、全路由状态/视口和Gate5未完，UX不得关闭。完整11项顺序、操作/验收/问题处理见[当前路线图](../50_plans/CURRENT_ROADMAP.md#唯一完整-to-do-与执行队列严格串行)与[夜间接手手册](../../HANDOFF.md#04-夜间接手执行手册2026-09-27-当前权威)。

2026-09-26 更新：大麦常驻库曾在备份后幂等恢复并通过 verify 19/19 两次；随后根 checkout 的旧 `make test-dashboard` 误向常驻 `flow` 附加测试批次 `01a0dcdd-8245-7c17-99aa-fce91a8a7a57`（1 import、12 snapshots、1 run、50,400 metric values），可能成为 API `latest`。只读检查确认未删除/覆盖原大麦批次；未获授权，不回滚、不删除。此前备份 `work/backups/flow-pre-demo-rehydrate-20260926.dump`（SHA-256 `b374a16e…9782d`）早于该新增批次，不能作为当前恢复点。`649a2aba` 已推送并通过 CI run `36232029817`：维度表只展示当前快照事实并显示覆盖分母，完整筛选目录保留；Web 136/136、typecheck、隔离 verify19/19、E2E9/9通过。状态/证据文档提交 `7229cd0d` 与 `4c55f10e` 的 CI 也通过。常驻库页面状态需获批处置后重新只读核验；其他全站矩阵仍未完成。
2026-09-26 补充：API 路由审查发现客观报表快照与经营报告渲染的若干 GET 可能新增冻结快照；这些路由已明确排除在只读探测之外，纳入单独 API 语义评审，不以请求验证其状态。其余 Gate 1 只读矩阵与页面状态验收继续推进。
2026-09-26 更新：新增隔离只读矩阵 `0dde935f`，Clean SHA 运行43条 GET、43/43 HTTP200；verify19/19、浏览器E2E9/9。GitHub run `36241816630` 尚运行。指标范围覆盖驾驶舱双期间/四个维度筛选、财报/四问/经营分析、公开期间、指标库、Finding、批次和快照尝试；不会保存响应正文，也排除会冻结写数据的 GET。Gate1页面视口、加载/错误/403和所有下钻仍未完成。
2026-09-26 更新：生产构建页面一致性/响应式/状态 E2E 发现 `/data` 历史批次区和 `/operations` 期间选择框在390px横向溢出，已修复数据表局部滚动、历史头换行及窄屏选择器宽度。69/69 E2E、Web 136/136、typecheck、lint（0 errors、1既有 warning）通过。全站状态×视口截图/所有下钻与异常态仍需逐页验收；新代码 CI 待完成。
2026-09-26 更新：状态验收再补 `/data` 批次历史 loading/403、`/analysis` 工作台 loading/error/403；批次列表 403 明示权限缺失但保留上传入口，pending 状态可访问。生产 E2E 74/74、Web 138/138、typecheck通过、lint0 errors/1既有warning。全站空态/部分降级态与数据密集页390/1024/1440完整状态视口组合仍待补验，新 SHA CI待完成。
2026-09-26 更新：处理无数据空态：`/analysis` 报告列表成功但为空时结束 loading 并显示数据接入引导；`/operations` 两个数据源均成功但均为空时显示准确空态及数据/公开分析入口，不再误报“加载财报列表失败”。测试：生产 E2E76/76、Web139/139、typecheck、lint通过（仅既有warning）。CI仍待新 SHA；未覆盖全部状态/页面/视口组合。
2026-09-26 更新：`main@3c15073f` 隔离完整大麦旅程通过：迁移/seed、verify 19/19、43/43安全 GET、浏览器9/9（含报告发布/下载SHA核验与数据导入）；专属 `damai-demo-iso` 栈已清理，常驻库未触碰。CI run `36243330055` 尚queued。Gate1其他页面状态-视口矩阵/深链未关闭。

2026-09-26 更新：全站深链批次三在主线工作树本地实现：只读公开财报 PDF 读取限定已登记 SHA 并校验对象内容，原文访问由 statement.source.read 授权并 durable audit；有登记原件的页码徽标才指向 PDF 页；调查源单元格沿 Finding/ImportVersion/Batch/SourceRecord 血缘读取；冻结新 objective payload 保留页锚并在原件可用时给 HTML 生成回链；管理关注已有 metric_code 增加指标库链接。没有可证实的 finding_id 关系，不虚构关联。批次历史端点本已存在。Web 142/142、相关 API 30/30、全量 API 845 passed、生产 E2E 93/93，Clean Damai verify 19/19、可见性 API 43/43、浏览器 9/9、脚本测试 101/101、文档门禁通过。前一 SHA 的 CI dashboard 状态测试暴露 cwd 相对 fixture 路径错误，已修复并纳入生产 E2E；`cef0c362` / run `36248059559` CI success。全站 UX 工作包仍 active，Gate 1全路由页面/状态/视口矩阵未完成。

截至本次文档同步，批次历史 clean-SHA 隔离验收通过（seed/verify19/19、浏览器9/9）；dashboard CI URL冲突已修复，最新SHA/CI见路线图。常驻开发库安全恢复与验证19/19两次完成。大麦发行财报各51行、FY2025覆盖37/40、FY2026 40/40；常驻API有8卡、12/12趋势及2条findings，状态degraded且矩阵保留合理缺格；3000端口 hydration 与KPI缺失原因展示已修复。经营分析点余额读取与派生指标依赖缺陷已修复（FY2026七项运营效率指标均可算，其中流动比率0.8119、资产负债率0.8986、DSO 116.3881天），比率单位和公开披露缺项/内部授权原因按语义显示。40次GET、36个不同路由/参数组合全部HTTP200；正式报告产物历史为空与API持久化一致。其他页面金额/数量格式、Gate1完整视口/错误态复测、批次三与其余页面下钻仍待完成。主线只在`main`串行推进。

上段中的“两次 dashboard CI 失败”及“CI现需修正”仅记录本次修复前状态；以本页顶部更新为准：dashboard job 已通过，完整 workflow 尚在运行。

历史状态快照：下文部分 S01/R0–R4 描述记录了各自交付时的上下文；若与当前状态、分支集成或门禁冲突，以本段和 [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md) 为准。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。U8 冻结后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一主线：状态真相 + 单一串行 To-do）：U08、S01、前端一致性整改、大麦完整财年演示数据及 UX Gate 1/Gate 5 已完成；当前唯一执行项是公开财报 C 级归因/原件复核/抽取修订。全部后续任务及状态只按该路线图执行。
- 旧统一计划、O 系列计划、EXECUTION_TODO 与 2026-09-24/25 三份总计划均已 superseded/archived（保留历史细节与证据，不再作为执行依据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 历史工作流与阶段快照（非当前 To-do）

> 下方条目保留各阶段形成时的上下文，部分状态已过时，不代表当前执行/阻塞/授权情况，也不是可领取任务。当前唯一状态以本页开头为准；唯一队列及下一步只看 [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md)。

1. **U8（已完成并冻结）**：[生产冻结交付记录](../60_delivery/2026-09-13-u8-production-freeze.md)；可恢复基线 `u8-final-baseline`；严格冻结标签 `flow-u8-freeze-20260913`。
2. **U4（blocked）**：旧样本首跑 199 行均不可比较；小米 2026H1 与阿里 FY2027Q1 新 holdout 已冻结并录入独立 oracle，先修版式适配并回归旧样本，再按盲测纪律运行新留出。
3. **[S01 战略边界、事实合同与安全门禁](../50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）**：Task 1–5 + R0/R1（台账 §6）+ R2/R3/R4（台账 §7）全部交付，Task 6 正式关闭。阶段 3 起转入[公开模块 C 级出口](../50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（T09–T12，gated）。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。
7. **大麦完整财年演示数据（底座 completed；页面覆盖部分完成）**：24个月synthetic全链已落地；常驻开发库受控恢复、verify19/19两次通过。Dashboard API 200、8卡、趋势12/12、2条findings，仍degraded；财报2份、发布快照1、冻结候选12，静态覆盖FY2025 37/40、FY2026 40/40。毛利矩阵实际/预算比较各10/32格可用，缺格不补零。常驻只读页面显示批次/Finding/财报/经营快照，未发布比较值显式标记；经营分析资产负债表点余额角色问题修复，百分比/倍数/天数已单位化显示。正式报告产物历史为空，其他页面金额/数量格式审计仍待完成。隔离栈verify19/19、浏览器E2E9/9；FY2025四问API500已修复。Gate 1全路由响应矩阵、Gate3/4其他页面呈现/下钻及深链批次三未完成。详见[Gate 1/Gate 2记录](../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)和[剩余体验收口工作包](../50_plans/work_items/UX--post-damai-experience-closeout.md)。合成数据不解除公开C级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
