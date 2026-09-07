# FLOW 文档中心｜2026-09-07

状态：当前导航。工程读取基线 `04ba4d7`，迁移至 0018；不以文档更新代替功能验收。

## 01｜先看当前结论

| 顺序 | 文档 | 用途 |
|---|---|---|
| 1 | [当前项目状态](knowledge-base/00_start_here/PROJECT_STATE.md) | 已提交能力、真实缺口、CI 时点与下一步 |
| 2 | [下一阶段执行准备计划](superpowers/plans/2026-09-07-next-stage-upgrade-plan.md) | P00–P12 详细顺序、依赖、交付和验收；本次不实施 |
| 3 | [参考与优化订正总册](knowledge-base/02_research/synthesis/2026-09-07-reference-and-improvement-master.md) | 来源、30 项建议、18 项订正、417 条素材索引 |
| 4 | [文档全量登记](documentation-status.md) | 每份文档的状态、日期、命名和处置 |
| 5 | [本次整理记录](implementation/2026-09-07-documentation-review-and-reorganization.md) | 发现、修订、命名映射与验证边界 |

## 02｜有效规格与计划

[D049 方向与验收](superpowers/specs/2026-09-06-objective-financial-analysis-direction.md)优先；[统一财务事实合同](superpowers/specs/financial-facts-contract.md)、[指标治理规格](superpowers/specs/2026-09-05-flow-metric-dictionary-design.md)和既有领域规格共同约束实现。较晚的已确认决策覆盖旧范围，不因整理文档改变财务公式。

[A01–H01 总台账](superpowers/plans/2026-09-06-objective-financial-analysis-master-plan.md)保留既有阶段进度；P 计划细化后续增量和验收，两者按映射表衔接。早期 Phase、WS 和 Pilot 计划是历史或被接替的排期，不再各自声称“唯一当前计划”。

## 03｜使用与开发

| 文档 | 适用范围 |
|---|---|
| [项目说明](../README.md) | 产品、快速启动及带拍摄时点的真实截图 |
| [运行架构](architecture/flow-v1-runtime.md) | 服务、同步构建、存储、打印与部署边界 |
| [领域对象](architecture/flow-v1-domain-objects.md) | canonical 与财报事实、版本、复核、冻结身份 |
| [Excel 合同](data-contract/flow-v1.md) | 已冻结物流交换格式，不代表全部财报接口 |
| [Excel 接入](intake/flow-v1-intake.md) | 映射、清洗、对账、发布及显式构建 |
| [指标与快照](metrics/flow-v1-metrics.md) | 物流 15 项子集、完整 55 项知识库和版本治理的区别 |
| [API 索引](api-reference.md) | 从已提交 OpenAPI 生成的完整方法/路径 |
| [单用户认证](operations/authentication.md) | 服务端凭据、会话与配置加载；不等于多角色权限 |
| [截图目录](assets/screenshots/README.md) | 历史实际画面及 P5 图形证据，不冒充本次新截图 |

## 04｜历史、证据与档案

[文档登记](documentation-status.md)按当前说明、有效规格、后续计划、历史计划、历史验收、研究候选、生成资料和不可变档案分类。历史命令、旧失败与旧测试数量保留；历史验收不自动证明最新提交。

[知识库](knowledge-base/README.md)提供[决策日志](knowledge-base/04_decisions/DECISION_LOG.md)、[影响图](knowledge-base/04_decisions/CHANGE_IMPACT_MAP.md)、[Agent 起点](knowledge-base/00_start_here/AGENT_START_HERE.md)及[交接指南](knowledge-base/07_handoff/CONTINUATION_GUIDE.md)。

命名采用 `YYYY-MM-DD-主题.md`；已有日期名保持，未注明日期的叙述性历史文档补日期。README、AGENTS、INDEX、PROJECT_STATE 等固定入口，以及脚本/测试依赖的路径保持稳定，标题和元数据标明日期；原件、截图、可读会话、批准快照及生成产物不为美观改写。详细例外与旧新映射见全量登记。
