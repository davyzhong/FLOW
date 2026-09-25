---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 1.9
created_at: 2026-09-12
updated_at: 2026-09-25
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 2026-09-25：数据库迁移头 `0029_statement_provenance`（沿 `0024 → … → 0028 → 0029` 修订链核对）；**U8 已完成并冻结**——U8-A～D 均已交付。S01 Task 1–5 已完成；安全规格 V1.1 已获用户批准并通过独立审查（零 P1/P2）。**多代理并行已由用户拍板终止，转为单 Agent 串行接管**：R0（冻结清理）与 R1（安全合同修复）已完成——F2 各项（durable audit writer、authorization 按 action×resource 判定、identity JSON 严格校验、legacy cutoff 误伤新 token）全部修复（`4264cb8`→`bc62937`），66 条路由全接 require_action，durable 审计与 correlation 中间件上线。**Task 6 已关闭（S01 完成）**：R2（治理写 7 条策略化 + publishing/operations 四阶段接线 + 旁路 pipeline 死代码删除 + §3.3 身份字段全链收口）、R3（module-boundaries-v2：path-glob ownership + 全树 AST 禁止互导，`scripts/check_module_boundaries.py`）、R4（full-verification-v2：隔离 compose project + 动态端口 + 真实 CA + U8 dump 恢复→升级 0028 + dump hash/聚合哈希/SQL-HTTPS marker 双证明，`scripts/r4_full_verification.sh` 本地 PASS，evidence `work/r4/evidence.json`）已全部交付；T09 前置（L0 入库保真基准 1454/1454，`scripts/accuracy_benchmark.py`）已可执行。**恢复基线随 R2–R4 合并更新为分支 `codex/r2-route-policy-v3` 最终绿色 SHA**（run 见台账 §7；历史基线 `640cfb8`/`4c02a3c` 保留为审计锚点）。逐车道基线、门禁与冻结令见[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) §6，本页不重复其细节。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。U8 冻结后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一状态入口）：U08、S01、前端一致性整改与大麦完整财年演示数据 completed；第二代静态知识刷新 active；公开 C 级、U4、内部真实试点仍受外部门禁
- **[FLOW 统一完整实施计划](../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md)**（唯一详细执行合同）：统一承接旧 U/O、S01、多 Agent、前端、知识刷新、大麦和基线修复计划；旧计划不再领取
- 旧统一计划与 O 系列计划已 superseded（保留任务细节与证据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 进行中 / 阻塞 / 待授权

1. **U8（已完成并冻结）**：[生产冻结交付记录](../60_delivery/2026-09-13-u8-production-freeze.md)；可恢复基线 `u8-final-baseline`；严格冻结标签 `flow-u8-freeze-20260913`。
2. **U4（外部到料即并行）**：独立会话录入 oracle，全行 diff 与留出泛化验收。
3. **[S01 战略边界、事实合同与安全门禁](../50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）**：Task 1–5 + R0/R1（台账 §6）+ R2/R3/R4（台账 §7）全部交付，Task 6 正式关闭。阶段 3 起转入[公开模块 C 级出口](../50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（T09–T12，gated）。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。
7. **大麦完整财年演示数据（completed）**：两年（24 个月）synthetic 全链已落地——`DAMAI.SYN` 独立合成身份、双财年闭合财报（FY2025/FY2026）经正式审核链发布、原子幂等 seed（二次 seed 全表零增长）、发行包零漂移重建（manifest SHA 锁定）、Finding/证据/四段结论/冻结报告齐备、指标覆盖包（FY2025 22/40、FY2026 25/40）与五粒度驾驶舱切换上线。实测：发行包 1920 经营实际 / 10752 预算 / 4800 AR / 672 财务实际，4 客群 / 40 客户 / 8 产品 / 6 区域 / 5 组织；一键启动 `make damai-demo-up` + verify 19/19 通过；八页面 E2E 9/9 通过（`make test-damai-demo-e2e`）；C3 全量回归 17 门禁绿，CI 全绿于 `d701c1d`（run 36098674773）。合成数据只用于产品全链验证，不解除公开 C 级或真实企业门禁。
8. **第二代静态知识刷新（active）**：批准规格与 preflight 已完成；K0–K6 尚待执行，用户战略裁决前不得切换 `CURRENT_RELEASE`。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
