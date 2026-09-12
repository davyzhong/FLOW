---
doc_id: FLOW-DECISION-D038
title: D038 Pilot Readiness 推进顺序
doc_type: decision
status: accepted
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
decided_at: 2026-09-12
authority: user
source_refs: [docs/knowledge-base/04_decisions/DECISION_LOG.md]
---

# D038 Pilot Readiness 推进顺序

- 状态（原文）：有效；用户于 2026-09-02 明确批准。（映射为 accepted）

- 状态（原日志）：有效；用户于 2026-09-02 明确批准。
- 决定：Phase 1–10 功能窄切片之后，严格按照“仓库与验收基线修复 → 补齐 Excel 导入和报告下载的用户闭环 → 最小安全部署 → 脱敏真实数据试点 → 用试点证据决定 V1.1”推进。
- 完成定义：功能窄切片完成不等于试点或生产就绪；身份权限、部署加固、备份恢复、可观测性和真实数据验证均必须单独验收。
- 约束：真实试点之前不以外部研究功能清单扩张 V1.1；试点数据必须脱敏，所有业务结论必须能回溯到受治理快照、证据和输出产物。
