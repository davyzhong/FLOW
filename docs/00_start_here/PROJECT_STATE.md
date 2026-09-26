---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 2.2
created_at: 2026-09-12
updated_at: 2026-09-26
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 2026-09-26，远端 `main` 为 `face8279`，迁移头为 `0030_page_anchor_vocabulary`；之后的文档状态更新和最新 SHA 的 CI 需按同一 SHA 单独核验。U8、S01、前端一致性 Task 0–9、大麦数据包和常驻库 G2 已完成；测试库隔离已于 `b60c51b` 修复，新的小米 2026H1 与阿里 FY2027Q1 holdout 已冻结并录入独立 oracle（`926af825`）。公开 C 级交叉评的42项确认异常已在 `4111f6a` 判定为真实抽取错误；109项口径疑点待裁决，京东物流200格英文原件已于 `b161fff` 冻结、待重核，抽取修订和新留出盲测未完成。大麦数据合同有24个月经营明细（1,920实际、10,752预算、4,800应收回款、672财务实际），但本地只读 API 抽查显示仅两份已发布年度报表、FY2025/FY2026 指标覆盖22/40和25/40，驾驶舱为 `degraded`（月度趋势及毛利矩阵有未发布项）；用户已批准数据可见性修复工作包，当前处于 Gate 1 只读盘点。后续主线只在 `main` 串行推进。

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
7. **大麦完整财年演示数据（底座 completed；页面覆盖未完成）**：24个月 synthetic 全链已落地，隔离栈 verify 19/19、八页面 E2E 9/9、重复 seed 零增长、发行包零漂移；常驻开发库 G2 已装载。最新本地 API 抽查：FY2025/FY2026 各一份年度报表、每份40行覆盖四张表；指标覆盖22/40、25/40；驾驶舱8卡/6趋势/8产品/4客群/2发现，但 state=`degraded`，部分趋势指标和毛利矩阵未发布。详见[大麦数据后的剩余体验收口](../50_plans/work_items/UX--post-damai-experience-closeout.md)。合成数据不解除公开 C 级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
