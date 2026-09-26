---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 2.6
created_at: 2026-09-12
updated_at: 2026-09-26
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 2026-09-26，远端 `main` 当前基线为 `4932504c`，迁移头为 `0030_page_anchor_vocabulary`；本提交 CI 结果尚待核验。U8、S01、前端一致性 Task 0–9、大麦数据包和常驻库 G2 已完成；测试库隔离已于 `b60c51b` 修复，新的小米 2026H1 与阿里 FY2027Q1 holdout 已冻结并录入独立 oracle（`926af825`）。公开 C 级交叉评的42项确认异常已在 `4111f6a` 判定为真实抽取错误；109项口径疑点待裁决，京东物流200格英文原件已于 `b161fff` 冻结、待重核，抽取修订和新留出盲测未完成。大麦静态数据合同现有24个月经营明细（1,920实际、10,752预算、4,800应收回款、768财务实际，含合计守恒的 OCF）；常驻开发库仍为旧版672条财务实际，禁止据静态生成结果声称已加载。新静态财报发行工件每份51行；静态指标覆盖生成结果 FY2025 37/40、FY2026 40/40，其中 FY2025 三项同比指标无FY2024比较期。常驻开发库年报尚未重载，报表 API 此前仍返回每份40行。驾驶舱8张KPI卡、12个月趋势点（每点4指标）此前有OCF趋势12/12为 `trend_metric_not_published`、KPI预算比较4/8为 `comparison_not_published`、毛利矩阵实际22/32为 `metric_grain_not_published`且比较24/32未发布，整体 `degraded`；OCF事实已补至静态 canonical 并通过快照粒度测试，但隔离 verify 后的浏览器 E2E 9项因共享Next `.next`锁而全部连接失败，因此页面缺口尚未验证。验收脚本需先使用独立 `distDir`；不终止既有服务。FY2025四问工作台500已由`48f8363`修复。Gate 1诊断首轮来自 `main@3ff95115` + overlay `1ede2648…`，不是干净代码验收；全目标干净SHA复测、隔离UI验收和毛利矩阵根因复查仍待完成。主线只在 `main` 串行推进。

历史状态快照：下文部分 S01/R0–R4 描述记录了各自交付时的上下文；若与当前状态、分支集成或门禁冲突，以本段和 [CURRENT_ROADMAP](../50_plans/CURRENT_ROADMAP.md) 为准。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。U8 冻结后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一主线：状态真相 + 执行队列）：U08、S01、前端一致性整改与大麦完整财年演示数据 completed（含常驻库装载 G2）；C级交叉评已完成但归因、订正和新留出未完成；其余执行顺序见路线图。
- 旧统一计划、O 系列计划、EXECUTION_TODO 与 2026-09-24/25 三份总计划均已 superseded/archived（保留历史细节与证据，不再作为执行依据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 进行中 / 阻塞 / 待授权

1. **U8（已完成并冻结）**：[生产冻结交付记录](../60_delivery/2026-09-13-u8-production-freeze.md)；可恢复基线 `u8-final-baseline`；严格冻结标签 `flow-u8-freeze-20260913`。
2. **U4（blocked）**：旧样本首跑 199 行均不可比较；小米 2026H1 与阿里 FY2027Q1 新 holdout 已冻结并录入独立 oracle，先修版式适配并回归旧样本，再按盲测纪律运行新留出。
3. **[S01 战略边界、事实合同与安全门禁](../50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）**：Task 1–5 + R0/R1（台账 §6）+ R2/R3/R4（台账 §7）全部交付，Task 6 正式关闭。阶段 3 起转入[公开模块 C 级出口](../50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（T09–T12，gated）。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。
7. **大麦完整财年演示数据（底座 completed；页面覆盖未完成）**：24个月 synthetic 全链已落地，静态财务实际现为768条，含从已有月度合成现金流守恒分摊的 OCF；canonical 25项、快照粒度对账3项、发行包确定性检查通过。常驻开发库仍是672条旧版实际，不得重灌。新隔离栈 seed/verify 19/19通过，但浏览器E2E被共享 Next `.next`锁阻断，尚未完成八页面验收；修复 E2E 专用 `distDir` 后重跑，再核验 OCF 是否可见。财报每份51行，指标覆盖生成结果 FY2025 37/40、FY2026 40/40。毛利矩阵 grain/comparison 缺项尚未归因；FY2025四问API 500 已由`48f8363`修复。诊断和生成证据见[Gate 1/Gate 2记录](../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)；详见[剩余体验收口工作包](../50_plans/work_items/UX--post-damai-experience-closeout.md)。合成数据不解除公开 C 级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
