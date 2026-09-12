---
doc_id: FLOW-STATE-001
title: PROJECT_STATE
doc_type: state
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: repository
---

# FLOW 当前项目状态（唯一 current state）

截至 `0fc3488`（2026-09-12）：数据库迁移头 `0024_operations_publication`；最近 CI run `34696597772` 验证中（M0/M1 文档批次）；产品主线 **U8 进行中**——U8-C 结构化日志已由 `088977b` 交付，剩余真实存储完整旅程、HTTPS 部署拓扑与统一部署验收。

## 当前执行入口（M4 前有效）

- 产品执行：[统一计划 U1–U10](../../superpowers/plans/2026-09-07-unified-next-plan.md)（唯一执行入口；M/P 系列已归档并入；`CURRENT_ROADMAP.md` 尚未生效，M4 建立）
- 经营轨断点：[O 系列计划](../../superpowers/plans/2026-09-09-operations-track-plan.md)（仅剩 O5，待内部数据授权）
- 文档迁移：[迁移实施计划 M0–M6](../../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md)（M0 已完成基线冻结 `dd5a24b`；M1 进行中——元数据合同已由 `0fc3488` 生效并接入 CI）

## 进行中 / 阻塞 / 待授权

1. **U8（进行中）**：真实存储完整旅程、HTTPS 部署拓扑、统一部署验收；备份恢复已 done。
2. **U4（外部到料即并行）**：独立会话录入 oracle，全行 diff 与留出泛化验收。
3. **U9/O5（待授权）**：硬依赖内部数据授权 + U8 收口。
4. **U10（硬依赖 U4+U8+U9/O5）**：V1.1 证据 go/hold/drop 决策。

## 知识基线

静态知识基线 `pre-static-obsidian-2026-09-12T15:46+08:00`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
