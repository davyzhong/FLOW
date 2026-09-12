---
doc_id: FLOW-SPEC-INDEX-001
title: 规格总索引
doc_type: governance
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
applies_to: specs
knowledge_release: flow-knowledge-2026-09-12.1
---

# 规格总索引（SPEC_INDEX）

规则：机器与测试消费的合同**永久原位**（compatibility path）；新增规格进对应域目录；本索引是规格唯一目录。

| spec | 域 | status | 权威路径 | 备注 |
|---|---|---|---|---|
| financial-facts-contract | financial-facts | approved | `docs/superpowers/specs/financial-facts-contract.md`（原位，机器消费） | 事实合同；测试引用其规范 |
| flow-v1-design | platform | approved | `docs/superpowers/specs/2026-08-29-flow-v1-design.md` | V1 总设计（Phase 1–10 已实现） |
| analysis design | analysis | approved | `docs/superpowers/specs/2026-09-01-flow-v1-phase-5-analysis-design.md` | Phase 5 |
| dashboard design | analysis | approved | `docs/superpowers/specs/2026-09-01-flow-v1-phase-6-dashboard-design.md` | Phase 6 |
| review repairs design | platform | approved | `docs/superpowers/specs/2026-09-04-review-repairs-design.md` | P0/P1 修复轮 |
| metric dictionary design | metrics | approved | `docs/superpowers/specs/2026-09-05-flow-metric-dictionary-design.md` | 指标库 v1/v1.1 |
| objective direction | product-cross | approved | `docs/superpowers/specs/2026-09-06-objective-financial-analysis-direction.md` | D049 载体 |
| operations methodology | operations | approved | `docs/superpowers/specs/2026-09-09-operations-track-methodology.md` | O 轨 + L1-L4 |
| static knowledge architecture | platform | approved | `docs/superpowers/specs/2026-09-12-static-knowledge-and-document-architecture-design.md` | V1.1，本迁移设计 |
| strategic reset design | product-cross | review | `docs/superpowers/specs/2026-09-13-flow-strategic-reset-design.md` | D052–D054 载体；三层两模块目标结构 |
| data contract | financial-facts | approved | `docs/data-contract/flow-v1.md`（原位，机器消费） | data-contract 域 |
| intake spec | data-intake | approved | `docs/intake/flow-v1-intake.md`（原位） | |
| metrics spec | metrics | approved | `docs/metrics/flow-v1-metrics.md`（原位） | |
| authentication | security | approved | `docs/operations/authentication.md`（原位） | |
| architecture runtime | platform | approved | `docs/architecture/flow-v1-runtime.md`（原位） | |
| domain objects | platform | approved | `docs/architecture/flow-v1-domain-objects.md`（原位） | |

机器 keep 路径（消费者清单 `migration/consumer-registry.tsv`）：`docs/implementation/p5/`、`docs/implementation/objective-analysis/`、`02_research/synthesis/` 两数据集 YAML。
