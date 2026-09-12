---
doc_id: FLOW-NAV-KB-README-001
title: 知识库导航
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-12
updated_at: 2026-09-12
owner: FLOW
applies_to: knowledge-base
---

# FLOW 项目知识库｜2026-09-12

状态：当前索引。当前工程状态和下一步只维护在[PROJECT_STATE](00_start_here/PROJECT_STATE.md)；历史时间线已独立留档，不再与当前摘要并列争夺优先级。

## 阅读顺序

1. [Agent 起点](00_start_here/AGENT_START_HERE.md)与[当前状态](00_start_here/PROJECT_STATE.md)。
2. [D049 客观财务分析方向](../superpowers/specs/2026-09-06-objective-financial-analysis-direction.md)、[事实合同](../superpowers/specs/financial-facts-contract.md)。
3. [决策日志](04_decisions/DECISION_LOG.md)、[变更影响图](04_decisions/CHANGE_IMPACT_MAP.md)。
4. [下一阶段统一执行计划](../superpowers/plans/2026-09-07-unified-next-plan.md)：唯一 U 队列、Knowledge Gate，以及 U8 主线、U4 外部到料、U9/O5 授权试点、U10 证据决策的详细计划；旧 P/A–H 台账只作历史证据。
5. [财经分析知识地图](02_research/2026-09-11-finance-knowledge-map.md)、[Obsidian 固定截面扫描评估](02_research/synthesis/2026-09-12-obsidian-internal-kb-assessment.md)与[累计参考订正总册](02_research/synthesis/2026-09-07-reference-and-improvement-master.md)：研究与候选来源，不自动批准功能。

当前迁移至 `0024_operations_publication`；U1–U3、U5–U7 与 O1–O4 已完成。下一阶段先收口 U8 运行保障；U4 等独立 oracle 到料可并行；U9/O5 等内部数据授权与 U8 收口；U10 再以四方证据决定 V1.1，不从旧 Phase 重开。每个后续任务必须按 D051 默认引用 `obsidian-2026-09-12T15:46+08:00` 并完成知识取用门禁；只有显式知识库维护才建新截面。当前 CI 和在途工作见状态页。

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
