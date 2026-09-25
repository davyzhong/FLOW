---
doc_id: FLOW-WI-UX-POST-DAMAI-001
title: 大麦数据后的剩余体验收口
doc_type: work-item
status: blocked
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
depends_on: [FLOW-WI-DAMAI-FULL-YEAR-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, frontend-route-state-viewport-matrix]
applies_to: web-frontend
---

# 大麦数据后的剩余体验收口

## 范围

只承接旧前端计划尚未关闭、且需要真实数据态验证的能力：下载/导出审计、真实
来源跳转、经分专员工作流首页、固定下钻路径、报告渐进披露和治理折叠。

## 当前阻塞

大麦 D3 尚未完成。现有前端一致性 Task 0–9 已关闭，不得以本工作包名义重做
设计系统或页面全量迁移。

## 退出条件

- 大麦正常/空/加载/错误/403 状态与三视口门禁全部通过；
- 导出审计和真实来源跳转有 API、组件与 E2E 证据；
- 首页、下钻、报告和治理交互符合经分专员工作流；
- 同一 SHA 的 unit/e2e/视觉证据/CI 全绿。

详细步骤见[统一完整实施计划 U 轨](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#9-u真实数据驱动的剩余体验收口)。
