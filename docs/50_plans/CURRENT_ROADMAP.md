---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 1.9
created_at: 2026-09-12
updated_at: 2026-09-25
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一执行入口）

> 本页只维护顺序、依赖、状态与证据链接；详细步骤在各工作包。全仓唯一可执行总计划——历史计划均已 superseded。

唯一详细执行合同为 [FLOW 统一完整实施计划](../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md)。
本页决定“现在是什么状态”，详细计划决定“如何实施”；两者不得建立第二套状态。

## 顺序与状态（2026-09-24 对 `7e252cb` 核对；前次为 2026-09-17 v1.7）

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **blocked(外部到料)** — 可并行 | 独立会话人力 | HANDOFF §0：oracle 需人工录入 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 2a | [大麦物流完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **completed** | 已批准规格；不依赖公开 C 级 | D1–D3 全交付（A1–A4/B1–B3/C1–C3）：`DAMAI.SYN` 独立身份、正式审核链、原子幂等 seed、发行包零漂移、verify 19/19、八页面 E2E 9/9（`make damai-demo-up` / `make test-damai-demo-e2e`）；C3 全量回归 17 门禁绿，CI 全绿于 `d701c1d`（run 36098674773）。合成数据只用于产品全链验证，不解除公开 C 级或真实企业门禁 |
| 2b | [大麦数据后的剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **blocked** | 大麦 D3 completed（已达成，可领取） | 只承接导出审计、真实来源跳转、经分专员工作流首页、固定下钻、报告渐进披露和治理折叠；既有前端一致性 Task 0–9 不重做 |
| K | [第二代静态知识刷新与战略重基线](work_items/KNOWLEDGE--refresh-v2.md) | **active** | 批准规格；跨三仓库 | Task 0/preflight 已完成；K0–K6 待执行。可与 D 轨在不重叠文件上并行；战略激活与 D3 文档关闭必须串行；用户裁决前 `CURRENT_RELEASE` 不变 |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **blocked(用户裁决)** | S01 关闭 ✓ | **T09 已交付**：L0 1454/1454 + L1 页级答案集 98.9%（1775/1795，strong 972/weak 803）且锚失效/值不一致双 0（`accuracy_benchmark.py --level L1`）；余项=独立盲评与 holdout 抽签（需用户/第三方） |
| 3a | [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | — | B3 溯源 95.5% 行项目带页锚（迁移 0029 + 导入/API/前端）；B4 supersedes 链 + 差异脚本；B5 只读 MCP 三工具（token fail-closed）；B6 确定性差异说明起草 |
| 3b | [数据扩张、行业基准与 10× 性能基线](work_items/PUBLIC--data-expansion-benchmarks.md) | **active** | 性能基线 ✓；扩张待外部财报 | G2 完成：10×（1034→10340 行）P95 明细 6.2ms/检索 0.97ms/聚合 1.11ms（`perf_baseline.py`）；C1 扩张需真实财报到料 |
| 3c | [AI 问数 v1 与评测集](work_items/PUBLIC--ai-qa-v1.md) | **completed(v1)** | — | 确定性检索引用 QA + 94 问评测集（60 数值 + 34 拒答）命中率 100%、拒答零误答（`ask_facts.py` / `generate_qa_eval.py`）；LLM 通道与 v2/v3 另行裁决 |
| 3d | Web 前端一致性整改（信息架构/设计 token/组件库/五态/响应式） | **completed** | — | P0–P3 五批：`fe61b5c`（F2 token+值漂移）→ `8fa13a6`（生产构建门禁+溢出修复）→ `53ef2eb`（数据态门禁+触控+溯源交互）→ `defd823`（PageState+FlowDataTable+两页迁移）；P4–P5 四批（2026-09-18）：`0c4c45a`（metric-library 深度迁移）→ `b7b4257`（investigations 详情）→ `3089472`（Task 8 切片）→ `9cf8cb3`/`02c11ea`（frontend-states 状态门禁+60 图状态矩阵归档）；门禁矩阵 390/1024/1440 × 数据态 × 加载/错误/403，生产 e2e 69/69、单测 86/86、lint 1 登记例外；Task 0–9 全关闭，执行日志见[整改计划 §10](../superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md)。遗留（不阻塞）：溯源真实来源链接（已按公开来源政策解锁，见 HANDOFF v3.3 §2.3） |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告。设计输入已备：知识库第二截面登记经营分析会四体系/月度周期蓝本与月报可视化实例（借鉴 #20/#22/#24，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）；AR 应收信用子域知识（科目/口径/账龄五桶/催收与信用规则，借鉴 #26，[FinBoss 评估册](../knowledge-base/02_research/synthesis/2026-09-19-finboss-assessment.md)——整理性质，行业参考值待溯源） |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked** | 公开 C 级 + 数据授权 | 历史工作包经统一计划重新纳入 I 轨；E2 数据扩张不是硬前置 |
| R2' | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked** | U4 + U8 + U09/O05 | D/K 完成证据可补充，但不是硬依赖；无证据项默认 hold |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

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
- 详细步骤只从 `FLOW-PLAN-INTEGRATED-EXECUTION-20260924` 领取；旧详细计划均为历史证据，不按其空复选框恢复任务；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
