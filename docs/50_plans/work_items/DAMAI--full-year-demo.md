---
doc_id: FLOW-WI-DAMAI-FULL-YEAR-001
title: 大麦物流完整财年演示数据与全产品验收
doc_type: work-item
status: active
version: 1.3
created_at: 2026-09-24
updated_at: 2026-10-12
owner: FLOW
depends_on: [FLOW-SPEC-DAMAI-DEMO-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, FLOW-SPEC-DAMAI-DEMO-001]
applies_to: repository
---

# 大麦物流完整财年演示数据与全产品验收

## 范围

按统一计划 D1–D3，把当前聚合半成品修正为 FY2025+FY2026 全量、确定性、可
重建、可幂等装载的合成发行版，并用真实服务链和八页面 E2E 验证系统。

## 用户补充要求与重开范围（2026-10-12）

原 D1–D3 版本已完成，但用户现要求大麦物流的全部经营 Mock 必须基于阿里巴巴/菜鸟公开原始数据，不能把无来源假设当作经营事实；并以该数据集验证系统功能和 CFO 驾驶舱。因此本包在唯一队首 CFO 驾驶舱工作中重开数据来源验收，不另设并行队列。原完成记录保留为历史，不再代表新数据基线已完成。

交付须区分并记录 `disclosed_fact`、`derived_fact`、`generated_demo_detail` 和隔离 `test_fixture`：每条公开事实包括报告、URL、期间、页表、原值/单位/币种和 SHA；派生值记录公式、输入和舍入；用于页面钻取的生成明细须能与来源聚合对账且明确为 Mock；组织/用户/权限信息仅作为测试夹具。无公开来源且无法复算的财务/经营值改为 unavailable。重点审查已标注的利息费用 65% 拆分、固定资产折旧 10% 估算、债务/应付拆分、销售收现及资本开支，不得继续作为实际事实。

验收还需覆盖原型 51 张图表的完整数据映射、CFO 十模块与所有系统关键功能，证明指标、图形、表格和来源之间可点击、可跳转、可下钻/上算/追溯；测试限定在隔离环境。上述均纳入 CURRENT_ROADMAP CFO 唯一队首顺序，按 CFO 工作包“用户补充验收基线”执行。

### 2026-10-12 来源基线首轮审计

审计记录见[大麦物流来源事实与 Mock 基线审计](../../60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md)。仓库已存在菜鸟 FY2021–FY2023 完整报表行、FY2019–FY2025 菜鸟分部序列、FY2021–FY2023 运营指标及对应抽取器/CAINIAO 加载器；当前 `DAMAI.SYN` 生成器未复用这些资产，另造了合成财报与件量。当前期间还与阿里/菜鸟财年错位，件量数量级和国内指标命名均有问题。下一步复用现有 P5 来源事实，补逐值 SHA/页表/期间定位与可重建映射，再将未公开粒度作为明示演示生成明细；未来源且不可复算的事实改为 unavailable。原始档案不改写。

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
