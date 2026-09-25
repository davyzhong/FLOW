---
doc_id: FLOW-PLAN-EXECUTION-TODO
title: 执行待办清单（已归档，并入 CURRENT_ROADMAP）
doc_type: navigation
status: archived
version: 1.2
created_at: 2026-09-24
updated_at: 2026-09-25
owner: FLOW
applies_to: repository
superseded_by: FLOW-PLAN-CURRENT
---

# 执行待办清单（已归档，2026-09-25）

> **归档说明**：2026-09-25 用户裁决（2A）要求只保留一条主线。本页全部活跃事项已并入 [CURRENT_ROADMAP](CURRENT_ROADMAP.md) 的「执行队列」一节；本文件不再维护、不再作为状态或任务依据，内容保留为历史记录。决策日志（§五-b）等原始记录不删除。
- 当前整改顺序与验收见[项目执行收敛与验收计划](2026-09-25-project-execution-convergence-plan.md)；本文件为唯一活跃 To-do 状态表。用户已要求后续执行工作直接在 `main` 顺序完成，不新建执行分支。
- 依据：D052–D054 战略、[综合执行 Review](../80_reviews/2026-09-25-comprehensive-execution-review.md)、[oracle-register](../../validation/financial_reports/oracle-register.md)。

## 一、oracle 独立录入线（解锁 U4 首跑）

- [x] zto_2026q1：四 key items + 25 行补充明细录入（`4acc1c3`；用户授权 AI 转录，登记 §1a）
- [x] tencent_fy2025：key items 录入（282 页年报；ZCode 录入 2026-09-24，oracle/tencent_fy2025.yaml）
- [x] sf_2026h1：四 key items + 127 行补充明细录入（213 页半年报；Kimi 夜班会话 2026-09-24，oracle/sf_2026h1.yaml SHA `16cf22eb…bf69`，8 项勾稽恒等式闭合）
- [x] 三样本齐后：manifest key_items 升级精确值 + 登记哈希（三份 key_items_precise 段，2026-09-24）
- [x] **U4 首跑（2026-09-24）**：三样本 199 行全部 not_comparable，系统现状对未适配版式全部显式降级（无伪造输出）；原始失败全量保留于 holdout_runs/2026-09-24/ 与 holdout-results.md

## 二、大麦物流实施线（damai-logistics-demo-v1）与常驻栈可见性

- [x] L1 演示数据实施包已集成 main：合并提交 `e22d193`，同 SHA CI run `36137591750` 17/17 success；verify 19/19、八页面 E2E 9/9、二次 seed 零增长、发行包零漂移。最新 main `370fd1f` 仅含自动更新的 README 截图。
- [ ] 常驻开发栈数据可见性：先只读确认环境、行数、备份/恢复、seed 覆盖语义；在确认不覆盖用户数据且目标为开发栈后运行正式 seed/up + verify；八页面验收并留证。隔离栈的 E2E 不可代替此项。
- [x] 两条工作线已纳入 main：审计/G1 `96010a2` CI run `36129442008` 17/17 success；大麦通过普通合并 `e22d193` 集成，CI run `36137591750` 17/17 success；schema 冲突核对无大麦迁移，main migration 0030 保留。

## 三、U 系列财务轨（主线性任务）

- [x] U1–U7 全部 done
- [x] U4 首跑（2026-09-24，原始失败全保留，见 holdout-results.md；修复后三样本降为回归集并须补新留出候选）
- [ ] U4 修复线：cn_ashare_table 支持「合并及公司」合版标题 + 年报页码提示区间参数化（修复后跑回归，不计入留出泛化结论）
- [x] U8 收口：真实存储完整旅程、HTTPS 部署拓扑、结构化日志、统一部署验收已正式关闭；审计分支旧待办状态须在集成状态文档中纠正（交付证据见 `docs/operations/u8-closure-baseline.md` 与实施分支 HANDOFF）。
- [ ] U5/U10：按 D053 重新裁决范围（U10 用户倾向 go，2026-09-24；依赖 U4+U8+U9 到齐后启动）

## 四、O 系列经营轨

- [x] O1–O4 全部 done（四样本泛化：顺丰/腾讯/菜鸟/阿里）
- [x] 阿里 9988 分部披露接入（2026-09-24）：`alibaba_segment_series.yaml` FY2019–FY2026 八年分部收入+经调整 EBITA 全序列，三次架构重述如实记录，分部→合计勾稽全闭合
- [x] zto 公开数据获取（2026-09-24）：中通 2026 中报 45 页已归档 `p5_samples/zto_2057/`（SHA 75e98464）。
- [ ] zto 数据接入：修复/替换 pypdf 乱码文本层，完成抽取、勾稽、来源页锚及 API/UI 使用链路测试。
- [x] 溯源真实来源链接设计输入（2026-09-24）：`docs/05_design/2026-09-24-provenance-source-link-design-input.md`（半页，待评审后实现）

## 五、待用户决策/输入

- [x] `codex/frontend-consistency-remediation` 分支：**保留分支结案**（2026-09-24 问答轮；不入 main，从待决清单移除）
- [x] U9 内部数据授权：**按 roadmap 顺序**，C 级出口完成后再启动（2026-09-24）
- [x] U10 V1.1 证据决策：用户倾向 **go**（2026-09-24；依赖 U4+U8+U9 到齐后按预置决策包启动）

## 五-b、决策日志（2026-09-24 问答轮，AskUserQuestion 两轮共 8 项）

1. 原决策记录：**双线推进**——大麦线与 oracle 录入线并行；后续用户已明确改为单主线串行、只在 `main` 执行，不再新开执行分支。
2. oracle AI 转录授权：**腾讯 fy2025 + 顺丰 2026h1 两份一次性授权**（与 zto 同模式，须独立会话执行）。
3. M2 原子激活（962b651，CURRENT_RELEASE 切换）：用户**追认有效**；后续知识工作（v2 刷新/增量扫描/roadmap v1.7）引用链无需变动。
4. 压力测试 10 条抽取错误候选：**按 AI 判断直接修正**（用户明示选择；执行时逐条在订正层登记原值/新值/依据，保留审计痕迹）。
   **已关闭（2026-09-25）**：10 条全部为误报（8 条符号印刷差异 + 2 条图像页），经订正层登记（validation/financial_reports/corrections.md）；顺带修复 2023fy 上期列 23 项 + 2019fy NCI 上期误抓；L1 覆盖率 1794/1794=100%、双零维持。
5. 前端遗留分支：**保留结案**（不入 main，不删）。
6. O 系列数据扩张：**批准阿里 9988 抽取 + 授权寻找 zto 公开数据**。
7. U9 授权时机：**按顺序**（C 级出口完成后启动）。
8. U10：**倾向 go**（未启动；U4 首跑后按预置决策包走）。

## 六、已完成里程碑（参考，勿重做）

U1–U7 全部 ✅ · U2 全关 ✅ · U5 ✅ · O1–O4 ✅ · 战略沉淀 D052–D054 ✅ · 竞品调研 C01–C20 ✅ · 知识地图 ✅ · 分支清理 ✅（8 删/1 保留）· CI 基线修复 ✅

## 七、综合 Review 后的收口 To-do（按依赖顺序）

权威执行规格：[FLOW 项目执行收敛与验收计划](2026-09-25-project-execution-convergence-plan.md)。以下状态为综合 review 基线；开始每项前先核对远端最新 SHA 与同 SHA CI。

1. [x] **审计线 CI 修复/复验**：MinIO/client 镜像修复已集成 main `96010a2`，CI run `36129442008` 17/17 success。
2. [x] **大麦实施提交主线集成**：普通合并 `e22d193`，CI run `36137591750` 17/17 success。
3. [ ] **主状态文档统一（G3b，进行中）**：同步 `PROJECT_STATE.md`、`CURRENT_ROADMAP.md`、本 TODO、工作包与 HANDOFF 的 migration、CI、集成状态及外部阻塞；跑文档门禁并推送。
4. [x] **常驻开发栈演示数据（G2，2026-09-25 完成）**：用户明确裁决本系统为演示系统、大麦数据全部入库；入库前 pg_dump 备份（`work/backups/flow-pre-damai-seed-20260925-203648.sql.gz`）；首次 seed 后 API/Web 启动、页面有数；随后发现共享库 `statement_report`/`objective_report_snapshot` 被并行会话的本地测试默认连接清空（conftest 指向共享 `flow` 库的旧坑），利用 seed 幂等语义重跑补回缺口；最终在集成后 main 代码上 `make damai-demo-verify` **19/19 通过**（含 damai 覆盖率双数据集端点），对象存储读回 SHA 一致。
5. [ ] **U4 修复与新留出**：支持“合并及公司”版式标题、参数化页码区间；原三样本回归；另建独立盲留出，不复用回归集充当泛化证明。
6. [ ] **C-level 出口**：先对账 corrections/10 条候选修正的文件、提交和基准凭证；然后由用户发起非实现方 AI 交叉评与独立 holdout 抽签；材料齐后正式 Go/No-Go。`1794/1794` 只表示覆盖，不等于 C-level 通过。
7. [ ] **P3 数据与溯源接入**：完成 ZTO 文本层与数据链路接入、勾稽和来源页锚测试；评审并实现真实来源链接；复核阿里分部序列在集成分支的来源与系统可见性。
8. [ ] **知识 release 收尾**：核对 M2 用户追认、`CURRENT_RELEASE`、sealed candidate/激活记录、Task 10 三仓库证据和独立复验；指针/证据不一致时先查证，不直接改 release。
9. [ ] **后续内部工作台与真实周期验证（gated）**：仅在 C-level Go 与内部数据授权满足后开始 U9/T13；按连续三个真实月度周期、同输入人工基准、盲评与工时门槛验收。U10 依预置决策包启动，不由模拟数据单独解锁。

### G0 开工基线记录

- [x] 基线核对完成（历史快照，2026-09-25）：当时审计分支 `aee9f5a` CI 在 MinIO 镜像拉取时失败，大麦 `f62cf8e` 相关 CI 成功；当时 main 为 `63f99b2`。最终修复与集成证据见上方 G1/G3a。
- [x] 未提交工作保护：`HANDOFF.md` 修改及 `services/api/tests/security/test_route_policy_registry.py` 未跟踪文件作者无法确定，按用户/并行 Agent 工作隔离保留，不纳入本次提交。
- [x] G1 执行链原从 `codex/flow-execution-convergence` 派生，已集成 main `96010a2`；大麦线经普通合并 `e22d193` 集成。后续不创建新执行分支。
