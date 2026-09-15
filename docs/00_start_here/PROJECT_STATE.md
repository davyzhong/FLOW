---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 1.6
created_at: 2026-09-12
updated_at: 2026-09-15
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 2026-09-15：数据库迁移头 `0027_security_contract_fix`（沿 `0024 → 0025 → 0026 → 0027` 修订链核对）；**U8 已完成并冻结**——U8-A～D 均已交付。S01 Task 1–5 已完成；安全规格 V1.1 已获用户批准并通过独立审查（零 P1/P2）。**多代理并行已由用户拍板终止，转为单 Agent 串行接管**：R0（冻结清理）与 R1（安全合同修复）已完成——F2 各项（durable audit writer、authorization 按 action×resource 判定、identity JSON 严格校验、legacy cutoff 误伤新 token）全部修复（`4264cb8`→`bc62937`），66 条路由全接 require_action，durable 审计与 correlation 中间件上线。**Task 6 维持不关闭**：R1 使其 closure-ready，但按接管计划完成定义，须 R2（route-policy-v3 治理写 + publishing/operations 接线）、R3（module-boundaries-v2 全树 AST）、R4（full-verification-v2）全绿后才可宣布 S01 完成。**当前唯一恢复基线为 `640cfb8`**（main，CI run 34907918485 全绿 17/17，同树含 R1 代码与文档门禁修复）；历史基线 `ba5f34c`/`4c02a3c` 保留为审计锚点。逐车道基线、门禁与冻结令见[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) §6，本页不重复其细节。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。U8 冻结后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一执行入口）：U08 completed；S01 active；U4 等外部到料；旧 U9/O5、U10 等重新裁决
- 旧统一计划与 O 系列计划已 superseded（保留任务细节与证据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 进行中 / 阻塞 / 待授权

1. **U8（已完成并冻结）**：[生产冻结交付记录](../60_delivery/2026-09-13-u8-production-freeze.md)；可恢复基线 `u8-final-baseline`；严格冻结标签 `flow-u8-freeze-20260913`。
2. **U4（外部到料即并行）**：独立会话录入 oracle，全行 diff 与留出泛化验收。
3. **[S01 战略边界、事实合同与安全门禁](../50_plans/work_items/S01--post-u8-boundary-contract-security.md)（当前 active）**：Task 1–5 已完成（Facts V2、兼容适配、Enterprise/AnalysisCycle 与 0025 均已进入 main）；安全规格 V1.1 已获用户批准，其独立审查已于 2026-09-13 闭环（`6c3c1cd`，零 P1/P2）。**Kimi `0841ff9`（route-policy v1）不在 main**——它与已批准的 V1.1 设计冲突、实质回退 S01 方向，被 v2 取代，分支停在 `cf90df0` 作为审计证据，不得 rebase 或 force-push。2026-09-14 晚起单 Agent 接管：R0+R1 完成（台账 §6），Task 6 closure-ready 但**不关闭**，剩余 R2–R4 按[单 Agent 接管说明](../70_operations/2026-09-14-s01-single-agent-repair-handoff.md)串行推进；当前唯一恢复基线 `640cfb8`。后续按该接管说明与冻结令执行。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
