---
doc_id: FLOW-NAV-MAP-001
title: 旧路径→新路径与接替关系
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: docs
---

# 旧路径 → 新路径与接替关系

逐文件处置全表见 `docs/knowledge-base/00_governance/migration/path-map.tsv`（M0 冻结）。主要条目：

| 旧路径 | 新路径 / 接替 | 执行批次 | 状态 |
|---|---|---|---|
| `docs/knowledge-base/00_start_here/PROJECT_STATE.md` | `docs/00_start_here/PROJECT_STATE.md` | M1 | 已生效（旧页转兼容导航） |
| `docs/knowledge-base/00_start_here/AGENT_START_HERE.md` | `docs/00_start_here/READING_ORDER.md` | M1 | 已生效 |
| `docs/knowledge-base/04_decisions/DECISION_LOG.md` | `docs/10_governance/DECISION_INDEX.md` + `decisions/Dxxx` | M1 | 进行中 |
| `docs/superpowers/specs/*` | `docs/40_specs/SPEC_INDEX.md`（原位登记，机器路径 keep） | M3 | 进行中 |
| 产品定位（散于 D049/旧 README） | `docs/20_product/` 七份单一职责文档（含 PRODUCT_PRINCIPLES） | M3 | 已生效 |
| `docs/architecture|data-contract|intake|metrics/` | `docs/30_architecture/` / `docs/40_specs/<域>/` | M3 | 未开始 |
| `docs/operations/` | `docs/70_operations/` | M3 | 未开始 |
| `docs/implementation/` | `docs/60_delivery/implementation/` | M5 | 未开始（p5 机器路径永久 keep） |
| `docs/reviews/` | `docs/80_reviews/` | M5 | 未开始 |
| `docs/superpowers/plans/2026-09-07-unified-next-plan.md` | `docs/50_plans/CURRENT_ROADMAP.md` | M4 | **已生效**（旧计划 superseded） |
| `docs/superpowers/plans/2026-09-09-operations-track-plan.md` | `docs/50_plans/work_items/U09-O05--*.md` | M4 | 已生效 |
| 历史 plans（Phase/WS/M/P 系列 18 份） | `docs/90_archive/plans/` | M5 | **已生效** |
| `HANDOFF.md`（仓库顶层） | `docs/knowledge-base/07_handoff/HANDOFF.md` | M5 | **已生效** |
| `Finance_Intelligence_OS_完整会话归档.md`（顶层） | `docs/90_archive/plans/` | M5 | **已生效** |
| `docs/documentation-status.md` | `docs/60_delivery/generated/DOCUMENT_STATUS.md` | M5.2 | 未开始 |
| `docs/knowledge-base/02_research/synthesis/` | `docs/knowledge-base/10_sources/source_notes/` | M2 | 未开始 |

永久原位（不迁移）：五个不可变根（见 `00_governance/immutable-paths.lock.tsv`）、`docs/implementation/p5/` 机器数据、`08_wechat_sources/`（M2 拟追加 immutable delta）。


## M5 处置修订（2026-09-12）

以下条目由 move 改判 **keep**（引用密集/事实登记位，移动断链风险大于收益，遵循「不以搬迁换取表面整齐」）：`02_research/synthesis/`（来源层事实登记位，SOURCE_REGISTER 引用）、`06_sources/`（来源目录权威）、`09_competitive/`（内部 INDEX 自洽）、`implementation/` 非机器部分（验证记录与提交绑定）。逐文件处置见 `00_governance/migration/path-map.tsv`。
