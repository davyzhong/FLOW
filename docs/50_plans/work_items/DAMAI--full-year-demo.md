---
doc_id: FLOW-WI-DAMAI-FULL-YEAR-001
title: 大麦物流完整财年演示数据与全产品验收
doc_type: work-item
status: completed
version: 1.1
created_at: 2026-09-24
updated_at: 2026-09-25
owner: FLOW
depends_on: [FLOW-SPEC-DAMAI-DEMO-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, FLOW-SPEC-DAMAI-DEMO-001]
applies_to: repository
---

# 大麦物流完整财年演示数据与全产品验收

## 范围

按统一计划 D1–D3，把当前聚合半成品修正为 FY2025+FY2026 全量、确定性、可
重建、可幂等装载的合成发行版，并用真实服务链和八页面 E2E 验证系统。

## 当前断点

- 已有画像、生成器、闭合财报、静态发行包和部分 Intake/分析链。
- 未完成 D1.1–D3.3；正式验收前不得使用当前聚合数据灌库验收。
- 不新增 migration，不修改 `.env`/CI，不替换非大麦公开 fixture。

## 退出条件

- 维度、明细量、预算、AR、四表和经营财务对账全部闭合；
- `DAMAI.SYN` 独立身份和正式 review/freeze/publish 链无旁路；
- seed 原子、幂等，四条命令和八页面 E2E 可重放；
- 文档、回归与最终 completed SHA 的远端 CI 全绿。

详细步骤见[统一完整实施计划](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#6-d1大麦物流完整财年数据合同与静态发行包)。
