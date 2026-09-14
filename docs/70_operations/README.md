---
doc_id: FLOW-OPS-070
title: 运行手册
doc_type: navigation
status: current
version: 1.2
created_at: 2026-09-12
updated_at: 2026-09-14
owner: FLOW
applies_to: docs
---

# 运行手册

部署、配置、备份、日志、故障处理（M3 迁入 operations/）。允许 doc_type: operations。禁止: 设计目标（与现状混淆）。

## 当前入口

- [S01 多代理恢复与再启动顺序](2026-09-14-s01-recovery-and-restart-runbook.md)：当前 main/integration 变红后的统一恢复门禁。
- [S01 单一 Agent 修正接管说明](2026-09-14-s01-single-agent-repair-handoff.md)：用户终止多代理并行后的唯一接管顺序。
- 代理修正单：[安全车道](2026-09-14-sol-security-correction-brief.md) / [Kimi 路由车道](2026-09-14-kimi-route-policy-correction-brief.md) / [GLM 模块与协调车道](2026-09-14-glm-module-coordination-correction-brief.md)。
- [机器可读修正矩阵](2026-09-14-s01-agent-correction-matrix.tsv)：供代理或自动化工具按行领取与核验。
- [三智能体并行执行使用手册](three-agent-parallel-execution-runbook.md)：S01 Task 6–10 的分支、派发、合并、CI 与故障恢复协议。
