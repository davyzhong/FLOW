---
doc_id: FLOW-SRC-README-001
title: 来源与证据层
doc_type: navigation
status: current
version: 1.1
created_at: 2026-09-12
updated_at: 2026-10-26
owner: FLOW
applies_to: knowledge-base
---

# 来源与证据层（10_sources）

回答「这条知识从哪里来、是否允许使用」，不承担产品结论。

- `SOURCE_REGISTER.md` —— 来源登记册（人类可读）与分层登记策略
- `source-register.tsv` —— 机器可读登记（活登记，知识卡按需追加篇级）
- `snapshots/` —— 固定截面定义（当前唯一截面：obsidian-2026-09-12T15:46+08:00）
- `source-baseline-2026-10-26.tsv`、`source-delta-2026-10-26.tsv`、
  `source-diff-2026-10-26.tsv` 与 `../00_governance/migration/source-id-registry-2026-10-26.tsv`
  —— K3 当前资料内容来自 `obsidianwiki-20261026T005516+0800-d601b4d5`。当前 registry/baseline/delta 已统一绑定该 accepted snapshot；已审阅条目的语义字段按批次登记，其余来源仍待审，不能视为已路由或可采纳。详见[当前快照与基线复核](../../60_delivery/verification/2026-10-26--k3-current-snapshot-v1.md)。
- 同名 `2026-10-19` 文件仅代表旧 accepted 工作区截面，保留为历史证据，不再作为当前输入。旧历史没有完整改名 registry，因此未确认的改名以新增/删除分别登记，不以标题相似度推断。
- `semantic-review-2026-10-26-batch-001.tsv` —— 首批 3 条 HIGH 主题候选的只读路由/可读性记录；不代表来源采纳或原始来源核验完成。
- `semantic-review-2026-10-26-batch-002.tsv` —— 第二批 3 条 HIGH 候选的全笔记核验、路由和内容风险记录；原始来源核验及采纳仍未完成。
- `source_notes/`（M2 后启用）—— 外部研究摘要（自 02_research/synthesis 迁入，M2 后续批次）

处置枚举：adopted / partially-adopted / duplicate / background / rejected / pending-verification；核验等级独立记录（program-routed / representative-read / human-verified）。
- `semantic-review-2026-10-26-batch-004.tsv` —— 第四批 3 条 HIGH 候选的全文审阅与现金流阈值/编制口径风险记录；均为 pending-verification。
- `semantic-review-2026-10-26-batch-005.tsv` —— 第五批 3 条 HIGH 候选全文审阅，记录合并报表案例不平衡、勾稽简化及通用指标阈值风险；均 pending-verification。
- `semantic-review-2026-10-26-batch-006.tsv` —— 第六批 3 条 HIGH 候选全文审阅，记录合并会计处理和内部交易抵消的规则边界风险；均 pending-verification。
- `semantic-review-2026-10-26-batch-007.tsv` —— 第七批 3 条 HIGH 候选全文审阅，记录三表案例信息不全、现金流编制摘要缺少边界及同主题材料重叠；均 pending-verification。
- `semantic-review-2026-10-26-batch-008.tsv` —— 第八批 3 条 HIGH/K6 全文审阅，覆盖资金预测方法与现金流模型；记录模型简化和两篇疑似重复发布，均 pending-verification。
- `semantic-review-2026-10-26-batch-009.tsv` —— 第九批 3 条 HIGH/K6 全文审阅，包含 2024 年流动资金贷款规则的官方来源核对、模型边界及重复候选记录；均 pending-verification。
- `semantic-review-2026-10-26-batch-010.tsv` —— 第十批 3 条 HIGH/K2 全文审阅，记录净利润与现金流关系的算例缺项、公式边界及防舞弊表述风险；均 pending-verification。
