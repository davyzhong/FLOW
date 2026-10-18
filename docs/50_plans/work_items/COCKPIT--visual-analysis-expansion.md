---
doc_id: FLOW-WI-COCKPIT-VISUAL-ANALYSIS-20261017-001
title: CFO 驾驶舱盈利分析与图表缺口补全
doc_type: work-item
status: completed
version: "1.1"
created_at: 2026-10-17
updated_at: 2026-10-17
owner: FLOW
depends_on: [FLOW-WI-COCKPIT-CFO-001, FLOW-WI-COCKPIT-VISUAL-20261017-001]
acceptance_refs: [FLOW-VERIFY-COCKPIT-CHART-COVERAGE-20261016-001]
applies_to: cockpit
supersedes: []
superseded_by: null
---

# CFO 驾驶舱盈利分析与图表缺口补全

> 状态：已完成并待本轮提交推送。交付包括杜邦盈利能力页面、冻结期指标与来源行深链、两期图表、接口契约与权限登记。详细实现及验证结果记录在 CURRENT_ROADMAP 和 HANDOFF。

## 目的

在现有驾驶舱交付上补齐独立盈利能力分析及已核实的图表缺口，核心是把指标库已有的杜邦三因子以真实、可访问、可追溯的页面呈现。不是重做已验收的 51 图覆盖和现有趋势/结构图。

## 范围与约束

- 页面：新增 `/cockpit/profitability`，杜邦分解、期间对比、指标数据表、定义与来源深链。
- 数据：只读已发布 `MetricSnapshot` / `MetricValue`、`ReportSnapshot` 或客观财报 `ObjectiveReportSnapshot`；每个上屏数字携带实际快照 ID。财务派生指标必须在现有 Objective 快照创建阶段按指标字典公式计算、保存定义版本与行级来源轨迹，Cockpit 路由和页面只读，禁止实时重算。
- 扩展 Objective 快照 JSON payload 版本，不修改数据库表结构；旧 v1 快照不改写，继续兼容并将缺少分析指标的页面内容显示为 unavailable。只有显式冻结/重冻结动作可生成含指标值的新不可变快照。
- 总览/其余模块：只按实际页面和 API 现状核对，已交付图表不重复开发。无数据时如实呈现不可用原因。
- 复用 ECharts、`buildDupont`、`ChartBox`、已有格式器、指标字典、权限和聚合端点模式；不增加依赖、不改 schema/迁移/CI。

## 验收标准

1. 新路由使用 AppShell，导航注册并纳入 navigation 守护测试。
2. 新 Objective 快照创建时保存遵守指标字典平均余额口径的 ROE、净利率、总资产周转率、权益乘数与 calculation trace；杜邦乘积勾稽差异及通过/失败一并冻结。新快照页面展示杜邦关系和对比图；旧 v1 快照缺少冻结值时标明 unavailable，不伪造图表。
3. 数值携带快照、指标定义和报告来源身份，链接目标正确；访问控制沿用现有单企业权限。
4. 加载、错误、无数据、窄屏、键盘与数据表状态可用；图表与表格数值一致。
5. 隔离数据测试、API/Web 定向测试、typecheck/lint/build、浏览器验收、M1 与契约检查通过。

## 实施计划

[实施计划](../../superpowers/plans/2026-10-17-cockpit-visual-analysis-expansion.md)；[设计规格](../../superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)。唯一执行顺序与进度仅见 [CURRENT_ROADMAP](../CURRENT_ROADMAP.md)。
