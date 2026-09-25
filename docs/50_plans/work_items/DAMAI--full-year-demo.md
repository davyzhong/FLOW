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

## 完成状态

D1–D3 已完成并集成 main：普通合并 `e22d193`，同 SHA CI run `36137591750` 的
17 个 job 全部通过。验收证据包括 `make damai-demo-verify` 19/19、八页面 E2E
9/9、二次 seed 全表零增长、发行包重建零漂移。合成数据经正式审核/冻结/发布链，
不绕过现有治理流程。

以上为隔离验收栈的验证结论。常驻开发库装载（G2）已于 2026-09-25 完成：用户裁决演示数据全部入库，入库前 pg_dump 备份，集成后 main 代码上 verify 19/19 通过、页面可见；期间发现共享库部分表被并行会话本地测试默认连接清空，经幂等重 seed 补回（证据见 [执行待办](../EXECUTION_TODO.md) §7-4）。

## 退出条件

- 维度、明细量、预算、AR、四表和经营财务对账全部闭合；
- `DAMAI.SYN` 独立身份和正式 review/freeze/publish 链无旁路；
- seed 原子、幂等，四条命令和八页面 E2E 可重放；
- 文档、回归与最终 completed SHA 的远端 CI 全绿。

详细步骤见[统一完整实施计划](../../superpowers/plans/2026-09-24-flow-integrated-execution-plan.md#6-d1大麦物流完整财年数据合同与静态发行包)。
