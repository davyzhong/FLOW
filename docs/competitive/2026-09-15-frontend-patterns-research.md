---
doc_id: FLOW-COMPETITIVE-FE-PATTERNS-20260915
title: 前端/表格/报告交互模式调研——开源产品与行业竞品（五轮对比）
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
related: [./optimization-checklist.md, ./summary-and-positioning.md, ./open-source-bi.md, ./china-financial-bi.md, ../superpowers/plans/2026-09-15-frontend-design-upgrade-proposal.md]
confidentiality: project-internal
---

# 前端/表格/报告交互模式调研（2026-09-15，五轮检索对比）

> 目的：为 FLOW 前端设计升级方案（见关联的计划文档）提供行业依据。调研对象
> 分五层：组件库层、产品层（fintech）、开源 BI 层、设计系统层、国内 BI 层。
> 每条模式标注「可借鉴/需适配/不采纳」与 FLOW 的落地位置。

## 一、组件库层：Tremor / shadcn+TanStack 生态

| 模式 | 内容 | 采纳判断 |
|---|---|---|
| 可组合仪表盘件 | Tremor 35+ 组件：KPI 卡、sparkline、tracker、差值徽章（本期 vs 上期 + 涨跌色）、进度 tracker | **借鉴形状**：FLOW 的 MetricGrid/KPI 卡对齐其 API 形状（值+差值+趋势+徽章），但不引入 Tremor 依赖 |
| 数据表六模式 | TanStack Table headless：排序/分面筛选/列可见性/行选择/虚拟化/服务端模式 | **采纳 headless 路线**：引入 TanStack Table（无样式无渲染，符合 FLOW 确定性/零样式依赖哲学），FlowDataTable 包装 |
| 财务表特征 | 列合计/汇总 footer、tabular-nums 数字对齐、密度变体 | **采纳**：FlowDataTable 内建 summary footer 与 dense 变体 |

来源：[tremor.so](https://tremor.so/)、[tremorlabs/tremor-npm](https://github.com/tremorlabs/tremor-npm)、[shadcn Data Table](https://ui.shadcn.com/docs/components/base/data-table)、[ReUI Data Grid（财务列合计模式）](https://reui.io/components/data-grid)、[38 特性全功能表](https://next.jqueryscript.net/shadcn-ui/data-table-tanstack-tailwindcss/)

## 二、产品层：Ramp / Mercury / Stripe（Role-Metric-Density-Action 框架）

框架：先定主角色 → 主导指标 = 用户打开产品的第一个问题的答案 → 密度校准角色 → 每屏内嵌一个无需寻找的下一步动作。

| 产品 | 模式 | FLOW 适配 |
|---|---|---|
| Ramp（财务团队，高密度） | 首屏 = 「本期省了多少」而非交易列表；驱动 review-flagged / approve-pending 工作流 | **采纳「工作流驱动首屏」**：经分专员首屏应是「待办」——待审批草稿、待补数据、异常指标，而非平铺图表 |
| Mercury（创始人，低密度） | 余额+趋势为唯一一级信息；浅层导航一触即达 | **借鉴浅导航**：两级导航不再加深；每页回答一个主问题 |
| Stripe（开发者，极高密度） | 信任来自完整性：每条日志可操作、每个错误码链到文档、每笔可复现；**警示：不搬结构逻辑只搬视觉 = 高深的噪音** | **核心采纳**：FLOW 的证据溯源 = 同一哲学——每个数字可点开页码锚、每个口径链接标定义、每个快照可复现；这是「确定性+证据链」的前端表达 |

来源：[Fintech Dashboard Design — Ramp, Mercury & Stripe Patterns](https://www.themasterly.com/blog/fintech-dashboard-design-guide)、[Mercury Design Breakdown](https://www.925studios.co/blog/mercury-design-breakdown)

## 三、开源 BI 层：Metabase / Superset / Lightdash

- **语义层优先**：Metabase 每个答案锚定语义层（指标与业务逻辑），用户可展开查看查询——与 FLOW 指标字典「口径先行」同构，**强化既有方向**；
- Lightdash（dbt 生态）：指标定义即代码，页面只做投影——FLOW 指标字典 YAML 化同路线；
- Superset：面向 SQL 用户的探索式分析——FLOW 不做探索式 BI（范围外，D052）。

来源：[Metabase](https://www.metabase.com/)、[Kanopy：Metabase vs Superset vs Lightdash](https://kanopylabs.com/blog/metabase-vs-superset-vs-lightdash)

## 四、设计系统层：IBM Carbon / Atlassian

| 模式 | 内容 | 采纳判断 |
|---|---|---|
| 空态三分类 | 首次使用 / 无数据 / 操作结果空，各自文案与动作不同 | **采纳**：EmptyGuide 组件区分 first-use vs no-data vs post-action |
| 表空态替代表 | Carbon：空态替换整表（不保留表头/底栏） | **采纳 Carbon 方案**：表头无数据时是噪音 |
| 空态内嵌动作 | Atlassian：创建内容的动作直接内嵌在空态里 | **采纳**（F1-3 已实现雏形，升级为标准件） |
| 密度变体 | Carbon 官方 dense table 变体 | **采纳**：dense 作为 FlowDataTable 变体（经分专员高密度偏好） |

来源：[Carbon Empty states pattern](https://carbondesignsystem.com/patterns/empty-states-pattern/)、[Carbon Data table usage](https://carbondesignsystem.com/components/data-table/usage/)、[Atlassian Empty state](https://atlassian.design/components/empty-state)、[NN/g Empty States](https://www.nngroup.com/articles/empty-state-interface-design/)

## 五、国内 BI 层：观远 / Quick BI / Wind·iFinD / 帆软

| 能力 | 模式 | 采纳判断 |
|---|---|---|
| 钻取（观远） | 固定路径多层钻取 + 卡片跳转 + 多表联动，无代码配置 | **借鉴路径配置思想**：FLOW 以确定性引擎出下钻路径，不做自由拖拽配置 |
| 中国式复杂报表（Quick BI 电子表格） | 表内小计/合计/多级表头 | **延后**：当前报告为快照渲染非自由制表；引入时走 Excel 共生路线 |
| 导出控制（Quick BI） | 导出文件级权限 | **采纳**：发布产物下载已有授权面，补导出审计 |
| Excel 动态链接（Wind） | Excel 函数直连终端数据 | **远期采纳**：即 E4「Excel 共生导出（数字带溯源批注）」路线 |
| 统一口径（帆软/指标中台） | 指标中台保证看板一致 | **已满足**：指标字典 + 确定性引擎即 FLOW 语义层 |

来源：[观远钻取](https://docs.guandata.com/product/bi/659651697299161088)、[观远 24 年功能](https://docs.guandata.com/product/bi/Key-Features)、[FineReport 杜邦分析对比](https://www.finereport.com/blog/article/68db520fd2527e0eb7049a7f)

## 六、Guided Analytics / 渐进披露

- 渐进披露：随用户成熟度逐步放开复杂度，而非首屏全给；
- Guided Analytics：正确的信息、正确的时机、正确的数量；
- 5 秒规则：打开仪表盘 5 秒内应能判断「经营健康度」。

来源：[Power BI Dashboard UI/UX Audit Framework](https://www.linkedin.com/pulse/power-bi-dashboard-uiux-audit-framework-ahmad-chamy-zfkuc)

## 七、对 FLOW 的十条综合结论（v2，2026-09-15 用户纠正后修订）

> v1 曾结论「不引入 Tailwind/Tremor」，被用户正确质疑：**有成熟组件库就引用，
> 不自研**。v1 的论据（token+纯 CSS 已成体系）属沉没成本谬误——「风格不统一、
> 工程差」的病根恰恰是全部手写。修订如下（v2 覆盖 v1 的第 1/3/4 条）：

1. **引入 Tailwind v4 + shadcn/ui**（官方支持 React 19；v4 的 `@theme` CSS-first
   配置与既有 `--rep-*` token 直接融合，存量 CSS 渐进共存）——自研六类基础
   样式与手写图表迁移到行业标准组件；
2. **引入 TanStack Table（headless）+ TanStack Query**：表格能力（排序/筛选/
   虚拟化/列管理）与数据获取（缓存/重试/去重）均用行业标准，替换自研
   useApiQuery 与手写表格逻辑；
3. **表格升级为 FlowDataTable**（shadcn Data Table 模式）：dense 变体、summary
   footer（列合计）、tabular-nums、空态整表替换（Carbon 模式）；
4. **图表引入 Recharts**（shadcn charts 底座）：手写 SVG 瀑布/环形/柱状图迁移——保留确定性数据契约，渲染层换行业标准；
5. **首屏工作流化**（Ramp 模式）：待审批草稿、待查异常指标、未完成构建作为默认视图的组成部分；
6. **空态标准化**（Carbon/Atlassian）：EmptyGuide = 标题 + 为什么空 + 内嵌下一步动作 + 文档链接，区分 first-use/no-data/post-action；
7. **浅导航纪律**：两级封顶（Q&A 已确认），页面内用锚点分区不再加层级；
8. **导出控制与审计**：下载动作写入审计（对齐导出权限模式）；
9. **钻取走确定性路径**：指标卡 → 行项目 → 原文页，路径由引擎给出，不做自由配置；
10. **渐进披露**：治理操作、高级筛选默认折叠；报告页先结论后证据（结论卡 → 证据表 → 原文）。
