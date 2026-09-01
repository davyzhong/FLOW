# 变更影响图与可重启节点

## 目的

本文件帮助后续 Agent 从任意历史节点修改设计，而不遗漏下游影响。修改任何核心决定时，应先定位对应节点，再检查所有受影响对象。

## 核心依赖链

```text
行业与用户
→ 数据域和标准模板
→ 标准数据中间层
→ 指标与 Driver Model
→ 驾驶舱和 Investigation
→ Finding、证据和 AI 上下文
→ PPT、Excel 和正式月报
```

## 变更影响表

| 变更点 | 直接影响 | 必须同步复核 |
|---|---|---|
| 主用户从 Finance BP 改为管理层 | 首页密度、导航、分析权限 | Finding 表达、Investigation 入口、报告叙事 |
| 行业或业务从物流供应链改变 | 数据模板、维度、模拟故事 | KPI、Driver Model、专题页面、报告章节 |
| 月度改为日度/实时 | 数据粒度、批次和性能 | 趋势、异常规则、刷新机制、存储和成本 |
| 客户群 × 产品维度改变 | 核心事实表粒度 | 交叉矩阵、下钻、预算表、利润桥 |
| Excel 单文件改为多文件 | 接入和关联策略 | 批次、错误恢复、文件血缘和对账流程 |
| 标准数据字段或主键改变 | 数据契约和历史版本 | Excel 模板、映射器、迁移、指标依赖、源行追溯 |
| 指标公式改变 | Metric Snapshot | 驾驶舱、Finding、历史比较和所有报告 |
| Driver Model 改变 | Analysis Engine | Investigation、证据需求、AI 解释和报告结论 |
| AI 权限扩大 | 风险与可信机制 | 数字一致性测试、审阅、引用和发布规则 |
| 证据发布门槛改变 | Finding 生命周期 | 报告编排、审阅状态和审计记录 |
| Investigation 审批资格规则改变（D037） | 状态机与迁移 0008 | Investigation API/工作台、Phase 8 AI 上下文、Phase 9 报告资格判定 |
| 输出格式增加 Word | Publishing Renderer | 模板、分页、字体、回归测试和版本记录 |
| 部署方式确定 | 技术架构 | 鉴权、存储、文件安全、模型接入和运维 |

## 可从头重启

适用场景：改变产品定位、行业、首要用户或 V1 目标。

建议读取：

1. 历史 ChatGPT 完整会话；
2. 五份研究资料和综合研究结论；
3. 决策日志 D001–D009；
4. 原始行业截图。

重启时应创建新的设计规格，不直接修改已批准 V1 规格而不留版本。

## 从用户体验节点重启

适用场景：保留数据和行业设计，只重做驾驶舱、Investigation 或角色视角。

建议读取：

1. 决策日志 D010–D018；
2. `dashboard-density-v2.html`；
3. `investigation-evidence-v2.html`；
4. 外部财务驾驶舱参考图。

需要同步复核导航、信息密度、Finding 表达和报告叙事。

## 从数据架构节点重启

适用场景：修改标准模板、数据库模型、批次或数据接入。

建议读取：

1. 决策日志 D019–D024；
2. `canonical-data-layer.html`；
3. `standard-excel-package-v2.html`；
4. 正式规格第 6–8 章。

修改后必须重新验证指标、血缘、对账和全部下游页面。

## 从分析方法节点重启

适用场景：新增指标、Driver Model、Finding 类型或分析 Playbook。

建议读取：

1. 综合研究结论；
2. 正式规格第 9–10 章；
3. Investigation 原型；
4. 报告资料中的瀑布图、因果链和利润漏损页面。

当前可执行分析基线还应读取：

5. `docs/superpowers/specs/2026-09-01-flow-v1-phase-5-analysis-design.md`；
6. `docs/superpowers/plans/2026-09-01-flow-v1-phase-5-analysis.md`；
7. `docs/implementation/phase-5-verification.md`。

修改 Playbook、比较窗口、策略阈值或评分权重后，必须生成新的 policy hash，并重新验证 Driver 对账、Finding 硬门槛、排名、Evidence 和下游快照消费边界。

## 从 Dashboard / Investigation 交接节点重启

适用场景：修改驾驶舱信息密度、筛选、可视化、状态、Dashboard API，或 Phase 7 Investigation 的进入身份。

建议读取：

1. `docs/superpowers/specs/2026-09-01-flow-v1-phase-6-dashboard-design.md`；
2. `docs/superpowers/plans/2026-08-30-flow-v1-phase-6-dashboard.md`；
3. `docs/implementation/phase-6-verification.md`；
4. `docs/implementation/phase-6-dashboard-fidelity.md`；
5. 决策日志 D033–D036；
6. `dashboard-density-v2.html` 和最新 1440/1920 截图基线。

修改 Dashboard Projection 时必须同步复核 OpenAPI/TypeScript 合约、完整身份、Decimal 表示、筛选能力矩阵、降级状态、网络边界和截图基线。修改 Investigation 跳转时必须保证 Finding、batch、Metric Snapshot 和 Analysis Run 四个身份仍共同传递，且与 Phase 7 的证据查询边界一致。

## 从发布节点重启

适用场景：修改报告结构、增加格式或企业模板。

建议读取：

1. 决策日志 D025–D028；
2. `unified-publishing.html`；
3. 两份 PPT 研究资料；
4. 正式规格第 13 章。

## 变更记录要求

任何重新设计都应记录：

- 被修改的决策 ID；
- 修改原因；
- 原方案为何不再适用；
- 新方案的生效范围；
- 受影响的文档、数据对象、页面和测试；
- 是否需要迁移历史数据或重新生成报告。
