---
doc_id: FLOW-OPS-R2-DD0-BASELINE-20260915
title: R2 Gate 开工基线记录（DD0）
doc_type: operations
status: active
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
applies_to: repository
subject_ref: main@361e4f0
---

# R2 Gate 开工基线记录（DD0 轻量版）

核对时间：2026-09-15，单一 Agent 串行模式，分支 `codex/r2-route-policy-v3`。

| 核对项 | 结果 |
|---|---|
| HEAD / origin/main | `361e4f0`（一致，fetch 后无新外部提交） |
| 同 SHA CI | run `34913878637` success（17/17 required jobs） |
| 迁移头 | 唯一：`0027_security_contract_fix` |
| U8 冻结锚 | tag `flow-u8-freeze-20260913`；dump `backups/u8-baseline/flow-u8-final.dump`（Git 外）；合同 `config/acceptance/u8-baseline.json`（迁移头 0024 + 关键表计数 + 12 快照聚合哈希） |
| 最后一绿基线 | `640cfb8`（run 34907918485），其间 `c93c896`/`361e4f0` 均为文档提交且同 SHA 全绿 |
| 工作区 | 干净（0 未提交项） |
| 权威文档四点核对 | PROJECT_STATE v1.6 / CURRENT_ROADMAP / S01 工作包 / 协调台账 §6 相互一致，下一 Gate = R2 |

R2 范围（T01–T05，唯一授权范围）：治理写 7 条策略化落地、publishing/operations
四阶段串行事务 + durable intent/outcome、pipeline 死代码删除、工程卫生包
（运行日志移出 Git / owner 职责域化 / dashboard 快照重发 / m6 门禁评估）。

不在 R2 范围：AI 问数、行业扩张、内部工作台、UI 大改。
