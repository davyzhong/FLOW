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

## 当前执行入口

- **[CURRENT_ROADMAP.md](../50_plans/CURRENT_ROADMAP.md)**（唯一执行入口，M4 起生效）：U08 active；U4 等外部到料；U9+O5 等授权；U10 硬依赖三者
- 旧统一计划与 O 系列计划已 superseded（保留任务细节与证据）
- 文档迁移：[迁移实施计划 M0–M6](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md)（M0–M4 完成；M5 历史整理待批次批准）

## 进行中 / 阻塞 / 待授权

1. **U8（进行中）**：真实存储完整旅程、HTTPS 部署拓扑、统一部署验收；备份恢复已 done。
2. **U4（外部到料即并行）**：独立会话录入 oracle，全行 diff 与留出泛化验收。
3. **U9/O5（待授权）**：硬依赖内部数据授权 + U8 收口。
4. **U10（硬依赖 U4+U8+U9/O5）**：V1.1 证据 go/hold/drop 决策。

## 知识基线

静态知识基线 `flow-knowledge-2026-09-12.1`（D051）；M2 发布 `flow-knowledge-2026-09-12.1` 前，产品设计引用一律使用该前缀。日常执行不读取动态 Obsidian。

## 能力矩阵与历史证据

已实现能力（物流窄切片、来源与财务事实 B01–B05、指标库 v1.1、报告中心、认证等）与历史验收细节见[历史状态快照](../knowledge-base/00_start_here/2026-09-07-project-state-history.md)与 [HANDOFF](../../knowledge-base/07_handoff/)；本页只维护当前事实。

## 更新纪律

每次只依据提交、测试和用户确认更新；修改正式合同先查决策与影响图；实施需对应任务授权。历史段落不叠加到本页。
