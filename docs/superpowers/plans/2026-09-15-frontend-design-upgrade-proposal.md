---
doc_id: FLOW-PLAN-FE-DESIGN-UPGRADE-20260915
title: 前端设计升级方案 v1（基于五轮竞品调研）
doc_type: plan
status: proposed
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
depends_on: [FLOW-WP-PUBLIC-C-EXIT-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: web-frontend
research_refs: [../competitive/2026-09-15-frontend-patterns-research.md]
decision_refs: [D052, D053]
---

# 前端设计升级方案 v1（基于五轮竞品调研）

> 依据 [前端交互模式调研](../../competitive/2026-09-15-frontend-patterns-research.md)
> 的十条结论，给出 FLOW 前端从「可用」到「专业可信」的设计升级路线。
> 定位判断（调研依据）：FLOW 的主用户是**经分专员**（专业角色），密度应当
> 中偏高；产品主张是「确定性 + 证据链」——前端的核心任务是把这个主张
> **翻译成可点的交互**，而不是堆图表。

## 0. 设计原则（四条，全部有调研出处）

1. **证据完整性即信任**（Stripe 模式的 FLOW 版）：每个数字可点开溯源卡
   （值/口径/单位/来源报告/PDF 页码锚），每个口径链接指标字典定义，
   每个快照可复现下载；
2. **首屏工作流化**（Ramp 模式）：经分专员打开产品第一眼是「待我处理」
   ——待审批草稿、异常指标、未完成构建——而非平铺图表；
3. **渐进披露**（Guided Analytics）：页面先结论后证据（结论卡 → 证据表 →
   原文）；治理操作与高级筛选默认折叠；
4. **密度校准**（Carbon dense 变体）：专业角色给 dense 表格与紧凑指标带，
   不为演示美观牺牲信息密度。

## 1. 分阶段落地路线

### 阶段一（已完成，本分支）：地基
token 体系（globals.css 变量扩容 + 223 处硬编码收编）、六类 flow-* 基础
样式、导航两级重组、落地页功能入口、空态引导雏形、reports-center API
收编 + useApiQuery hook。即已完成的前端整体优化批次。

### 阶段二：表格与溯源（核心差异化，建议下一 Gate 主力）
| 项 | 内容 | 调研出处 |
|---|---|---|
| F-DataTable | 引入 TanStack Table（headless 唯一新依赖），封装 FlowDataTable：排序/分面筛选/列可见性/dense 变体/summary footer/tabular-nums | 组件库层 |
| F-Provenance | 溯源卡组件：数字 hover → 卡片（值/口径/单位/来源/页码），点击 → 原文页；数据源 = 已入库的 page_number/page_anchor | Stripe 模式 + B3 已有数据 |
| F-EmptyGuide | 空态标准组件：{ kind: first-use/no-data/after-action } + 原因 + 内嵌动作 + 文档链接；表空态整表替换 | Carbon/Atlassian |
| F-ExportAudit | 下载/导出动作写审计事件 | Quick BI 导出控制 |

### 阶段三：页面模式升级（依赖阶段二组件）
| 项 | 内容 |
|---|---|
| P-WorkbenchHome | 经分专员首屏工作流化：待办区（草稿审批/异常指标/未完成构建）+ hero 指标带（一个主问题一个答案） |
| P-DrillPath | 指标卡 → 行项目 → 原文页的确定性下钻路径（引擎给出路径，非自由配置） |
| P-ReportFlow | 报告页渐进披露：结论卡 → 证据表 → 原文；导出区带权限与审计 |
| P-GovernanceFold | 治理操作渐进披露：操作区默认折叠，事件流先摘要后全量 |

### 阶段四（远期，登记不排期）
- Excel 共生导出（数字带溯源批注，Wind/观远模式，即 E4）；
- 中国式复杂报表电子表格（Quick BI 模式，需自由制表需求成立后）；
- 多主题（暗色）与打印样式。

## 2. 明确不采纳（防范围蔓延）

- Tailwind / Tremor / MUI / antd 等样式或组件框架（token+纯 CSS 已成体系）；
- 探索式自由 BI（Superset 路线，D052 范围外）；
- 拖拽式仪表盘编辑器（观远模式——与确定性产品主张冲突）；
- 深层导航/多级菜单（浅导航纪律）。

## 3. To-do（按阶段领取，须过路线图裁决）

- [ ] 阶段二 F-DataTable：FlowDataTable 组件 + dashboard 资产表/statement 明细表迁移（TanStack 引入 + 5 用例）
- [ ] 阶段二 F-Provenance：溯源卡组件 + statements 页数字接入（page_number 数据已就绪）
- [ ] 阶段二 F-EmptyGuide：标准空态组件 + 三类空态迁移（dashboard/operations/reports）
- [ ] 阶段二 F-ExportAudit：下载审计事件（后端 require_action 已覆盖授权，补审计行）
- [ ] 阶段三 P-WorkbenchHome：首屏待办工作流
- [ ] 阶段三 P-DrillPath/P-ReportFlow/P-GovernanceFold
- [ ] 每项验收：e2e + 组件测试 + 视觉走查 + 同 SHA CI 绿

## 4. 依赖与风险

- TanStack Table 为新增前端依赖（headless、无样式、MIT）——相对收益明确，
  需用户确认后引入；
- 溯源卡依赖 10 条抽取错误候选人工查源关闭后的干净数据；
- 视觉走查每阶段一次，防止「样式统一」演变为「全局重设计」。
