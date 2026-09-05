# 变更影响图与可重启节点

## 目的

本文件帮助后续 Agent 从任意历史节点修改设计，而不遗漏下游影响。修改任何核心决定时，应先定位对应节点，再检查所有受影响对象。

## 核心依赖链

```mermaid
flowchart LR
    A[行业与用户] --> B[数据契约 / 模板 / 映射]
    B --> C[标准数据中间层]
    C --> D[指标快照与分析运行]
    D --> E[驾驶舱与 Investigation]
    E --> F[Finding / Evidence / 审批]
    F --> G[冻结报告 JSONB]
    G --> H[PPTX / XLSX / HTML / PDF]
    F --> I[受约束 AI 与审计]
    J[认证 / 代理 / 存储 / 部署] -. 运行边界 .-> E
    J -. 运行边界 .-> H
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
| 产品定位收敛为准确财务分析（D039） | 路线图排序、叙事与品牌约束 | 经营判断相关远期项、试点验证重点（准确性承诺）、报告章节结构、正式品牌释义 |
| 会计基础数据与财务分析指标库立项（D040） | 新增语义知识层（准则/科目/分录/指标卡片与取数映射），后续 `flow.metrics.logistics.v1` 迁移为库内行业指标集 | D016/D028/D031/D033/D037 不可变与确定性边界复核、指标口径变更的版本化流程、驾驶舱/报告/Copilot 的口径引用来源、已发布快照不受目录演进影响 |
| 输出格式增加 Word | Publishing Renderer | 模板、分页、字体、回归测试和版本记录 |
| 冻结报告载荷或渲染规则改变（D028，迁移 0010） | JSONB 冻结内容、版本判定、不可变触发器 | 四格式黄金值、并发冻结/审批锁、事务提交；旧无 payload 快照需重新冻结，不能补造历史 |
| 人工映射与质量警告确认改变 | MappingVersion、源 SHA/批次身份、发布资格 | `/data` 状态刷新、失败恢复、标准化导出、Intake API 与生成契约 |
| 单用户登录与代理认证改变 | AUTH_TOKEN、签名会话、公开 origin | 匿名拒绝、会话到期/轮换、Origin 检查、HTTPS cookie、下载头与同源浏览器链路 |
| 对象存储配置或传输改变 | 原始文件、内容寻址、发布产物 | 真实 PutObject/GetObject、SHA 校验、下载、重试、备份恢复；存储替身不能替代真实链路验收 |
| 部署方式确定 | 技术架构 | 鉴权、存储、文件安全、模型接入和运维 |
| 试点数据字段或口径改变 | Intake Mapping、canonical 与指标目录 | 对账、Driver、Finding、Dashboard、报告及脱敏规则 |
| 依据试点调整 V1.1 范围（D038） | 产品优先级与验收标准 | 决策日志、实施计划、数据契约、用户旅程和发布说明 |

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
4. 正式规格第 13 章；
5. `docs/implementation/2026-09-04-review-repairs.md` 与迁移 `0010_frozen_reports`。

当前冻结内容已完整持久化为 JSONB，渲染只能消费冻结内容；审批、冻结与证据变更需要一致的锁和事务边界。改变已批准结论或拒绝证据会退回复核，不能依靠旧 approved 状态继续冻结。

## 从 Pilot Readiness 节点重启

适用场景：维护已实现的 Excel 导入/报告下载闭环、完成安全部署和真实对象存储补验、开展脱敏真实数据试点或据此调整 V1.1。状态基线为 2026-09-04 的 `c1a59d1`。

建议读取：

1. 决策日志 D038；
2. `docs/implementation/phase-10-acceptance.md`；
3. `docs/superpowers/plans/2026-09-03-flow-pilot-readiness-phase-2-security-deployment.md`；
4. `docs/operations/authentication.md` 与 `docs/implementation/2026-09-04-review-repairs.md`；
5. `docs/implementation/phase-pilot-1-user-closure.md` 与 Phase 3/6/7/9 历史验证记录。

当前已完成单用户认证，但备份恢复、HTTPS 部署、结构化日志及真实试点仍待完成。独立 MinIO 建桶/列桶成功不等于上传链路成功；PutObject 超时须独立解决并补验，不得以历史门禁或存储替身替代。

试点修改不得绕过数据中间层或重新定义已发布历史；新增字段、指标或 Driver 必须版本化，并重新运行全部受影响门禁。只有试点中的可复核证据才能改变 V1.1 优先级。

## 变更记录要求

任何重新设计都应记录：

- 被修改的决策 ID；
- 修改原因；
- 原方案为何不再适用；
- 新方案的生效范围；
- 受影响的文档、数据对象、页面和测试；
- 是否需要迁移历史数据或重新生成报告。
