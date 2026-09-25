---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 2.0
created_at: 2026-09-12
updated_at: 2026-09-25
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 2026-09-25，当前主分支为 `main@370fd1f`，数据库迁移头为 `0030_page_anchor_vocabulary`（主线迁移链和当前开发库均已核实）；`e22d193` 将大麦实施线以普通合并集成，CI run `36137591750` 17/17 success；审计/G1 修复 `96010a2` 的 CI run `36129442008` 亦 17/17 success。大麦完整财年 synthetic 数据已在隔离验收栈通过 verify 19/19、八页面 E2E 9/9、重复 seed 零增长及发行包零漂移；**常驻开发库已装载大麦数据（G2 完成，2026-09-25）**：用户裁决演示系统数据全部入库，入库前已备份，集成后 main 代码上 verify 19/19 通过、页面可见。U4 的三份 oracle 已到齐但首跑 199 行均 `not_comparable`，需先修解析版式并补独立留出。公开 C 级覆盖答案集 `1794/1794` 的数字来自订正台账，不等于 C 级出口通过；非实现方盲评与 holdout 抽签仍待外部完成。用户已明确后续执行直接在 `main` 顺序完成，不再新建执行分支。

历史状态快照：下文部分 S01/R0–R4 描述记录了各自交付时的上下文；若与当前迁移号、分支集成或门禁状态冲突，以本段、CURRENT_ROADMAP 和 EXECUTION_TODO 为准。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。U8 冻结后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一状态入口）：U08、S01、前端一致性整改与大麦完整财年演示数据 completed；G2 常驻栈可见性、U4 修复与知识刷新待办状态见路线图；公开 C 级、内部真实试点仍受外部门禁
- **[FLOW 统一完整实施计划](../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md)**（唯一详细执行合同）：统一承接旧 U/O、S01、多 Agent、前端、知识刷新、大麦和基线修复计划；旧计划不再领取
- 旧统一计划与 O 系列计划已 superseded（保留任务细节与证据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 进行中 / 阻塞 / 待授权

1. **U8（已完成并冻结）**：[生产冻结交付记录](../60_delivery/2026-09-13-u8-production-freeze.md)；可恢复基线 `u8-final-baseline`；严格冻结标签 `flow-u8-freeze-20260913`。
2. **U4（blocked）**：三份 oracle 已录入但首跑 199 行均不可比较；先修版式适配，再用旧样本回归并补独立留出。
3. **[S01 战略边界、事实合同与安全门禁](../50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）**：Task 1–5 + R0/R1（台账 §6）+ R2/R3/R4（台账 §7）全部交付，Task 6 正式关闭。阶段 3 起转入[公开模块 C 级出口](../50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（T09–T12，gated）。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。
7. **大麦完整财年演示数据（completed）**：两年（24 个月）synthetic 全链已落地，合并提交 `e22d193`；主线 CI run `36137591750` 17/17 success。隔离栈 verify 19/19、八页面 E2E 9/9、重复 seed 零增长、发行包零漂移。**常驻开发库已装载并在集成后 main 上 verify 19/19（G2 完成，2026-09-25）**；合成数据不解除公开 C 级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
