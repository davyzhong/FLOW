---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 5.5
created_at: 2026-09-12
updated_at: 2026-09-26
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一主线）

> 2026-09-26 当前基线：主线 `ad76fd4c` 及其前置代码 SHA `cef0c362` 的 GitHub CI 均 success（run `36250368501`、`36248059559`）。全量 API 845 passed、生产 E2E 93/93、Web 142/142、脚本测试 101/101；Clean Damai verify 19/19、只读安全 GET 43/43、浏览器旅程 9/9。深链批次三已完成；UX 工作包仍因全路由×状态×视口验收未完而 active。常驻 `flow` 测试批次偏差未经用户授权不得处置。

> **本页是全仓唯一主线**：既维护状态真相，也维护执行队列。2026-09-25 用户裁决（2A）后不再存在第二份「唯一」文档：EXECUTION_TODO、整合总计划、统一完整实施计划与执行收敛计划均已归档为历史/参考，状态与任务只以本页和工作包为准。详细验收步骤在各工作包与参考规格。

> **测试库安全状态**：共享库误清根因已修复并于 `b60c51b` 验证：测试默认使用
> `flow_test`，常驻 `flow` 零污染。仍须保留该保护，不得将本地破坏性测试指向常驻库。

## 项目状态盘点（仅说明各工作包状态；可执行事项只认下面唯一的“执行队列”）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked（按队列等待）** | 解析器适配 + 新留出 | 首跑199行均 `not_comparable`；适配后旧样本回归，再按冻结协议跑独立留出 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 2a | [大麦物流完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **completed** | 已批准规格；不依赖公开 C 级 | D1–D3 已集成 main `e22d193`，CI run `36137591750` 17/17 success；隔离栈 verify 19/19、八页面 E2E 9/9、重复 seed 零增长、发行包零漂移。**常驻开发库已装载（G2 完成 2026-09-25）**：用户裁决演示数据全部入库，集成后 main 上 verify 19/19、页面可见；合成数据不解除公开 C 级门禁 |
| 2b | [大麦数据后的剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **active（队列第1项）** | G2 ✓；用户已批准 | 深链批次一至三已完成；基线 `ad76fd4c` CI success。剩余为全路由响应/API与页面状态、视口、下钻矩阵及 Gate 5 同 SHA 复验；常驻库偏差未获授权不得处置。 |
| K | [第二代静态知识刷新与战略重基线](work_items/KNOWLEDGE--refresh-v2.md) | **active（队列排队，不并行启动）** | 按唯一队列轮到时启动；规格/preflight 已完成 | K0–K6 未执行；`CURRENT_RELEASE` 仍为 `flow-knowledge-2026-09-12.1`，用户战略裁决前不得切换。 |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **blocked(归因、补证与裁决)** | S01 关闭 ✓ | 独立交叉评已完成（[结果](../80_reviews/ai-cross-review/results/gpt-6-astra-2026-09-25.md)）：1,530 格中42异常、109存疑、200因JDL乱码无法完整核验；待原PDF逐项归因/订正。1794/1794仅为登记覆盖口径，不等于通过 |
| 3a | [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | — | B3 溯源 95.5% 行项目带页锚（迁移 0029 + 导入/API/前端）；B4 supersedes 链 + 差异脚本；B5 只读 MCP 三工具（token fail-closed）；B6 确定性差异说明起草 |
| 3b | [数据扩张、行业基准与 10× 性能基线](work_items/PUBLIC--data-expansion-benchmarks.md) | **active（队列排队，不并行启动）** | 性能基线 ✓；扩张待外部财报 | G2 完成：10×（1034→10340 行）P95 明细 6.2ms/检索 0.97ms/聚合 1.11ms（`perf_baseline.py`）；C1 扩张需真实财报到料 |
| 3c | [AI 问数 v1 与评测集](work_items/PUBLIC--ai-qa-v1.md) | **completed(v1)** | — | 确定性检索引用 QA + 94 问评测集（60 数值 + 34 拒答）命中率 100%、拒答零误答（`ask_facts.py` / `generate_qa_eval.py`）；LLM 通道与 v2/v3 另行裁决 |
| 3d | Web 前端一致性整改（信息架构/设计 token/组件库/五态/响应式） | **completed** | — | P0–P3 五批：`fe61b5c`（F2 token+值漂移）→ `8fa13a6`（生产构建门禁+溢出修复）→ `53ef2eb`（数据态门禁+触控+溯源交互）→ `defd823`（PageState+FlowDataTable+两页迁移）；P4–P5 四批（2026-09-18）：`0c4c45a`（metric-library 深度迁移）→ `b7b4257`（investigations 详情）→ `3089472`（Task 8 切片）→ `9cf8cb3`/`02c11ea`（frontend-states 状态门禁+60 图状态矩阵归档）；门禁矩阵 390/1024/1440 × 数据态 × 加载/错误/403，生产 e2e 69/69、单测 86/86、lint 1 登记例外；Task 0–9 全关闭，执行日志见[整改计划 §10](../superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md)。遗留（不阻塞）：溯源真实来源链接（已按公开来源政策解锁，见 HANDOFF v3.3 §2.3） |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告。设计输入已备：知识库第二截面登记经营分析会四体系/月度周期蓝本与月报可视化实例（借鉴 #20/#22/#24，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）；AR 应收信用子域知识（科目/口径/账龄五桶/催收与信用规则，借鉴 #26，[FinBoss 评估册](../knowledge-base/02_research/synthesis/2026-09-19-finboss-assessment.md)——整理性质，行业参考值待溯源） |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked** | 公开 C 级 + 数据授权 | 历史工作包经统一计划重新纳入 I 轨；E2 数据扩张不是硬前置 |
| R2' | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked** | U4 + U8 + U09/O05 | D/K 完成证据可补充，但不是硬依赖；无证据项默认 hold |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

## 唯一完整 To-do 与执行队列（严格串行）

截至 2026-09-26：**10 项，已完成 0 项，进行中 1 项，排队 5 项，阻塞 4 项**。阻塞项仍保留在本队列中；队首若遇阻，停止并报告解除条件，不切换到后续项。状态表、工作包和历史文档是证据/规格，不构成第二份待办。

1. **[进行中] UX 可见性与全站验收关闭**（工作包见状态表2b）：完成剩余路由/API/页面数据一致性、五态×390/1024/1440 视口矩阵、缺口与下钻验收，运行 Gate 5 干净 SHA 全链和 CI。深链批次一至三已完成（批次三见 `cef0c362`）；不可写入或清理常驻 `flow`。意外测试批次未经用户授权维持原状。
2. **[排队] 公开财报 C 级归因、原件复核与抽取修订**（工作包见状态表3）：处理已确认42项异常后的109项口径疑点、JDL 200 格原件复核、抽取器修订；保留原始值及证据，任何结论可追溯。
3. **[阻塞] U04 解析器适配与独立留出验证**（工作包见状态表1'）：先支持「合并及公司」标题与页码区间参数化；对旧三样本做回归，再按已冻结协议对小米2026H1、阿里FY2027Q1做首次独立验证。解除条件：适配完成且留出资料/Oracle 具备；新留出首跑前不得调参。
4. **[排队] C 级质量基准与 Go/No-Go**：依赖第2、3项；重跑 L1 并归档机器结果。`1794/1794` 仅表示登记覆盖，不代表准确性通过。
5. **[排队] P3 真实数据、来源与行业扩张**（工作包见状态表3b）：修复/替换 ZTO 乱码文本层并完成抽取、勾稽、页锚、API/UI验证；复核阿里分部序列；C1 只接纳真实财报原件。
6. **[排队] 第二代静态知识 release 与战略重基线**（工作包见状态表K）：按已批准 K0–K6 完成 Davybase 图片批次验收、非微信图片覆盖、稳定15:00 Obsidian Git 截面、来源基线与知识资产、sealed candidate、战略影响评估、用户正式裁决、原子激活和独立复验。完成用户裁决前 `CURRENT_RELEASE` 不变。
7. **[阻塞] `rnd_exp` 官方依据核验**：解除条件为取得《应用指南汇编 2024》原文；原件到手后再核验，当前登记值不视为已确认。
8. **[阻塞] U09/O05 授权内部试点**（工作包见状态表R1）：依赖公开 C 级 Go 与内部数据授权；未授权前不接入真实企业数据。
9. **[阻塞] U10 V1.1 证据决策**（工作包见状态表R2'）：依赖 U04、U08、U09/O05 的证据包；U08 已完成，其余证据未齐时不得作通过结论。
10. **[排队] 内部月度工作台与四级真实周期验收**：依赖 C 级通过、内部授权和工作台可用；完成连续3个真实月度周期、同输入人工基准、逐周期盲评和20%工时门槛。不得以模拟数据替代。

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
