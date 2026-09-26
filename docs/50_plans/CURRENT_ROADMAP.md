---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 5.13
created_at: 2026-09-12
updated_at: 2026-09-27
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一主线）

> 2026-09-27 主线状态：当前提交 `c08a2f6a`（状态/交接同步）本次未查到对应 GitHub CI run；不得将历史绿灯当作当前 SHA 绿灯。最近一次已验收的 UX 深链历史基线为 `ad76fd4c`，其代码前置 SHA `cef0c362` 的 CI runs `36250368501`、`36248059559` success；全量 API 845 passed、生产 E2E 93/93、Web 142/142、脚本测试 101/101；Clean Damai verify 19/19、只读安全 GET 43/43、浏览器旅程 9/9。深链批次三已完成；UX 工作包仍因全路由×状态×视口验收未完而排队。常驻 `flow` 测试批次偏差未经用户授权不得处置。

> **本页是全仓唯一主线**：既维护状态真相，也维护执行队列。2026-09-25 用户裁决（2A）后不再存在第二份「唯一」文档：EXECUTION_TODO、整合总计划、统一完整实施计划与执行收敛计划均已归档为历史/参考，状态与任务只以本页和工作包为准。详细验收步骤在各工作包与参考规格。

> **测试库安全状态**：共享库误清根因已修复并于 `b60c51b` 验证：测试默认使用
> `flow_test`，常驻 `flow` 零污染。仍须保留该保护，不得将本地破坏性测试指向常驻库。

## 项目状态盘点（仅说明各工作包状态；可执行事项只认下面唯一的“执行队列”）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked（验证出口未满足；工作按唯一队列执行）** | 解析器适配 + 新留出 | 首跑199行均 `not_comparable`；到队列第3项时实施适配、旧样本回归及独立留出，不把验收门槛误作停工理由 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 2a | [大麦物流完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **completed** | 已批准规格；不依赖公开 C 级 | D1–D3 已集成 main `e22d193`，CI run `36137591750` 17/17 success；隔离栈 verify 19/19、八页面 E2E 9/9、重复 seed 零增长、发行包零漂移。**常驻开发库已装载（G2 完成 2026-09-25）**：用户裁决演示数据全部入库，集成后 main 上 verify 19/19、页面可见；合成数据不解除公开 C 级门禁 |
| 2b | [大麦数据后的剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **active（排队；非当前队首）** | G2 ✓；用户已批准 | 深链批次一至三已完成；基线 `ad76fd4c` CI success。剩余为全路由响应/API与页面状态、视口、下钻矩阵及 Gate 5 同 SHA 复验；当前排在 ORG-LEDGER 后；常驻库偏差未获授权不得处置。 |
| 2c | [企业组织建制与经营账套初始化包](work_items/ORG-LEDGER--enterprise-initialization-package.md) | **active（队首待续；隔离测试结果待复核）** | 大麦发行包 completed；遵守安全规格 | 基础包及脚本由 `e1a4d264` 推送；三表 schema 的具体批准由 `fc6e63a7` 记录。自检曾对25个登记文件通过；尚无完整安全验收与隔离旅程。工作区存在 manifest/build 更新、SQL/initialize、reset/initialize service、目录模型、企业服务、`0031_enterprise_directory.py` 与 tests 草案；上次隔离测试已结束但退出码/日志不可得。当前无运行进程；批准范围不含其他 schema/RBAC 改动或常驻库初始化/清理。 |
| K | [第二代静态知识刷新与战略重基线](work_items/KNOWLEDGE--refresh-v2.md) | **active（队列排队，不并行启动）** | 按唯一队列轮到时启动；规格/preflight 已完成 | K0–K6 未执行；`CURRENT_RELEASE` 仍为 `flow-knowledge-2026-09-12.1`，用户战略裁决前不得切换。 |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **blocked(归因、补证与裁决)** | S01 关闭 ✓ | 独立交叉评已完成（[结果](../80_reviews/ai-cross-review/results/gpt-6-astra-2026-09-25.md)）：1,530 格中42异常、109存疑、200因JDL乱码无法完整核验；待原PDF逐项归因/订正。1794/1794仅为登记覆盖口径，不等于通过 |
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

截至 2026-09-27：**11 项，已完成 0 项，实际执行中 0 项，队首待续 1 项，排队 9 项，外部材料受限 1 项**。企业初始化包是唯一队首；发行包基础已推送，三表 schema 具体批准已由 `fc6e63a7` 记录；manifest/build、SQL/initialize、组织模型/服务、迁移、测试及 Damai loader 修改仍在未提交工作区。最近 `uv run pytest -q tests/enterprise tests/fixtures/test_damai_loader.py` 进程已结束，但结果未从发起终端回收，不能据此判 PASS/FAIL。下一步审阅所有未提交差异并重跑该测试取得完整结果，再完成获批迁移与 full/business 隔离初始化旅程。严格限于批准的三表，不改 RBAC、不写常驻库。其余按本唯一队列顺序执行；状态表、工作包和历史文档不是第二份待办。

1. **[队首待续] 企业组织建制与经营账套初始化包**（工作包见状态表2c）：基础包/自检脚本已推送（`e1a4d264`），三表 schema 具体批准已记录（`fc6e63a7`）；manifest/build 更新、SQL/initialize、reset service、模型/迁移/服务/测试和 Damai loader 修改存在于未提交工作区。此前隔离 API/loader 测试结束但无可复核输出；先审查差异并重跑取得完整结果，再完成获批迁移、边界和 full/business 初始化旅程。只可改获批三表；破坏性/持久化验收仅在隔离栈，不碰常驻库。
2. **[排队] UX 可见性与全站验收关闭**（工作包见状态表2b）：完成剩余路由/API/页面数据一致性、五态×390/1024/1440 视口矩阵、缺口与下钻验收，运行 Gate 5 干净 SHA 全链和 CI。深链批次一至三已完成（批次三见 `cef0c362`）；不可写入或清理常驻 `flow`。意外测试批次未经用户授权维持原状。
3. **[排队] 公开财报 C 级归因、原件复核与抽取修订**（工作包见状态表3）：处理已确认42项异常后的109项口径疑点、JDL 200 格原件复核、抽取器修订；保留原始值及证据，任何结论可追溯。
4. **[排队] U04 解析器适配与独立留出验证**（工作包见状态表1'）：这本身是可执行的工程任务，不再误标为阻塞。支持「合并及公司」标题与页码区间参数化；旧三样本回归；对已冻结的小米2026H1、阿里FY2027Q1独立首跑，首跑前不得调参。若遇到输入缺项，主动检查已冻结材料并完成可复现的替代核验记录。
5. **[排队] C 级质量基准与 Go/No-Go**：依赖第3、4项；重跑 L1 并归档机器结果。`1794/1794` 仅表示登记覆盖，不代表准确性通过。
6. **[排队] P3 真实数据、来源与行业扩张**（工作包见状态表3b）：修复/替换 ZTO 乱码文本层并完成抽取、勾稽、页锚、API/UI验证；复核阿里分部序列；C1 只接纳真实财报原件。
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
