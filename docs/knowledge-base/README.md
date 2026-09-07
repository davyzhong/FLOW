# FLOW 项目知识库｜2026-09-07

状态：当前索引。当前工程状态和下一步只维护在[PROJECT_STATE](00_start_here/PROJECT_STATE.md)；历史时间线已独立留档，不再与当前摘要并列争夺优先级。

## 阅读顺序

1. [Agent 起点](00_start_here/AGENT_START_HERE.md)与[当前状态](00_start_here/PROJECT_STATE.md)。
2. [D049 客观财务分析方向](../superpowers/specs/2026-09-06-objective-financial-analysis-direction.md)、[事实合同](../superpowers/specs/financial-facts-contract.md)。
3. [决策日志](04_decisions/DECISION_LOG.md)、[变更影响图](04_decisions/CHANGE_IMPACT_MAP.md)。
4. [下一阶段执行准备计划](../superpowers/plans/2026-09-07-next-stage-upgrade-plan.md)：详细 P 任务；[A–H 台账](../superpowers/plans/2026-09-06-objective-financial-analysis-master-plan.md)：既有里程碑证据。
5. [累计参考与订正总册](02_research/synthesis/2026-09-07-reference-and-improvement-master.md)：30 项建议、18 项订正、417 条素材索引；不是全部原文已复核或功能已批准。

当前迁移至 0018；来源/事实链、构建编排、指标版本治理和管理界面已有实现。下一阶段补语义订正、独立验证、客观分析及报告/运行验收，不从 Phase 1/B02 重新开工，不把 v0 逐项审批作为前置。当前 CI 和在途工作见状态页，本次仅文档更新。

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
