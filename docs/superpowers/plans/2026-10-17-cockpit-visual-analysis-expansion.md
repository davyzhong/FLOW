---
doc_id: FLOW-PLAN-COCKPIT-VISUAL-ANALYSIS-20261017-001
title: CFO 驾驶舱盈利分析与图表缺口补全实施计划
doc_type: plan
status: active
version: "1.1"
created_at: 2026-10-17
updated_at: 2026-10-17
owner: FLOW
depends_on: [FLOW-SPEC-COCKPIT-VISUAL-ANALYSIS-20261017-001]
acceptance_refs: [FLOW-WI-COCKPIT-VISUAL-ANALYSIS-20261017-001]
applies_to: cockpit
supersedes: []
superseded_by: null
---

# CFO 驾驶舱盈利分析与图表缺口补全实施计划

## 目标

在已交付驾驶舱基础上实现真实、可视、可追溯的盈利能力/杜邦分析，并按现状证据只补实际缺失且数据充分的图表。严格复用 ECharts 和 FLOW 已有财务事实链，不制造菜鸟经营数据、不引入新的计算事实源。

## 执行顺序与验收

### 1. 核实冻结指标数据可用性与当前视觉缺口
- 对照 51 图验收记录、最新隔离账套接口载荷及已有路由截图，列明已完成视图、缺少视图、缺少数据的具体边界。
- 检查当前客观财报快照 schema、指标字典及报表行来源定位，确定新旧快照兼容边界；已有发布 `MetricSnapshot` / `ReportSnapshot` 指标直接复用。
- 扩展 Objective 快照冻结服务，在显式快照创建时使用既有指标字典定义及平均余额规则计算 ROE、净利率、总资产周转率、权益乘数，并将值、字典/公式版本、分子分母 trace、source report ID、原始行锚点及乘积勾稽状态写入不可变 JSON payload；递增 payload schema version，旧版本不变更。
- 验收：测试证明冻结内容确定、哈希包含分析载荷、无必需输入时返回 unavailable 原因、精度按公式规则处理；逐指标身份/来源完整。

### 2. 后端读取聚合与契约
- 复用已发布快照和现存报告 lineage；单个盈利能力聚合接口只读取客观财报冻结载荷，不触碰原始归一化行、不计算比率。
- 扩展 Objective snapshot GET 投影以返回冻结分析摘要；增加只读盈利能力聚合路由，沿用已批准的企业域权限与 loader，不增 Action。
- 不改数据库表 schema/迁移、CI；旧版快照返回 typed unavailable，绝不隐式冻结或重冻结。
- 验收：响应中的每个数值有 `metric_snapshot_id`、定义身份、期间、来源报告；越权、缺失和不完整口径均 fail-closed/unavailable。

### 3. 盈利能力页面与图表
- 新增 `/cockpit/profitability` 页面、AppShell、左侧导航登记、导航守护测试登记。
- 复用 `buildDupont`、`ChartBox` 和既有格式器；可视化包括杜邦因子树、两期因子比较、利润率/ROE 期间比较、数值数据表和口径说明。
- 每个数值提供指标定义与报告来源深链；键盘/读屏可通过表格获取相同信息，色彩不作为唯一编码。
- 验收：实际浏览器中图表可见且可访问；无可用指标时呈现逐项原因，不伪造线段、零值或长时间序列。

### 4. 总览与其他模块缺口核对及必要补齐
- 对照现有 API 响应和截图，逐项检查收入/利润、现金流、资产/负债结构和 DuPont 入口，不重建已存在图表。
- 只实现可由现有冻结数据直接呈现的缺失项；其他数据状态、图表状态和解释通过显式 unavailable 表达。
- 验收：所有已显示数字均与接口逐项一致且能追溯；无数据不补零。

### 5. 验证、交付与交接
- API 定向 pytest、web 定向单测、`pnpm typecheck`、lint、生产构建、导航 E2E、隔离账套 API/Playwright 验收。
- 在隔离数据源运行，不重置常驻数据；保存浏览器实际截图和验证记录，更新工作包、路线图和 HANDOFF。
- `python3 scripts/check_docs.py --phase m1`、链接检查、契约检查按实际变更运行。
- 由独立上下文审查最终 diff；只修复影响正确性/验收的问题。
- 验证结果核对准确提交 SHA；通过后 conventional commit 并立即 push，记录 CI run。

## 明确不做

不新增图表库；不编造长期趋势/预算/预测/行业基准；不重算已发布事实；不进行 schema/迁移/CI 改动；不改动原始财报、常驻账套和其他 worktree。
