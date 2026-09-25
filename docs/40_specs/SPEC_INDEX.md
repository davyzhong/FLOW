---
doc_id: FLOW-SPEC-INDEX-001
title: 规格总索引
doc_type: governance
status: current
version: 1.3
created_at: 2026-09-12
updated_at: 2026-09-18
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
| strategic reset design | product-cross | approved | `docs/superpowers/specs/2026-09-13-flow-strategic-reset-design.md` | V1.1；D052–D054、单一路线图、Facts V2/安全门禁、量化验收协议 |
| static knowledge refresh and strategic rebaseline | product-cross | approved | `docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md` | V1.1；第二代静态知识刷新、sealed candidate、战略裁决与原子激活合同 |
| damai logistics demo data release | product-cross | approved | `docs/superpowers/specs/2026-09-24-damai-logistics-demo-data-design.md` | 24 个月跨域 synthetic 演示数据、一键装载、页面覆盖与无 schema 变更约束 |
| data contract | financial-facts | approved | `docs/data-contract/flow-v1.md`（原位，机器消费） | data-contract 域 |
| intake spec | data-intake | approved | `docs/intake/flow-v1-intake.md`（原位） | |
| metrics spec | metrics | approved | `docs/metrics/flow-v1-metrics.md`（原位） | |
| authentication | security | approved | `docs/operations/authentication.md`（原位） | |
| architecture runtime | platform | approved | `docs/architecture/flow-v1-runtime.md`（原位） | |
| domain objects | platform | approved | `docs/architecture/flow-v1-domain-objects.md`（原位） | |
| module boundaries v1 | platform | approved | `docs/40_specs/platform/module-boundaries-v1.md` | S01 子规格：三层两模块边界（D052–D054） |
| financial facts contract v2 | financial-facts | approved | `docs/40_specs/financial-facts/financial-facts-contract-v2.md` | S01 子规格：Facts V2 向后兼容扩展 |
| internal workbench rbac audit v1 | security | approved | `docs/40_specs/security/internal-workbench-rbac-audit-v1.md` | S01 V1.1；2026-09-13 主协调者终审清零 P1/P2 + F1/F2 裁决后由用户明确批准 |
| security route inventory v1 | security | approved | `docs/40_specs/security/route-inventory-v1.tsv` | 最终 `api_router` 的 64 个挂载入口；按实际副作用登记 action/loader/owner/blocker |

机器 keep 路径（消费者清单 `migration/consumer-registry.tsv`）：`docs/implementation/p5/`、`docs/implementation/objective-analysis/`、`02_research/synthesis/` 两数据集 YAML。
