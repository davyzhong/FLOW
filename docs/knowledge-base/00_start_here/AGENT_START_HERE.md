# Agent 起点

## 一句话理解项目

FLOW 是面向物流供应链企业 Finance BP 的 AI 财务分析工作台：把不同来源的 Excel 数据转换到统一数据中间层，再基于同一套数据完成经营驾驶舱、异常诊断、证据复核以及 PPT、Excel、正式月报输出。产品定位遵循 D039：当前阶段聚焦财务数据的收集与基于客观数据的准确财务分析这一确定性任务；经营分析（经营侧数据 + 业务假设的主观归因）是明确的未来扩展方向。

长期产品方向是 Finance Intelligence OS，但 V1 采用一个可验证的物流供应链月度经营分析窄切片。

## 当前已经确定的产品主线

```text
外部 Excel 或 FLOW 标准模板
→ AI 识别、字段映射、清洗、校验和财务对账
→ 数据库标准数据中间层
→ 指标语义与确定性分析引擎
→ Finance BP 高密度经营驾驶舱
→ Investigation：影响、驱动、下钻、公式、证据和复核
→ AI 辅助解释、追问和报告编排
→ PPT、分析 Excel、HTML/PDF 正式月报
```

## 必须保留的架构原则

1. 下游不能直接读取原始 Excel，只能依赖标准数据中间层；
2. Excel 标准模板是交换格式，不是内部数据库；
3. 原始文件和原始值不可覆盖；
4. 数据中间层与指标语义层分离；
5. 财务数字、差异和驱动由确定性引擎计算；
6. AI 负责识别、解释、追问和编排，不自行创造数字；
7. 事实、判断和假设必须分开；
8. 未完成关键证据复核的 Finding 不得进入正式报告；
9. 驾驶舱、Investigation 和全部输出引用同一 Metric Snapshot；
10. 架构不绑定纯本地离线部署。

## V1 用户和场景

- 主用户：Finance BP；
- 行业：物流企业；
- 业务：供应链业务；
- 分析周期：月度；
- 默认视角：当月 + YTD；
- 对比：预算、同比、近 12 个月趋势；
- 核心维度：客户群 × 物流产品；
- 核心经营故事：规模和收入增长，但低毛利业务结构、履约成本上涨和回款放缓导致利润与现金恶化。

## 当前状态

- 产品研究：完成；
- 关键产品决策：完成；
- 信息架构和核心页面原型：完成并确认；
- 数据中间层和标准 Excel 数据包方向：完成并确认；
- 统一报告输出方向：完成并确认；
- FLOW V1 正式设计规格：已写入并提交；
- 知识库归档：完成；
- V1 主实施路线图：完成；
- Phase 1 基础架构与对象契约详细计划：完成；
- Phase 1 基础架构与对象契约：完成并通过本地干净检出与 GitHub Actions 验收；
- Phase 2 标准 Excel 数据契约与高拟真 fixture：完成并通过本地干净检出与 GitHub Actions 验收；
- Phase 3 Intake、Mapping & Quality：完成并通过本地干净检出与 GitHub Actions 验收；
- Phase 4 Metric Snapshots：完成并通过本地干净检出与 GitHub Actions 验收；
- Phase 5 Analysis & Findings：完成并通过本地全量回归与 GitHub Actions 11 个 jobs 验收，5 个 typed Playbook、严格对账 Driver、确定性 Finding、Evidence 和不可变 Analysis Run 已落地；
- Phase 6 Finance BP Dashboard：完成，typed 只读 Dashboard API、高密度真实页面、八指标、趋势、经营利润桥、Findings、产品表、毛利矩阵、完整状态和 Investigation 身份交接已落地并通过浏览器验收；
- Phase 7 Evidence-first Investigation：完成，受控 Finding/Evidence 状态机与追加式 ReviewEvent（迁移 0008）、typed Investigation API、证据优先工作台（驱动桥、公式与引擎版本、对账与质量检查、文件/工作表/行级血缘、结论四要素、证据复核与审阅历史）已落地并通过 `make test-investigation-e2e` 验收；
- Phase 8 Bounded AI Copilot：完成，强制对象引用、数字一致性、事实/判断/假设分离、数据不足降级与交互审计均有固定评估门禁；
- Phase 9 Unified Publishing：完成，PPTX/XLSX/HTML/PDF 均从同一冻结 Report Snapshot 渲染并通过跨格式关键值一致性门禁；
- Phase 10 Acceptance Suite：功能验收组合门禁已完成；部署、权限、备份恢复和深度可观测性明确顺延到 Pilot Readiness；
- 运行栈：Next.js、FastAPI、Celery、PostgreSQL、Redis、MinIO 已可构建启动；
- 数据库对象：接入、血缘、标准事实、指标、分析和发布三层 migration 已落地；
- API 合约：`/api/v1/health`、`/api/v1/workspace` 与生成式 TypeScript 类型已落地；
- 数据契约：`flow.excel.v1`、10 张工作表标准模板、确定性物流 fixture、已知答案和数据库语义往返已落地；
- 非标准 Excel 识别与映射、版本化导入和原子发布：已落地；
- `flow.metrics.logistics.v1` 的 15 个指标、14 条依赖、比较窗口、精确计算轨迹和不可变 Metric Snapshot：已落地；
- 当前缺口不是核心计算引擎，而是 Excel 导入与报告下载的可用用户闭环、最小安全部署和脱敏真实数据试点。

## 新 Agent 的工作规则

开始任何修改前：

1. 阅读 [项目状态](PROJECT_STATE.md)；
2. 阅读 [决策日志](../04_decisions/DECISION_LOG.md)；
3. 阅读 [正式设计规格](../../superpowers/specs/2026-08-29-flow-v1-design.md)；
4. 确认要修改的是哪一个历史决策或系统边界；
5. 查阅 [变更影响图](../04_decisions/CHANGE_IMPACT_MAP.md)；
6. 明确旧决定是保留、扩展还是被取代；
7. 修改设计文档和决策日志后，再进入实施计划或代码。

不要把研究资料中的功能清单直接当成 V1 需求，也不要因为历史会话里出现过某个建议就默认它仍然有效。

## 当前下一步

当前处于 Pilot Readiness。严格按 D038 顺序推进：仓库与验收基线修复 → Excel 导入和报告下载用户闭环 → 最小安全部署 → 脱敏真实数据试点 → 依据试点证据决定 V1.1。不要把“Phase 1–10 功能窄切片完成”误写成“已生产就绪”，也不要在真实试点前凭研究材料扩张 V1.1。修改任何已冻结契约前，先查阅决策日志与变更影响图。
