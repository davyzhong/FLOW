---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 1.1
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 2026-09-13 文档基线（战略同步证据 `a708bd5`）：数据库迁移头 `0024_operations_publication`；产品主线 **U8 进行中**——U8-C 结构化日志已由 `088977b` 交付，剩余真实存储完整旅程、HTTPS 部署拓扑与统一部署验收。

**战略方向（2026-09-13 已批准）**：D052–D054 + 经三轮独立规格审查通过的[战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)生效——企业内部月度财务经营分析工作台为最终产品，公开财报为独立模块（三层两模块）；固定原则见 [PRODUCT_PRINCIPLES](../20_product/PRODUCT_PRINCIPLES.md)。这是目标态定义：不改变当前执行入口，U8 仍 active，U8 后先完成 Financial Facts Contract V2、安全/权限子规格和模块边界门禁，旧 U9/U10 不自动续跑。

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一执行入口，M4 起生效）：U08 active；U4 等外部到料；U9+O5 等授权；U10 硬依赖三者
- 旧统一计划与 O 系列计划已 superseded（保留任务细节与证据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) 已全部关闭（bfc1271 / e373e25，用户确认 2026-09-13）

## 进行中 / 阻塞 / 待授权

1. **U8（进行中）**：真实存储完整旅程、HTTPS 部署拓扑、统一部署验收；备份恢复已 done。
2. **U4（外部到料即并行）**：独立会话录入 oracle，全行 diff 与留出泛化验收。
3. **战略边界重构门禁（U8 完成后）**：冻结 U8 版本，重构共享底座/公开模块/内部工作台边界与规格，并先发布 Financial Facts Contract V2 与安全/权限子规格。
4. **公开模块 C 级出口（门禁后）**：执行冻结样本、company-level holdout、可复算/可追源和独立盲评量化协议。
5. **内部工作台与真实企业验证（C 级出口后）**：需内部数据授权；至少连续三个完整月度周期，与同输入人工基准逐周期比较。
6. **旧 U9/O5、U10（待重新裁决）**：仅保留历史工作包身份，不按旧依赖链自动领取。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。仓库内不可移动/重写区：五个不可变根（`00_governance/immutable-paths.lock.tsv` 逐文件锁定）、`docs/implementation/p5/` 机器数据路径、`08_wechat_sources/` 档案。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
