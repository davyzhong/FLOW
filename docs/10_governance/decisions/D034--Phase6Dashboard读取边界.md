---
doc_id: FLOW-DECISION-D034
title: D034 Phase 6 Dashboard 读取边界
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

# D034 Phase 6 Dashboard 读取边界

- 状态（原文）：有效（映射为 accepted）

- 状态（原日志）：有效
- 决定：浏览器只通过 typed `GET /api/v1/dashboard/overview` 读取只读投影；该投影只消费相互绑定的已发布 Metric Snapshot、Analysis Run 及治理元数据。
- 禁止：浏览器不得读取原始文件、canonical 事实、Metric Value 或 Analysis 持久化接口，也不得重新计算指标、Driver、Finding 资格和排名。
- 原因：让首个用户界面继承 Phase 1–5 的数字一致性、版本身份和不可变保证。
