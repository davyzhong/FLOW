---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 5.36
created_at: 2026-09-12
updated_at: 2026-09-30
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一主线）

> **2026-09-30 深夜·驾驶舱抢队首（用户裁决）**：用户裁决三项——① 交付形式为**真实产品页面**（Next.js 组件化 + 真实 API + `apps/web/cockpit/*` 路由，不做静态原型）；② 驾驶舱**抢在 U04 盲评复评之前当队首**，U04 转「暂停（驾驶舱让位）」、恢复条件 = 驾驶舱批次 A 完成；③ 第一版**用大麦物流演示数据**跑通真实链路，不等 U04 / C 级。**C 级出口状态不变（仍 No-Go），驾驶舱用演示数据不构成公开财报能力证明。** 详见下表队首行与[实施方案](../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md)。批次 A 开工前须先裁决实施计划 §6 的 Q1（图表技术选型）。

> （接替说明）以下 2026-09-29 的队首裁决（盲评复评为队首）已被本条接替，U04 转为暂停。

> **2026-09-29 深夜·路线纠偏（用户裁决）**：用户确认 C 级 No-Go 解锁路径优先于数据扩张——ZTO 接入封存（`wip/zto-integration-20260929`），队首改为**修复后盲评复评**（C 级条件 5）；L0 挂 CI 方案待批；oracle 分批与泛化收敛随后。第 6 项 P3 暂停。

> **2026-09-29 U04 进度更新**：旧样本回归解析器与对比器修复已完成，本地 API statements 83项、脚本 unittest 155项、Ruff、mypy 203文件、plan-view、链接门禁均通过，文档 M1 通过；顺丰137/137、腾讯32/32、中通30/30，合计199/199匹配、0错配、0不可比较，产物为 `validation/financial_reports/holdout_runs/2026-09-29-adapter-v4/`。这是旧回归，不是新留出泛化通过。提交`1b313cb`准确SHA CI 中，smoke/data-contract/integration 等功能性 job 通过；`module-boundaries-e2e`测试通过，但 uv post-cleanup 因该 job 未创建 cache 目录而失败。用户批准两处最小 CI 变更（intake-e2e 超时 40→45、module-boundaries-e2e 关闭未使用的 uv 缓存）后提交 `229069ca` 准确 SHA CI run `36511316012` 17/17 success。**小米/阿里未调参首跑（run ID `2026-09-29-holdout-first-run`）双双失败**：小米 0/25、阿里 0/15，全部 not_comparable、零伪造输出，归因均为版式泛化失败（无对应适配器），登记于 [holdout-results.md §4](../implementation/objective-analysis/holdout-results.md)。按 oracle-register §4.5，用样本开发适配器即降级为回归集并启用备选 yunda/jdl 补新留出——此为下一 fork。运行器默认只选旧回归，新样本必须显式选择。常驻`flow`、`flow_test`未连接/未写入。

> 2026-09-29 最新执行进展：行身份/范围修订提交`eb2b7f3cbadec0c36eb4b36473c6321d69aa4fff`准确SHA CI run `36478301484` 17/17 success；全新隔离`flowcverify`实测 L0 1532/1532、L1 1776/1776，P5 facts 670 条内容 SHA 稳定。14份报告的样本冻结与 oracle/holdout 盘点已形成确定性清单 [`c-level-freeze-2026-09-29-v1.yaml`](../../validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml) 及审计 [`公开财报 C 级样本冻结与独立验证审计`](../60_delivery/verification/2026-09-29--public-sample-freeze-oracle-audit-v1.md)。冻结测试6/6通过；报告登记和全部5份 oracle YAML 可解析，当前哈希一致。审计结论：C级 **No-Go（证据不足，不代表准确率失败）**——14份被测报告完整独立 oracle 为0/14；旧三份留出首跑199行全部不可比较；小米与阿里 FY2027Q1 新留出未发现首跑结果；既有抽取交叉评并非渲染报告盲评。原两条错误 oracle 哈希已保留历史声明并订正当前实测SHA。U04 解析与生产依赖修复提交`1b313cb`的准确SHA CI 中仅 `module-boundaries-e2e` 的 uv cache post-cleanup 失败；该 CI 收尾修正经用户批准后由提交`229069ca`完成（另含 intake-e2e 超时 40→45），run `36511316012` 17/17 success，随后小米/阿里未调参首跑已完成并登记失败归因（holdout-results.md §4）。常驻`flow`数据库/服务未触碰。

> 2026-09-28 最新更正：UX Gate1/Gate5 已关闭。Gate5 在提交`0144bad4be1a869a5a4073c516d78b4bf333cbee`完成：隔离大麦验收 verify 19/19、GET 矩阵159项零意外、Playwright 15/15；Dashboard 隔离验收 7/7；生产 E2E 157/157、Web 143/143、API mypy 203文件、typecheck/lint、文档 M1 与链接门禁通过；准确 SHA 的 CI run `36371507389` 17/17 success。常驻`flow`未触碰。唯一执行项转为公开财报 C 级归因、原件复核与抽取修订。

> 2026-09-27 最新进度（优先于下方历史快照）：八个业务页值级子项已完成。Dashboard真实下钻修复已由 `e03a1755` / CI run `36319686868` 同SHA 17/17 success。新一轮隔离验收扩展Analysis/Investigation链接身份：四问指标→指标库、财报身份→对应财报、Finding→同一分析运行→指标快照报告；verify19/19、GET矩阵159项（149×200、10×预期422、零意外）、浏览器13/13；生产E2E94/94、Web143/143、lint/typecheck通过。代码测试尚未提交/同SHA CI。覆盖与剩余链接见[Gate 1覆盖证据](../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)。唯一执行项仍是 UX：先同步文档、门禁、提交推送和同SHA CI，再逐项补剩余安全下钻→状态×390/1024/1440视口矩阵→Gate5最终全链同SHA验收。常驻`flow` Compose来源标签混杂，不得重启、重建或写入。更早页面子项进度只作历史，不代表当前执行位置。

> 历史快照：`/data` 与 `/investigations` 子项在 `3660389e` 收尾；当前唯一执行位置以上方最新进度及“执行队列”为准。

> 历史快照（已被首段覆盖）：`/reports`、`/data`、`/investigations`阶段验收通过；这条历史更新不再代表当前唯一执行页面或剩余工作。

> 历史快照：ORG-LEDGER `2c7d6eb4` 与 UX 页面各阶段提交、CI结果和早期状态视口材料保留在工作包及交接的历史记录中；本段原含旧页面执行顺序，当前以本页首段和执行队列为准。

> **本页是全仓唯一主线**：既维护状态真相，也维护执行队列。2026-09-25 用户裁决（2A）后不再存在第二份「唯一」文档：EXECUTION_TODO、整合总计划、统一完整实施计划与执行收敛计划均已归档为历史/参考，状态与任务只以本页和工作包为准。详细验收步骤在各工作包与参考规格。

> **测试库安全状态**：共享库误清根因已修复并于 `b60c51b` 验证：测试默认使用
> `flow_test`，常驻 `flow` 零污染。仍须保留该保护，不得将本地破坏性测试指向常驻库。

## 项目状态盘点（仅说明各工作包状态；可执行事项只认下面唯一的“执行队列”）

2026-09-28 当前状态补记（再由本页首段最新进度覆盖）：JDL原200格英文版逐格对照已完成；184格来源行/列/值匹配（含5个源表空值），16格综合收益表归属与父项语义未决。109候选比材料统计多2，保留并行核验，不阻塞后续。C级仍未通过。

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| **0** | **[CFO 财务总监驾驶舱产品化](work_items/COCKPIT--cfo-dashboard-implementation.md)** | **active（唯一队首·2026-09-30 用户裁决抢队首）** | 大麦演示数据 ✓ + ORG-LEDGER ✓ + S01 ✓ | 原型 v2.0（1.16MB 单文件、51 图表、三模式做实、全卡穿透，Playwright 逐页 51/51 渲染成功、0 JS 错误）+ 设计文档 v0.6（§1–§10，§10 安全前置清单）。用户 2026-09-30 裁决：真实 Next.js 页面 / 抢在 U04 之前 / 用大麦数据跑通。**不解除 C 级门禁**。[实施方案](../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md) |
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked（队列暂停·驾驶舱让位）** — 恢复条件 = 驾驶舱批次 A 完成 | 样本冻结已完成 | 旧三样本回归199/199完成；准确SHA CI 仅余 module-boundaries-e2e 的 uv cache cleanup 失败（测试通过），修正需用户批准；之后首次未调参运行小米2026H1、阿里FY2027Q1。完整独立 oracle 与报告盲评仍是 C 级证据门槛 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 2a | [大麦物流完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **completed** | 已批准规格；不依赖公开 C 级 | D1–D3 已集成 main `e22d193`，CI run `36137591750` 17/17 success；隔离栈 verify 19/19、八页面 E2E 9/9、重复 seed 零增长、发行包零漂移。**常驻开发库已装载（G2 完成 2026-09-25）**：用户裁决演示数据全部入库，集成后 main 上 verify 19/19、页面可见；合成数据不解除公开 C 级门禁 |
| 2b | [大麦数据后的剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **completed** | G2 ✓；用户已批准；ORG-LEDGER CI ✓ | Gate1/Gate5关闭：隔离 Dashboard 7/7；大麦验收 verify19/19、GET矩阵159项零意外、Playwright15/15；生产E2E157/157、Web143/143、mypy203文件、typecheck/lint、M1/链接检查通过；提交`0144bad4`同SHA CI run `36371507389` 17/17 success。常驻库未触碰。 |
| 2c | [企业组织建制与经营账套初始化包](work_items/ORG-LEDGER--enterprise-initialization-package.md) | **completed** | 大麦发行包 completed；批准三表 schema | `2c7d6eb4`；CI run `36270782272` 的17/17 jobs success。隔离 `full` 首次/重复与 `business` 对账通过；11 个企业/loader 测试、全量 API 852、Web142、脚本107、大麦 verify19/19、API43/43、Playwright9/9、合同/文档/lint/typecheck 均通过。31文件 manifest 稳定 SHA `cbc7cccf…e513`。 |
| K | [第二代静态知识刷新与战略重基线](work_items/KNOWLEDGE--refresh-v2.md) | **active（队列排队，不并行启动）** | 按唯一队列轮到时启动；规格/preflight 已完成 | K0–K6 未执行；`CURRENT_RELEASE` 仍为 `flow-knowledge-2026-09-12.1`，用户战略裁决前不得切换。 |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **active（C级门禁未通过）** | 行身份修订与样本冻结 ✓ | 本轮证据审计已作 No-Go（证据不足，不是准确率判负）；当前队首转入 U04，C级仍无14份完整独立 oracle、新 holdout 首跑及成品盲评 |
| 3a | [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | — | B3 溯源 95.5% 行项目带页锚（迁移 0029 + 导入/API/前端）；B4 supersedes 链 + 差异脚本；B5 只读 MCP 三工具（token fail-closed）；B6 确定性差异说明起草 |
| 3b | [数据扩张、行业基准与 10× 性能基线](work_items/PUBLIC--data-expansion-benchmarks.md) | **active（队列排队，不并行启动）** | 性能基线 ✓；扩张待外部财报 | G2 完成：10×（1034→10340 行）P95 明细 6.2ms/检索 0.97ms/聚合 1.11ms（`perf_baseline.py`）；C1 扩张需真实财报到料 |
| 3c | [AI 问数 v1 与评测集](work_items/PUBLIC--ai-qa-v1.md) | **completed(v1)** | — | 确定性检索引用 QA + 94 问评测集（60 数值 + 34 拒答）命中率 100%、拒答零误答（`ask_facts.py` / `generate_qa_eval.py`）；LLM 通道与 v2/v3 另行裁决 |
| 3d | Web 前端一致性整改（信息架构/设计 token/组件库/五态/响应式） | **completed** | — | P0–P3 五批：`fe61b5c`（F2 token+值漂移）→ `8fa13a6`（生产构建门禁+溢出修复）→ `53ef2eb`（数据态门禁+触控+溯源交互）→ `defd823`（PageState+FlowDataTable+两页迁移）；P4–P5 四批（2026-09-18）：`0c4c45a`（metric-library 深度迁移）→ `b7b4257`（investigations 详情）→ `3089472`（Task 8 切片）→ `9cf8cb3`/`02c11ea`（frontend-states 状态门禁+60 图状态矩阵归档）；门禁矩阵 390/1024/1440 × 数据态 × 加载/错误/403，生产 e2e 69/69、单测 86/86、lint 1 登记例外；Task 0–9 全关闭，执行日志见[整改计划 §10](../superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md)。遗留（不阻塞）：溯源真实来源链接（已按公开来源政策解锁，见 HANDOFF v3.3 §2.3） |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告。设计输入已备：知识库第二截面登记经营分析会四体系/月度周期蓝本与月报可视化实例（借鉴 #20/#22/#24，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）；AR 应收信用子域知识（科目/口径/账龄五桶/催收与信用规则，借鉴 #26，[FinBoss 评估册](../knowledge-base/02_research/synthesis/2026-09-19-finboss-assessment.md)——整理性质，行业参考值待溯源） |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked（依赖/证据门槛，不等用户授权）** | 公开 C 级 + 可用真实企业数据 | 用户已授权执行；轮到后先用可用数据完成技术试点。无真实企业数据时形成明确的未验证结案，不把合成数据冒充真实试点 |
| R2' | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked（依赖证据门槛，不等用户授权）** | U4 + U8 + U09/O05 | U8 已完成；轮到后整理现有证据、逐项给出有依据的 go/hold，不因待证据项停止其他执行 |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

## 唯一完整 To-do 与执行队列（严格串行）

本轮进度及验证以本页首段为准。此前相关提交：首版台账`cbe11d6c405e0b9a23353d63b264fc57e8a360c9`/run `36391911442` 17/17；109候选重建`8cc968594aa1f087622f6155e8d3651a5d65c0bf`/run `36397631508` 17/17；JDL来源逐格复核`fdc96d63146e0ed8cb12e75a50f488dd3015398f`/run `36404144739` 17/17；BABA/P5修订`7735f273168d70e03a4b8ec43e83abd78546446e`/run `36463457793` success。109候选112组成员、去重111格，比材料统计109多2（BABA FY2020期初9,927/期末4,234）；二格原页确认流动证券投资行，但评审分母仍无证据，明确保留未决。JDL 200格本轮已逐格附页坐标和原文证据；常驻`flow`不写入。

2026-09-28 执行进度：UX Gate1/Gate5 已在`0144bad4`完成并由准确 SHA 的 CI run `36371507389` 17/17验证通过。C级只读来源基线审计提交`f1ab4283`对应CI run `36375305428` 17/17 success。JDL页界限修复提交`5c84c81fdd3c0908891d16f8dcfe05e1d2e64b6c`对应CI run `36382657675`准确SHA 17/17 success。隔离Compose栈迁移0031并装载14份报告，L0 1508/1508，L1 1775锚零失配；财报测试76项、脚本测试110项、M1、链接、定向ruff及shell语法通过。唯一下一子步为建立42异常/109口径疑点/JDL原200格的规范化逐格台账并逐项复核原件。常驻`flow`不写入/清理/重启/重建。

2026-09-29 最新更正：109格语义裁决和其后行身份/范围修订及全链验证已完成。新的 L1 v5 覆盖1776/1776；独立 `flowcverify` 全新隔离栈装载14份报告后 L0 1532/1532、L1 1776/1776，P5事实670条内容SHA不变。C级仍未通过。下一唯一子步为冻结样本/证据清单并核验尚未闭合的独立 oracle、盲评和 holdout；交付后作 Go/No-Go。常驻库未写入。

截至 2026-09-29：**11项，已完成3项，唯一执行中1项，排队7项**。第3项的样本与证据审计已按现有材料作 No-Go 结案；产品 C 级出口本身仍未通过。第4项 U04 的旧三样本版式回归已实现199/199，生产依赖修复已推送。准确SHA CI 的功能性 job 全绿，但模块边界 E2E 作业的 uv cache post-cleanup 失败（Playwright 测试成功）；由于修复会改 CI 配置，需先取得用户批准。批准前不读取小米/阿里抽取结果、不标记 CI 通过。常驻`flow`不写入/清理/重启/重建。

1. **[完成] 企业组织建制与经营账套初始化包**（工作包见状态表2c）：提交 `2c7d6eb4`，CI run `36270782272` 的17/17 jobs success。31文件发行包稳定 manifest SHA `cbc7cccf…e513`；隔离 `full` 首次/重复、`business` 重置及回滚/租户隔离通过；全量 API852、Web142、脚本107、verify19/19、只读 GET43/43、Playwright9/9，合同/文档/lint/typecheck均通过。仅三表迁移在隔离栈验证，未触碰常驻库。
2. **[完成] UX 可见性与全站验收关闭**（工作包见状态表2b）：Gate1/Gate5证据与准确SHA CI已收口，见上方最新状态和工作包最终关闭记录。

3. **[完成—证据审计 No-Go] 公开财报 C 级样本/证据盘点与当前门禁裁定**：冻结14份 PDF/YAML、报告身份映射、行身份修订表、L1 v5、实现 SHA；哈希确定性重建测试6/6。审计证实14份报告没有完整独立 oracle；5份既有 holdout oracle 均为部分转录，两个新留出尚无首跑结果；旧首跑199行全部不可比较；现有交叉评不是成品盲评。故本阶段 C 级判为 No-Go（证据不足），详见[冻结与 oracle 审计](../60_delivery/verification/2026-09-29--public-sample-freeze-oracle-audit-v1.md)。这不是 C 级通过，剩余证据工作继续由第4、5项承接。
4. **[进行中] U04 解析器适配与独立留出验证**（工作包见状态表1'）：顺丰文本型“合并及公司”、腾讯财报表格动态定位、中通公告重复字形解析，以及 comparator 列名/报表范围已修复；旧三样本回归199/199，见 adapter-v4。初始 smoke 缺包原因已定位为`pypdf`仅列dev组，现已移至生产依赖；独立 Compose 验证API/Web健康、迁移和dev主体seed成功。CI 收尾修正（`229069ca`，含 intake-e2e 超时 40→45 与 module-boundaries uv 缓存关闭，均经用户批准）已全绿：run `36511316012` 17/17 success。**首跑已执行**（run ID `2026-09-29-holdout-first-run`，输入/代码/oracle SHA 与完整机器 diff 已保存，人工介入 0）：小米 0/25、阿里 0/15，全部 not_comparable，零伪造输出；归因均为版式泛化失败（无对应适配器），见 holdout-results.md §4。**U4 已按范围关单（2026-09-29 深夜）**：①旧回归 adapter-v5 199/199 零退化；②小米/阿里适配器开发完成并按 §4.5 降级回归集（适配后回归 24/25、15/15+勾稽一致）；③备选 yunda/jdl 先冻结+oracle 后首跑：yunda 0/20（A 股适配器缺口）、jdl 0/25（显式降级），失败原始保留、身份保持留出；④泛化缺口登记为第5项裁决输入。关单提交链 `4f997020`+`a28b638d`（static-python 修复），准确 SHA CI run `36525496607` 17/17 success，**U4 正式关闭**。细节见 holdout-results.md §5 与 U04 工作包。不能由实现方代替独立录入/盲评。
5. **[完成·No-Go 裁决] C 级质量基准与 Go/No-Go**：当前 HEAD `3b2d130f` 隔离栈 `flowcgo` 重跑 L0 1532/1532、L1 1776/1776 零差异并归档；§3 六条件对账裁决 **No-Go**（条件 1/2/4/5 未满足：L0 未进 CI、完整 oracle 0/14、泛化层留出失败、盲评复评未做；条件 3/6 达成）。裁决文档与四步解锁路径见 [2026-09-29 C 级基准重跑与 Go/No-Go](../60_delivery/verification/2026-09-29--c-level-benchmark-rerun-gonogo-v1.md)。**用户路线纠偏裁决（2026-09-29）**：解锁路径重排为——①盲评复评（队首，条件 5）；②L0 挂 CI（条件 1，方案待批）；③oracle 分批/泛化收敛（条件 2/4）；④数据扩张（原第 6 项）暂停。
6. **[暂停·用户裁决 2026-09-29] P3 真实数据、来源与行业扩张**：ZTO 接入已完成大半（产品 YAML 57 行与 oracle 逐值一致、L1 答案集 v6 1823/1823 全锚定、隔离栈 L0/L1 实测零差异），按用户路线纠偏裁决**封存**于分支 `wip/zto-integration-20260929`（`2ce0700e`），未完成 API/UI 链路与文档同步。恢复条件：C 级解锁四步完成后或用户重新指令。阿里分部序列复核与 C1 扩张随本项一并暂停。
7. **[排队] 第二代静态知识 release 与战略重基线**（工作包见状态表K）：按已批准 K0–K6 完成 Davybase 图片批次验收、非微信图片覆盖、稳定15:00 Obsidian Git 截面、来源基线与知识资产、sealed candidate、战略影响评估、用户正式裁决、原子激活和独立复验。完成用户裁决前 `CURRENT_RELEASE` 不变。
8. **[外部材料受限；必须完成主动恢复/结案] `rnd_exp` 官方依据核验**：先搜索官方发布渠道、项目归档及可验证副本并记录来源；若穷尽后仍无原文，交付可复现的“原文不可得/当前值未核实”报告、影响范围及后续重启条件，不得宣称官方核验通过；完成该结案后继续队列。
9. **[排队—依赖验收门槛，不等用户授权] U09/O05 内部试点**（工作包见状态表R1）：公开 C 级达到 Go 且真实企业数据可用时完成真实试点；队列轮到时先完成系统/合成数据技术验证并整理授权范围。真实数据不可得则如实结案为“真实试点未验证”，不得把合成数据冒充真实证据，也不得以等待授权为由停摆。
10. **[排队—依赖证据，不等用户裁决] U10 V1.1 证据决策**（工作包见状态表R2'）：轮到后按既有标准整理已有证据并逐项给出 go/hold；证据缺口说明具体影响和替代证据路径，不把用户批准或确认设为默认下一步。
11. **[排队] 内部月度工作台与四级真实周期验收**：依赖 C 级通过、数据可用和工作台可用；完成连续3个真实月度周期、同输入人工基准、逐周期盲评和20%工时门槛。无真实周期数据时，先完成环境、流程和合成数据技术验收，形成真实验收的未满足清单及重启条件；不得以模拟数据替代真实结论。

裁决记录（2026-09-25 晚，用户四项裁决）：①分支整合归本主线串行执行；②四份「唯一」文档合并为本页唯一主线（2A）；③AI交叉评原由助手准备、用户发起，后经用户追加委托由助手安排未参与实现的隔离AI审查，结果见本页；④holdout候选由AI可复现随机抽签并归档（4A），数据冻结与oracle另行执行。

战略方向（2026-09-13，D052–D054）：企业内部月度财务经营分析工作台为最终产品，公开财报模块独立并先行成熟共享底座；顺序为 U8 → 边界重构 → 公开模块 C 级出口 → 内部工作台 → 四级验证。详见[战略重构设计](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)。

2026-09-24 补充：大麦合成发行版是“系统完整性验证工具”，知识刷新是“静态知识
维护轨”，两者可在公开 C 级外部门禁等待期间推进；二者均不改变 D052–D054 的
真实数据验收顺序，也不能代替独立 oracle、holdout 或真实企业三周期验证。

## 已完成的非待办参考

知识库增量扫描、指标库行业包、竞对五维矩阵及 O-01/O-02 地基均为已完成证据或设计输入，不再作为并行/非阻塞待办；相关详情分别见[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)、[五维矩阵](../competitive/2026-09-17-five-dimension-matrix.md)和指标库规格索引。Davybase 新增图片批次及非微信覆盖属于上面第6项的未完成工作，不能据早期扫描记录判为完成。

## 纪律

2026-09-26 深链批次三验收更新（覆盖本页第 4 项旧待办措辞）：批次三本地实现及验收完成，Clean Damai verify 19/19、可见性 API 43/43、浏览器 9/9、全量 API 845 passed、生产 E2E 93/93、Web 142/142、脚本测试 101/101；M1/link 门禁通过，修复 SHA `cef0c362` 同 SHA CI 成功。全站页面状态/视口矩阵仍未完成，故第 4、5 项保持 active，不能宣布 UX 工作包关闭。细节见[深链实施计划](2026-09-26-ui-deep-link-implementation-plan.md)。

2026-09-26 CI 补记：`bc141444` CI dashboard job 的两条状态测试因 helper 将 repo-root cwd 拼成错误 fixture 路径失败；已改为按源文件目录定位，并把该 spec 加入生产 E2E。修复后本地生产 E2E 93/93 通过；修复 SHA `cef0c362` 的 GitHub Actions run `36248059559` success。

- 任务领取/勾选/提交只用本页与工作包；模块可以维护不可领取的 workstream/backlog 视图，但不得形成第二份状态真相；每完成一阶段提交推送、CI 绿才算 done；
- 详细验收步骤在工作包与归档参考规格（原统一实施计划、执行收敛计划等，均已 archived）；旧详细计划均为历史证据，不按其空复选框恢复任务；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
