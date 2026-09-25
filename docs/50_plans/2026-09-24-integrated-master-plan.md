---
doc_id: FLOW-PLAN-INTEGRATED-MASTER-20260924
title: FLOW 整合总计划（多计划合一视图）
doc_type: plan
status: archived
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-25
owner: FLOW
depends_on: [FLOW-PLAN-CURRENT]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
decision_refs: [D052, D053, D054]
applies_to: planning
supersedes: []
superseded_by: FLOW-PLAN-CURRENT
---

# FLOW 整合总计划（多计划合一视图）｜2026-09-24

> **归档说明（2026-09-25，用户裁决 2A）**：全仓只保留一条主线——[CURRENT_ROADMAP](CURRENT_ROADMAP.md)（状态真相 + 执行队列）。本文不再作为执行依据或「唯一」文档，内容保留为历史与验收细节参考；任务状态以路线图为准。


> **定位（必须先读）**：本页是把仓库现存全部计划文档整合后的**内容与顺序视图**，
> 供用户与接手 Agent 一页看清"总共要做什么、谁先谁后、谁在等谁"。
> 按 `docs/50_plans/README.md` 纪律，**本页不是第二份总计划、不维护任务状态**：
> 状态真相仍以 [CURRENT_ROADMAP](CURRENT_ROADMAP.md)（唯一执行入口）、
> [EXECUTION_TODO](EXECUTION_TODO.md)（唯一活跃 TODO 台账）和各工作包为准。
> 若本页与上述文件冲突，以上述文件为准，并应修正本页。

## 1. 全部计划文档盘点（2026-09-24 实测）

| 文档 | doc_id | 整合前状态 | 整合后状态/处置 |
|---|---|---|---|
| `superpowers/plans/2026-09-07-unified-next-plan.md`（U1–U10） | FLOW-PLAN-UNIFIED-000 | archived | 不变（历史，已被 ROADMAP 取代） |
| `superpowers/plans/2026-09-09-operations-track-plan.md`（O 系列） | FLOW-PLAN-OPS-000 | archived | 不变（历史） |
| `superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md`（M0–M6） | FLOW-PLAN-MIGRATION-001 | completed | 不变 |
| `superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md`（S01 范围） | FLOW-PLAN-POST-U8-BOUNDARY-001 | active | 实质完成（S01 completed，ROADMAP 顺序 2）；保持 active 仅作范围参考，**待 S01 工作包正式归档时一并转 completed** |
| `superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md` | FLOW-PLAN-THREE-AGENT-PARALLEL-001 | active（漂移） | **本次修正为 superseded**（多 Agent 编排已被单 Agent 协议取代，HANDOFF §6/§7） |
| `superpowers/plans/2026-09-15-frontend-design-upgrade-proposal.md` | FLOW-PLAN-FE-DESIGN-UPGRADE-20260915 | active | 保持 active：阶段二剩 F-ExportAudit（用户明示搁置，领取前须先补规格）；阶段三 gated |
| `superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md` | FLOW-PLAN-FE-CONSISTENCY-REMEDIATION-20260916 | active（漂移） | **本次修正为 completed**（Task 0–9 全关闭，ROADMAP §3d 与计划 §10 执行日志为证） |
| `superpowers/plans/2026-09-18-static-knowledge-refresh...md`（K0–K6/S0–S3） | FLOW-PLAN-KNOWLEDGE-REFRESH-002 | active | M2 原子激活（`962b651`）已被用户 2026-09-24 追认；**关闭前待核实 Task 10 三仓库收尾证据**，核实后转 completed |
| `50_plans/CURRENT_ROADMAP.md` | FLOW-PLAN-CURRENT | active | 唯一执行入口，不变 |
| `50_plans/EXECUTION_TODO.md` | FLOW-PLAN-EXECUTION-TODO | current | 唯一活跃 TODO 台账，各会话共同维护（写入前先 pull），不变 |
| `HANDOFF.md` | FLOW-HANDOFF-STRATEGY-20260912 | current | 交接入口，v3.3（2026-09-19）；**待补 9-24 双线推进与 Q&A 决策** |
| `superpowers/plans/2026-09-24-damai-logistics-demo-data-implementation-plan.md`（在实施分支） | FLOW-PLAN-DAMAI-DEMO-20260924 | active | 当前主线执行计划 v2.4，见 §3 L1 |
| `superpowers/plans/2026-09-24-project-baseline-repair-implementation-plan.md`（在实施分支） | FLOW-PLAN-BASELINE-REPAIR-20260924 | active | Task 1 门禁修复、Task 2 状态刷新；Task 1 建议前置为大麦 A0 |

## 2. 战略锚点（不变）

D052–D054：企业内部月度财务经营分析工作台是最终产品；公开财报模块独立并先行成熟共享底座；
顺序 U8 ✅ → 边界重构 ✅ → 公开模块 C 级出口（当前 Gate）→ 内部工作台 → 四级验证。
2026-09-19 数据政策：研发期一律使用公开网络来源数据。2026-09-24 用户拍板：**大麦线与 oracle 录入线双线并行**。

## 3. 整合后的五条执行线

### L1 大麦物流全财年演示数据线（当前主线，分支 `codex/damai-logistics-implementation`）

目标：交付 `damai-logistics-demo-v1`——确定性、可重建、可幂等装载的合成数据发行版，
贯通导入/分析/指标/Finding/审核/冻结/发布/下载全链与八个主页面。
依据：规格 v1.5（approved）+ 计划 v2.4 + [半成品审查](../80_reviews/2026-09-24-damai-demo-partial-implementation-review.md) + [计划独立评审](../80_reviews/2026-09-24-damai-demo-plan-review.md)。

执行顺序（A→B→C 严格串行）：

1. **A0（评审新增前置项）**：baseline-repair Task 1 门禁修复 + ROADMAP 最小登记大麦工作包；
2. **A1** 红灯测试锁定全量数据合同（明细级 1,920/10,752/4,800）；
3. **A2** 明细生成器与 canonical 投影重构（40 客户×8 产品×6 区域，禁聚合成员）；
4. **A3** 财报独立身份 `DAMAI.SYN` + 正式审核链（禁直改 status、禁冒用 9988.HK）；
5. **A4** 静态发行包重建、零漂移（manifest 血缘 + README frontmatter）；**A4 完成前不做任何正式灌库**；
6. **B1** 事务化幂等 seed（AnalysisCycle 显式绑定 + 三类故障注入整体回滚；评审建议补"发布物失败"注入或显式排除说明）；
7. **B2** Finding/Evidence/Conclusion 状态机 + 冻结报告（≤5 个系统 Finding，其余为可追溯信号）；
8. **B3** 大麦 synthetic 指标覆盖数据集（API `dataset` 参数 + 前端切换，默认 public 不变）；
9. **C1** `damai-demo-build/seed/verify/up` 四命令 + 机器可读 receipt；
10. **C2** 八页面真实 E2E（含 `/data` 页面上传旅程；需明确是否进 CI 及证据留存方式）；
11. **C3** 全量回归 + 文档刷新 + 同一最终 SHA CI 全绿才算完成。

### L2 Oracle 独立录入线 → U4 首跑（与 L1 并行，独立会话执行）

- [x] zto_2026q1 录入（`4acc1c3`）；
- [ ] tencent_fy2025（282 页年报；AI 转录已授权 2026-09-24，须独立会话、只读 PDF 原文、不接触抽取器输出）；
- [ ] sf_2026h1（213 页半年报；同上授权）；
- [ ] 三样本齐 → manifest key_items 升级精确值 + 登记哈希 → **U4 独立全行验证首跑解锁**。
- 登记协议：[oracle-register](../../validation/financial_reports/oracle-register.md)（铁律：expected 值不得以抽取器输出回填）。

### L3 公开财报模块 C 级出口收口（当前战略 Gate）

证据链已就绪（T09–T12 交付：L0 1454/1454、L1 98.9%、溯源 95.5% 页锚、重述链、只读 MCP、
性能基线 10×、问数 v1 评测 100%/零误答、O-01/O-02 地基）。剩余三件套：

1. **10 条抽取错误候选修正**：2026-09-24 决策=按 AI 判断直接修正，逐条在订正层登记原值/新值/依据，保留审计痕迹；修完重跑双层基准并更新压力测试报告；
2. **AI 交叉评**：包已备（`docs/80_reviews/ai-cross-review/`），须用户开非实现方会话执行；
3. **holdout 抽签执行**：需用户/第三方。
三件套齐备 → **C 级出口 Go/No-Go 裁决** → 解锁 T13 与 T12 LLM 通道。

### L4 公开数据扩张线（可领取，非阻塞）

- 阿里 9988 分部披露抽取（六份 PDF 已归档，**用户已批准 2026-09-24**）；
- zto 样本公开渠道获取（**用户已授权寻找 2026-09-24**）；
- 溯源真实来源链接（公开数据政策已解锁：statement 溯源回链公开财报 URL + 前端浮层联动；先补半页设计输入再动工）；
- 公开管线扩公司面 → 抽取 → L0/L1 基准 → 冻结 → 重述链实战验证。

### L5 后续 gated 线（不主动领取）

| 项 | 阻塞条件 | 备注 |
|---|---|---|
| T13 企业内部工作台 | C 级出口 PASS + U9 数据授权（按 ROADMAP 顺序） | 设计输入已备（知识库第二截面、AR 子域、FinBoss 评估册） |
| U10 V1.1 证据决策 | U4 首跑 + U8 + U9 到齐 | 用户倾向 go（2026-09-24），届时按预置决策包启动 |
| AI 问数 LLM 通道 / 任意 AST 提议 | 用户另行裁决 | O-01/O-02 地基已就绪 |
| 合规尽调 G4（A5） | 未启动 | 阻塞 T13 与 MCP/LLM 开放 |
| rnd_exp 官方核验 | 待《应用指南汇编 2024》原文 | 复核暂登记 4301 |
| F-ExportAudit / 前端阶段三 | 用户明示搁置 / 阶段二组件依赖 | 领取前先补规格 |

## 4. 统一依赖顺序图

```text
L2 oracle 三样本 ──→ U4 首跑 ──┐
L3 三件套 ──→ C 级出口 Go/No-Go ──┼──→ T13 内部工作台 ──→ 四级验证
L1 大麦发行版 ──→（演示/试点底座，反哺 U09）┘
L4 数据扩张（并行，非阻塞）
U10：U4 首跑后按预置决策包；G4 合规：T13 前必须启动
```

## 5. 已确认决策记录（近两轮，执行时不得再争）

**2026-09-19**：无私有数据来源，研发期一律公开网络来源（A4 等外部材料前提作废）。

**2026-09-24 问答轮（8 项，详见 EXECUTION_TODO §五-b）**：双线推进；oracle AI 转录两份一次性授权；
M2 激活追认有效；10 条抽取错误按 AI 判断直修并登记订正层；前端遗留分支保留结案；
批准阿里 9988 抽取 + 授权寻找 zto 公开数据；U9 按顺序（C 级出口后）；U10 倾向 go。

## 6. 本次整合已修正的状态漂移

1. 三智能体并行计划：active → **superseded**（superseded_by: FLOW-HANDOFF-STRATEGY-20260912）；
2. 前端一致性整改计划：active → **completed**（Task 0–9 全关闭证据：ROADMAP §3d）；
3. 待核实：知识刷新计划（FLOW-PLAN-KNOWLEDGE-REFRESH-002）Task 10 收尾证据齐全后转 completed；
4. 待办：HANDOFF v3.3 尚未纳入 9-24 双线推进与 Q&A 决策，下次交接刷新时并入。

## 7. 统一执行协议

1. 单一 Agent、逐 Gate、串行执行；一个 Gate 一个 `codex/` 分支/独立 worktree；
2. 每 Gate：读批准规格 → 红灯测试 → 最小实现 → 目标测试 → 全链测试 → 独立规格审查 → 提交推送 → 等同 SHA CI 全绿；
3. 禁止 skip/xfail/弱化断言/删测试/关闭认证换绿；禁止用 docs/chore 提交标题掩盖业务代码；
4. 只承认目标 commit 与 CI head SHA 完全一致且 required jobs 全 success；
5. **计划沉淀铁律（2026-09-24 起，同步写入 AGENTS.md）：任何计划在执行前必须沉淀为带合法 frontmatter 的正式文档并通过 m1 门禁；范围或验收口径变化必须先更新计划文档并提交推送，再改代码；会话内口头计划不构成执行依据；**
6. 每完成一阶段，同步更新 ROADMAP/EXECUTION_TODO/PROJECT_STATE 并同 SHA CI 绿；
7. 冲突裁决顺序：用户最新明确指令 → D052–D054 → approved 规格 → PROJECT_STATE → ROADMAP/工作包 → HANDOFF → review/research → 历史计划与聊天记录。

## 8. 停机条件（任一出现即停，先修正再继续）

- 需要新增 schema/migration 或修改 CI/.env 而规格未批准；
- 为换绿而直改发布/审核状态、页面 mock、人工插入最终对象；
- 生成器、静态发行包、数据库三者不能对账；任一失败路径留下部分数据；
- 发现第二迁移头、跨企业可访问、AI 可发布/自批、恢复哈希不一致；
- 多会话共用检出造成基线错乱（发生过的坑：先 `git fetch && git status -sb` 再提交）。
