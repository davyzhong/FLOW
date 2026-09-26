---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 4.1
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

> 2026-09-26 更新：常驻开发库受控恢复已完成，备份后幂等seed、不清库/不迁移，verify19/19两次通过；dashboard API 200、8卡、趋势12/12、2条findings，仍degraded；财报2份、发布快照1、冻结候选12，静态覆盖37/40与40/40。Next开发origin配置修复后常驻3000端口只读页面6/6通过，未发布比较值现显示原因标签；批次/调查/财报/经营快照可见。正式报告产物历史仍为空，数值单位化格式审计待处理。验收器历史版本计数修复并有回归测试。隔离Damai全旅程verify19/19、E2E9/9；Gate1全路由矩阵、其他页面缺口与深链批次三仍未关闭。CI按最新SHA核验。

> **本页是全仓唯一主线**：既维护状态真相，也维护执行队列。2026-09-25 用户裁决（2A）后不再存在第二份「唯一」文档：EXECUTION_TODO、整合总计划、统一完整实施计划与执行收敛计划均已归档为历史/参考，状态与任务只以本页和工作包为准。详细验收步骤在各工作包与参考规格。

> **测试库安全状态**：共享库误清根因已修复并于 `b60c51b` 验证：测试默认使用
> `flow_test`，常驻 `flow` 零污染。仍须保留该保护，不得将本地破坏性测试指向常驻库。

## 顺序与状态（2026-09-26 对远端 main `6591e148` 核对；后续提交 CI 状态按 SHA 单独核验）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked(解析器适配 + 新留出)** — 可并行 | oracle 已到齐 | 2026-09-24 首跑 199 行均 `not_comparable`；先支持「合并及公司」标题与页码区间提示，再回归并另取独立留出 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 2a | [大麦物流完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **completed** | 已批准规格；不依赖公开 C 级 | D1–D3 已集成 main `e22d193`，CI run `36137591750` 17/17 success；隔离栈 verify 19/19、八页面 E2E 9/9、重复 seed 零增长、发行包零漂移。**常驻开发库已装载（G2 完成 2026-09-25）**：用户裁决演示数据全部入库，集成后 main 上 verify 19/19、页面可见；合成数据不解除公开 C 级门禁 |
| 2b | [大麦数据后的剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **active（Gate 1全路由干净SHA复验待完成；Gate 2静态事实完成；Gate 3部分完成；Gate 4批次历史clean-SHA通过、其余下钻待完成；Gate 5待本轮提交SHA CI）** | G2 ✓；用户于 2026-09-26 批准实施 | 常驻库备份后幂等恢复，verify19/19两次，重复seed零增长。Dashboard API 200（8卡、趋势12/12、2 findings，degraded）；常驻3000端口只读页面6/6，数据批次、调查Finding、财报及经营快照可见。未发布比较值已增加显式原因标签（Web Vitest 134/134）；正式报告产物历史为空，比率/金额格式待审计。验收器最新财报版本计数修复并有2项回归测试。隔离全旅程verify19/19、E2E9/9。其余页面缺口、全量Gate1与深链批次三待处理。见[工作包](work_items/UX--post-damai-experience-closeout.md)。 |
| K | [第二代静态知识刷新与战略重基线](work_items/KNOWLEDGE--refresh-v2.md) | **active** | 批准规格；跨三仓库 | Task 0/preflight 已完成；K0–K6 待执行。可与 D 轨在不重叠文件上并行；战略激活与 D3 文档关闭必须串行；用户裁决前 `CURRENT_RELEASE` 不变 |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **blocked(归因、补证与裁决)** | S01 关闭 ✓ | 独立交叉评已完成（[结果](../80_reviews/ai-cross-review/results/gpt-6-astra-2026-09-25.md)）：1,530 格中42异常、109存疑、200因JDL乱码无法完整核验；待原PDF逐项归因/订正。1794/1794仅为登记覆盖口径，不等于通过 |
| 3a | [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | — | B3 溯源 95.5% 行项目带页锚（迁移 0029 + 导入/API/前端）；B4 supersedes 链 + 差异脚本；B5 只读 MCP 三工具（token fail-closed）；B6 确定性差异说明起草 |
| 3b | [数据扩张、行业基准与 10× 性能基线](work_items/PUBLIC--data-expansion-benchmarks.md) | **active** | 性能基线 ✓；扩张待外部财报 | G2 完成：10×（1034→10340 行）P95 明细 6.2ms/检索 0.97ms/聚合 1.11ms（`perf_baseline.py`）；C1 扩张需真实财报到料 |
| 3c | [AI 问数 v1 与评测集](work_items/PUBLIC--ai-qa-v1.md) | **completed(v1)** | — | 确定性检索引用 QA + 94 问评测集（60 数值 + 34 拒答）命中率 100%、拒答零误答（`ask_facts.py` / `generate_qa_eval.py`）；LLM 通道与 v2/v3 另行裁决 |
| 3d | Web 前端一致性整改（信息架构/设计 token/组件库/五态/响应式） | **completed** | — | P0–P3 五批：`fe61b5c`（F2 token+值漂移）→ `8fa13a6`（生产构建门禁+溢出修复）→ `53ef2eb`（数据态门禁+触控+溯源交互）→ `defd823`（PageState+FlowDataTable+两页迁移）；P4–P5 四批（2026-09-18）：`0c4c45a`（metric-library 深度迁移）→ `b7b4257`（investigations 详情）→ `3089472`（Task 8 切片）→ `9cf8cb3`/`02c11ea`（frontend-states 状态门禁+60 图状态矩阵归档）；门禁矩阵 390/1024/1440 × 数据态 × 加载/错误/403，生产 e2e 69/69、单测 86/86、lint 1 登记例外；Task 0–9 全关闭，执行日志见[整改计划 §10](../superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md)。遗留（不阻塞）：溯源真实来源链接（已按公开来源政策解锁，见 HANDOFF v3.3 §2.3） |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告。设计输入已备：知识库第二截面登记经营分析会四体系/月度周期蓝本与月报可视化实例（借鉴 #20/#22/#24，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）；AR 应收信用子域知识（科目/口径/账龄五桶/催收与信用规则，借鉴 #26，[FinBoss 评估册](../knowledge-base/02_research/synthesis/2026-09-19-finboss-assessment.md)——整理性质，行业参考值待溯源） |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked** | 公开 C 级 + 数据授权 | 历史工作包经统一计划重新纳入 I 轨；E2 数据扩张不是硬前置 |
| R2' | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked** | U4 + U8 + U09/O05 | D/K 完成证据可补充，但不是硬依赖；无证据项默认 hold |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

## 执行队列（唯一主线；2026-09-25 用户四项裁决后重整）

> 已完成：G1 审计线 CI 修复（`96010a2`）→ 大麦线合并（`e22d193`）→ 审计线合并（`7a230af7`）→ G2 常驻开发库装载（verify 19/19）→ 状态统一（`6dac3b2`）。三条工作分支已全部并入 main，无独有提交。以下按依赖顺序：

0. ~~修复测试数据库隔离~~ **已完成**（`b60c51b`）：conftest 默认切 `flow_test`，实证常驻库零污染。
1. **C 级交叉评归因与原件复核**（上表3，进行中）：42 个确认异常已全部归因为真实抽取错误（`4111f6a`：19 项空白/破折号误借邻年值、22 项京东物流权益变动表误分类、1 项阿里 FY2023 前期商誉减值漏抽）；剩余：109 个口径疑点待裁决、JDL 200 格重核（英文版已冻结 `b161fff`，输入条件具备）、抽取器修订（实现方职责）。只在归因后修订新版本订正记录，保留原值与证据。
2. **U4 解析器修复与真正的新留出**（上表1'）：新留出双样本已冻结并完成独立 oracle 录入（`926af825`：小米 2026H1 + 阿里 FY2027Q1，抽签记录见 [holdout-lottery-2026-09-25](../../validation/financial_reports/holdout-lottery-2026-09-25.md)）。剩余：`cn_ashare_table` 支持「合并及公司」标题与页码区间参数化；旧三样本回归；新留出首跑前禁止适配/调参。
3. **重新跑质量基准并完成 C 级 Go/No-Go**：依赖必要修订、U4新留出首跑和盲测；重跑L1并归档机器结果。交叉评与抽签均不单独构成通过，`1794/1794` 只表示已登记覆盖口径。
4. **全站超链接化（深链下钻）**（**active**，用户 2026-09-26 确认）：按[实施计划](2026-09-26-ui-deep-link-implementation-plan.md)三批推进。**批次一、二已完成本地验收并推送 `7976691`**：六页接收端 + S/M 级下钻；新增指标条目、MetricSnapshot、AnalysisRun 只读详情 API 和授权血缘约束；Copilot 引用定位；公开覆盖矩阵报告链接映射。API/安全51/51、Web单测133/133、深链 Playwright15/15、typecheck、合同生成、文档M1/M6门禁通过；该 SHA 隔离 Damai 全旅程 verify19/19、E2E9/9。GitHub CI run `36225466153` 尚待最终核验。**批次三尚未开始**（原文/源记录查看器、冻结产物回链、ManagementWatchItem 关联等），计划不可关闭；Gate 1全路由数据/页面覆盖矩阵仍待完成。详见[实施计划](2026-09-26-ui-deep-link-implementation-plan.md)和[可链接性审计](../80_reviews/2026-09-26-ui-linkability-audit.md)。
5. **大麦数据可见性与剩余 UX 收口**（上表2b，用户已批准）：Gate1初始矩阵绑定`main@3ff95115`+dirty overlay，非干净提交验收。FY2025工作台契约、Gate2覆盖FY2025 37/40与FY2026 40/40、OCF及矩阵比较策略已完成；深链批次一、二已交付，隔离全旅程verify19/19、E2E9/9。常驻开发库2026-09-26已备份后幂等恢复（无清库/迁移），verify19/19两次；Next开发origin修复后常驻只读页面6/6通过，另确认批次、Finding、财报和经营快照显示。正式报告产物历史为空。仍需Gate1全路由响应矩阵、Gate3/4其余页面缺口与下钻、深链批次三、Gate5最新提交SHA总CI复验。详细状态见工作包。
6. **P3 数据与溯源接入**（上表3b）：修复/替换ZTO文本层，完成抽取、勾稽、页锚及API/UI链路测试；评审并实现真实来源链接；复核阿里分部序列在main的来源和可见性。
7. **知识 release 收尾**（上表K）：完成K0–K6，核对M2用户追认、`CURRENT_RELEASE`、sealed candidate/激活记录、Task 10三仓库证据和独立复验；用户裁决前不切指针。
8. **外部阻塞项**：取得《应用指南汇编2024》原文后核验rnd_exp；公开数据扩张C1等待真实财报。不得用合成样本替代。
9. **内部工作台与真实周期验证**（上表4/5，gated）：仅在C级Go及内部数据授权满足后启动；连续3个真实月度周期对同输入人工基准、盲评与工时门槛验收；U10按证据包裁决，不由模拟数据单独解锁。

裁决记录（2026-09-25 晚，用户四项裁决）：①分支整合归本主线串行执行；②四份「唯一」文档合并为本页唯一主线（2A）；③AI交叉评原由助手准备、用户发起，后经用户追加委托由助手安排未参与实现的隔离AI审查，结果见本页；④holdout候选由AI可复现随机抽签并归档（4A），数据冻结与oracle另行执行。

战略方向（2026-09-13，D052–D054）：企业内部月度财务经营分析工作台为最终产品，公开财报模块独立并先行成熟共享底座；顺序为 U8 → 边界重构 → 公开模块 C 级出口 → 内部工作台 → 四级验证。详见[战略重构设计](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)。

2026-09-24 补充：大麦合成发行版是“系统完整性验证工具”，知识刷新是“静态知识
维护轨”，两者可在公开 C 级外部门禁等待期间推进；二者均不改变 D052–D054 的
真实数据验收顺序，也不能代替独立 oracle、holdout 或真实企业三周期验证。

并行动作（非阻塞）：

- rnd_exp 官方核验（待《应用指南汇编 2024》原文，复核暂登记 4301）。
- 知识库第二截面增量扫描完成（2026-09-17，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）：四分类真新增 203 篇（HIGH 138）+ Davybase 图片知识化附录层 915 篇（微信全库批次进行中）；借鉴附录 #20–#24 已登记并入统一计划输入。
- 指标库行业包 v1.2 完成（2026-09-17，借鉴 #21）：16 行业参考包 + 通用指标新增流动资产率 + 基准增强（现金流量比率 ≥1、产权比率 100%/200%），经派生脚本 `finalize_metric_dictionary_v1_1.py` 再生成（幂等）零迁移落地；前端指标库新增「行业参考包」tab。O-01 四元素设计输入登记于 `docs/40_specs/metrics/README.md`。
- 竞对五维对比矩阵完成（2026-09-17，[五维矩阵](../competitive/2026-09-17-five-dimension-matrix.md)）：整合 C01–C20/方法矩阵/前端五轮调研为功能/界面/体验/性能/交互统一视图，FLOW 现状（defd823 实测）对标 12 家代表产品；结论=主线不调整，O-01/O-02（语义暴露+复算管线）升级为 AI 问数 v2 必须项，指标库行业包（#21）为低成本候选增项。
- O-01/O-02 地基落地（2026-09-17，AI 问数 v2 必须项第一批）：`GET /api/v1/metric-library/semantic-context`（对象/维度/限定/值四元素语义上下文，引用携带 entry_id 回链口径）+ `POST /api/v1/metric-library/computation-proposals`（提议→程序复算：AI 只能提名治理字典 effective 指标，确定性沙盒在冻结报表事实上复算，缺口=结构化 refusal 绝不编造，审计走 JSONL 无新表）+ `GET /computation-inventory`（复算事实清单）。行动者=ai_analyst/analyst（metric_library.read），零 RBAC 矩阵变更；任意 AST 提议与 LLM 通道另行裁决。

## 纪律

- 任务领取/勾选/提交只用本页与工作包；模块可以维护不可领取的 workstream/backlog 视图，但不得形成第二份状态真相；每完成一阶段提交推送、CI 绿才算 done；
- 详细验收步骤在工作包与归档参考规格（原统一实施计划、执行收敛计划等，均已 archived）；旧详细计划均为历史证据，不按其空复选框恢复任务；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
