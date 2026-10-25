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
  —— K3 当前输入 `obsidianwiki-20261026T003619+0800-4ea1c067` 的只读登记与四维差异；语义字段仍待审，不能视为已路由或可采纳。详见[当前快照与基线复核](../../60_delivery/verification/2026-10-26--k3-current-snapshot-v1.md)。
- 同名 `2026-10-19` 文件仅代表旧 accepted 工作区截面，保留为历史证据，不再作为当前输入。旧历史没有完整改名 registry，因此未确认的改名以新增/删除分别登记，不以标题相似度推断。
- `source_notes/`（M2 后启用）—— 外部研究摘要（自 02_research/synthesis 迁入，M2 后续批次）

处置枚举：adopted / partially-adopted / duplicate / background / rejected / pending-verification；核验等级独立记录（program-routed / representative-read / human-verified）。
