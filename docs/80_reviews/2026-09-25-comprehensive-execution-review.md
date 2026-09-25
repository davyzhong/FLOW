---
doc_id: FLOW-REV-COMPREHENSIVE-20260925
title: 全计划执行综合 Review（ZCode 审计 × 独立 Review 合并）
doc_type: review
status: open
version: 1.0
created_at: 2026-09-25
updated_at: 2026-09-25
last_reviewed_at: 2026-09-25
owner: FLOW
subject_ref: FLOW-PLAN-EXECUTION-CONVERGENCE-20260925
findings: [l1-demo-closed, resident-db-empty, audit-branch-ci-unverified, u4-not-comparable, c-level-exit-gated, p3-ingestion-pending, knowledge-release-reconcile, project-state-drift]
applies_to: repository
knowledge_release: flow-knowledge-2026-09-12.1
---

# FLOW 全计划执行综合 Review（合并版）

> 本报告合并两份独立审计：ZCode 会话审计（2026-09-24 晚，基于提交链/CI/数据库实况）与独立 Review（2026-09-25，基于 `bdc57a9`/`f62cf8e` 双分支）。合并前对全部关键断言做了二次核实（CI run 号、工作包状态、数据库行数、E2E 证据均逐一验证）。两份报告的结论分歧处已在正文标注裁决与依据。

## 0. 合并结论（先说）

**项目有重大实质进展，但整体计划未完成、最终目标未达成。**

- **大麦物流全财年演示线（L1）已完整交付并关闭**：A1–A4 → B1–B3 → C1–C3 串行全绿。最终 completed SHA `75fb2f1` 17 jobs 全绿（run `36101860056`；metrics-known-answers 首跑为 Docker Hub 瞬断 flake，重跑即绿），文档收尾 SHA `f62cf8e` 亦绿（run `36105604310`）。实测证据：verify 19/19、八页面 E2E 9/9（隔离栈+Playwright 38s）、二次 seed 全表零增长、发行包零漂移、数据合同 8/8。**它证明的是模拟数据下的全产品流程可用，不等于真实/公开报告质量验收。**
- **ZCode 前次审计的「CI 五连红 / 工作包未关单 / m6 失败清单」已被夜班会话修复**（`307300b` 替换不可达的 quay.io/minio 镜像、`75fb2f1` 关单、`85d7aa5` 文档治理），本报告据此更新。
- **仍未达成的三件事**：①审计分支（`bdc57a9`）同 SHA CI 仍红（run `36024558891` failure，同一 minio 类基座问题或待重跑）；②常驻开发环境数据库仍为 0 行——演示数据只在隔离栈验证，未对用户日常栈执行 `damai-demo-seed`；③C 级出口三件套缺两件（AI 交叉评、holdout 抽签——均需用户发起非实现方会话）。
- 项目状态文档（PROJECT_STATE/ROADMAP/HANDOFF 与两分支台账）仍未统一（详见 §3 缺陷 1/2）。

## 1. 完成度总表（五条执行线 × 七 Gate，验证后状态）

| 线/Gate | 内容 | 状态 | 关键证据与缺口 |
|---|---|---|---|
| L1 大麦演示线（=D1/D2/D3） | 全财年合成数据全链 | ✅ **完成并关单** | `75fb2f1` 17 jobs 绿 + `f62cf8e` 绿；工作包 `DAMAI--full-year-demo.md` status: completed v1.1；HANDOFF §2.5 全证据（verify 19/19、E2E 9/9、零漂移、U8 非破坏升级 PASS）。缺口：常驻栈未 seed（见 §3 缺陷 3）；工作包正文仍残留「不要灌数」旧语句（见 §3 缺陷 4） |
| L2 Oracle 录入线（=U4 前置） | 三样本独立转录 | ✅ 完成 | zto（`4acc1c3`）+ tencent（`e8f2624`）+ sf_2026h1（Kimi 夜班，SHA `16cf22eb…bf69`，8 项勾稽闭合）；key_items 精确值升级并登记哈希 |
| U4 独立全行验证 | 首跑可比性 | ❌ **未通过** | 三样本首跑 199 行全部 `not_comparable`（`cn_ashare_table` 不适配「合并及公司」合版标题）；系统正确显式降级、无伪造、失败全留档（holdout_runs/2026-09-24）。修复后须**新增独立留出样本**，原三份转为回归集，不得当泛化验收 |
| L3 公开模块 C 级出口 | 三件套 → Go/No-Go | ⚠️ **1/3 完成** | 10 条抽取候选修正未见完成提交（L1 记录已更新至 1794/1794，但覆盖率≠交叉审阅通过）；AI 交叉评、holdout 抽签需用户开非实现方会话。三件套齐 → Go/No-Go 裁决 → 解锁 T13 |
| L4 公开数据扩张 | 9988 分部 + zto + 溯源 | ⚠️ **大部分完成** | 阿里 FY2019–FY2026 分部序列 ✅（勾稽闭合）；zto 中报已归档（SHA `75e98464`）但 pypdf 乱码需换文本层后端、**未入库**；溯源真实链接仅完成设计输入（半页，待评审实现） |
| K 知识刷新 v2（Gate K） | 第二截面+重基线 | ⚠️ **状态不一致，未确认收口** | M2 激活（`962b651`）用户已追认、`CURRENT_RELEASE` 生效；但两分支路线图对后续收尾描述不同，「封存候选→影响评估→原子激活→独立复验」链条缺一致完成凭证；Task 10 三仓库收尾证据待核实 |
| U 剩余体验收口（Gate U） | 导出审计/专员工作流 | ❌ 未开始（21 项） | ROADMAP 顺序 2b blocked（承接导出审计、真实来源跳转等） |
| G0 基线恢复 / 项目状态文档 | 门禁+状态统一 | ⚠️ 门禁 PASS（278 docs 0 errors），**状态文档未统一** | 见 §3 缺陷 1/2 |
| 最终目标（D052–D054） | 内部工作台 → 四级验证 | ❌ 未达成 | 链条：C 级出口 Go/No-Go（阻塞）→ U9 数据授权（未启动）→ T13 → 四级验证。模拟数据不替代真实质量门槛 |

## 2. 完成度量化

- **工程维度：约 80%**（L1 全绿、L2/L4 完成、D3 关单；剩 U Gate、L3 两件、zto 入库、U4 修复线）
- **可验收维度：约 60%**（审计分支 CI 红、常驻栈无数据、C 级出口证据不足、状态文档分裂拉低）
- **战略目标维度：约 50%**（公开模块「先行成熟」接近但差最后验证闭环；内部工作台与四级验证未开始——这是设计内的 gated，不算执行偏差）

## 3. 错误与缺陷清单（合并去重，均经核实）

**错误（技术事实）**

1. **审计分支 CI 红**：`bdc57a9` run `36024558891` failure，基座问题（minio 类镜像拉取 unauthorized）与实施分支已修的同根（实施分支修复为 `307300b` 换 bitnamilegacy 镜像；审计分支需同款修复或 rebase）。
2. **U4 首跑全量不可比**：三样本 199 行 `not_comparable`；修复项=合版标题支持+页码区间参数化，且修复后需补独立留出样本。
3. **zto 文本层乱码**：pypdf 乱码、pdftotext 正常，接入前需换后端，数据未入库。
4. （已修复，留档）实施分支 minio 镜像不可达曾致五 job 连红，`307300b` 修复后 17 jobs 全绿。

**缺陷（治理/文档）**

1. **状态文档分裂为三个平面**：main 的 PROJECT_STATE 停在 09-15（迁移头 0028、S01 active）；实施分支 HANDOFF 已更新大麦交付全证据；audit 分支 EXECUTION_TODO 含 U4 首跑与 P 系列进展。读者按任一单一文档都会得到错误的全局状态。
2. **权威指针不一致**：两分支 `CURRENT_ROADMAP` 对知识刷新收尾与大麦状态的描述不同；主路线图未同步。
3. **工作包文档自相矛盾**：大麦工作包 frontmatter completed，正文残留「尚未完成、不要灌数」旧语句——后续 Agent 可能按过时指令执行。
4. **EXECUTION_TODO 大麦节未勾选**（旧编号 Task 4 slice-2～Task 9 六个空框），与实施分支完成事实不同步；台账不能单独当可靠全项目状态表。
5. **计划 checkbox 登记失守**：统一执行计划 105 个 checkbox 0 勾选（工程完成但书面进度 0%），「完成即登记」协议未被执行——已由 v2.4 §0 与 HANDOFF §2.5 部分弥补，但 Gate 层仍未登记。
6. **本地工作区两项未提交变更**：`HANDOFF.md` 已修改、`services/api/tests/security/test_route_policy_registry.py` 未跟踪——合并/清理前须确认归属，不得覆盖（本报告提交时未触碰）。

## 4. 下一步建议（按风险与依赖排序）

1. **审计分支 CI 修复**：rebase 或同款修复 minio 镜像问题，让 `bdc57a9` 上的完整门禁实际跑完——在此之前审计线（oracle/数据扩张/迁移链 0030）不得称为已验收。
2. **常驻环境灌库演示**：对日常开发栈执行 `make damai-demo-seed` + `verify`（或将 `damai-demo-up` 作为标准演示入口），让「八页面全满」从隔离栈事实变为用户可见事实；同步清掉工作包正文残留旧语句。
3. **状态统一（一次性对账）**：以实施分支 HANDOFF §2.5 + audit 分支 EXECUTION_TODO 为两源，刷新 main 的 PROJECT_STATE/ROADMAP/HANDOFF，合并两分支成果为单一当前状态；EXECUTION_TODO 大麦节勾选对齐。
4. **U4 修复线**：合版标题 + 页码区间参数化 → 三样本回归 → **新增独立留出样本** → 盲测。
5. **C 级出口收口**：10 条候选修正落地 → 用户开非实现方会话执行 AI 交叉评 → holdout 抽签 → Go/No-Go 裁决。
6. **K 刷新收尾核实**：Task 10 三仓库证据核实后转 completed，统一 `CURRENT_RELEASE` 叙述。
7. **之后再推进** U9 授权 → T13 内部工作台 → 四级验证；U10（用户倾向 go）按预置决策包在 U4 修复完成后启动。

## 5. 两份源报告的差异裁决记录

| 分歧点 | ZCode 审计（09-24 晚） | 独立 Review（09-25） | 裁决（以核实为准） |
|---|---|---|---|
| L1 状态 | 「C3 ~20%，CI 五连红，未关单」 | 「分支已完成，CI success」 | **独立 Review 正确**：夜间会话完成修复+关单+CI 绿（`307300b`/`75fb2f1`/`f62cf8e`）；ZCode 审计快照过时 |
| 验收 run 号 | 未及引用 | run `36105604310` | 补充核实：关单 SHA `75fb2f1` 的验收 run 为 `36101860056`（success），`f62cf8e` 为 `36105604310`（success）——两说并存，均为绿 |
| 常驻栈数据 | 0 行 | 未提及 | 维持 ZCode 发现：**常驻库仍 0 行**（演示在隔离栈验证），合并报告列为缺口 |
| 登记纪律 | 「105 checkbox 0 勾选」 | 未提及 | 维持 ZCode 发现：Gate 层登记仍缺失，HANDOFF/v2.4 §0 为部分弥补 |
| C 级出口 | 「三件套缺 2 件等用户」 | 「L1 1794/1794 ≠ 验证通过」 | 一致，合并表述：覆盖率≠交叉审阅；三件套 1/3 |
| HANDOFF 更新 | 「未纳入 9-24 决策」 | 「待补」 | 已过时：`f62cf8e` 已更新 HANDOFF（含 §2.5 证据），维持「9-24 双线决策叙述已并入」的核实结论 |
