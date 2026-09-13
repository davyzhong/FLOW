---
doc_id: FLOW-NAV-KB-README-001
title: 知识库导航
doc_type: navigation
status: current
version: 1.2
created_at: 2026-09-12
updated_at: 2026-09-13
owner: FLOW
applies_to: knowledge-base
---

# FLOW 项目知识库｜2026-09-13

状态：当前索引。当前工程状态和下一步只维护在[PROJECT_STATE](00_start_here/PROJECT_STATE.md)；历史时间线已独立留档，不再与当前摘要并列争夺优先级。

## 阅读顺序

1. [Agent 兼容入口](00_start_here/AGENT_START_HERE.md)跳转到唯一[当前状态](../00_start_here/PROJECT_STATE.md)与[最短阅读顺序](../00_start_here/READING_ORDER.md)。
2. [当前路线图](../50_plans/CURRENT_ROADMAP.md)是唯一执行入口；U8 后下一阶段的 [S01 详细计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md)当前仍被 U8 阻塞；历史统一 U 计划和其他旧计划只保留任务细节与证据。
3. [战略重构设计 V1.1](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)、[固定产品原则](../20_product/PRODUCT_PRINCIPLES.md)与[决策索引 D001–D054](../10_governance/DECISION_INDEX.md)定义当前产品方向和裁决。
4. [现行事实合同 V1](../superpowers/specs/financial-facts-contract.md)约束当前实现；内部工作台所需 Financial Facts Contract V2 是 U8 后前置规格，不得把目标字段误称为已实现。
5. [财经分析知识地图](02_research/2026-09-11-finance-knowledge-map.md)、[Obsidian 固定截面扫描评估](02_research/synthesis/2026-09-12-obsidian-internal-kb-assessment.md)与[累计参考订正总册](02_research/synthesis/2026-09-07-reference-and-improvement-master.md)是静态素材与方法来源，不自动批准功能或成为企业事实。

当前迁移头为 `0024_operations_publication`；U1–U3、U5–U7 与 O1–O4 已完成，U8 仍是当前主线，U4 等独立 oracle 到料可并行。U8 后依次经过边界重构、Facts V2 与安全/权限门禁、公开模块 C 级量化出口、内部工作台和真实企业验证；旧 U9/O5、U10 必须重新裁决，不自动续跑。每个后续任务按 D051 默认引用静态知识发布 `flow-knowledge-2026-09-12.1`；只有显式知识库维护才建立新截面。当前 CI 和在途工作见状态页。

## 分类导航

| 目录 | 内容与使用方法 |
|---|---|
| [00_start_here](00_start_here) | 固定当前入口与注明日期的历史状态快照 |
| [01_conversations](01_conversations/INDEX.md) | 原始与可读会话档案；过去的话不自动构成当前需求 |
| [02_research](02_research/INDEX.md) | 原始材料、日期化综合研究、候选建议和订正 |
| [03_assets](03_assets/IMAGE_CATALOG.md) | 原始图片和历史原型；不改写为最新界面 |
| [04_decisions](04_decisions/DECISION_LOG.md) | 决策演变与影响，较晚已确认决策优先 |
| [05_design](05_design/PROTOTYPE_INDEX.md) | 批准规格快照和原型引用，原快照不改 |
| [06_sources](06_sources/SOURCE_CATALOG.md) | 来源、访问限制和链接 |
| [07_handoff](07_handoff/CONTINUATION_GUIDE.md) | 当前接续步骤和提示词 |
| [08_wechat_sources](08_wechat_sources/README.md) | 已移交 DavyBase，只保留引用和历史移交证据 |
| [09_competitive](09_competitive/INDEX.md) | BI/FP&A 竞品调研素材（C01–C20，界面/图表/方法/公式四维借鉴） |
| [99_manifest](99_manifest) | 文件清单、SHA-256 与档案说明 |

全项目导航见[文档中心](../README.md)，逐份状态与改名见[文档登记](../documentation-status.md)，命名和维护见[文档治理规则](../2026-09-07-documentation-governance.md)。

## 证据与历史规则

冲突时先看用户较晚明确要求，再看有效正式规格与决策。项目状态描述实现，不能自行批准新合同；研究和 AI 总结只作线索。官方原文、可见产品功能、专业观点、二次摘要、仅索引分别标可信边界。

原始归档基准日期为 2026-08-29。历史验收只证明其注明的提交和环境；旧 S3 超时已在 2026-09-06 修复，不作为当前未修故障。公开财报版本、企业内部试点和生产部署分开验收。

## 原始档案保护与更新

- `raw/`、`original/`、原始图片、批准规格快照不改写、不因排序改名。
- 生成产物及工具依赖路径保持稳定；问题在说明或订正层记录，不手工改数值。
- 衍生当前文档更新正文；历史计划/研究保留原语境并标适用状态，修正另加明确说明。
- 新增/修改知识库时更新相关索引，重新生成 `99_manifest/inventory.tsv` 与 `sha256sums.txt`，清单不包含自身。
- 按根目录 AGENTS.md 验证，只提交本任务文件并推送规范 [origin](https://github.com/davyzhong/FLOW)，不提交用户原件或其他任务改动。
