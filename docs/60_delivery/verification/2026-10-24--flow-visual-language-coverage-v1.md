---
doc_id: FLOW-VERIFY-VISUAL-LANGUAGE-20261024-001
title: FLOW 可复用视觉语言与全项目视觉覆盖验收
doc_type: verification
status: in_progress
version: 1.0
created_at: 2026-10-24
updated_at: 2026-10-24
owner: FLOW
applies_to: repository
---

# FLOW 可复用视觉语言与全项目视觉覆盖验收

## 当前状态

本记录是仍在执行中的视觉统一验收，不表示全部视觉差距已经关闭。阶段性截图位于 [`visual-language-20261024/`](visual-language-20261024/)，其中 `results.json` 保存每条路由、视口、HTTP 状态、横向溢出和浏览器错误摘要。

- 浏览器：Chromium / Playwright，生产 standalone Web 构建；API 与 Web 均在本机隔离进程运行。
- 视口：桌面 1440×1000、平板 1024×900、手机 390×844；20 路由共 60 组。
- 视觉验收数据：仅使用临时目录 `/tmp/flow-visual-audit-20261024` 中的大麦 synthetic 演示数据；release manifest SHA-256：`6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`。没有接入常驻或用户数据库。
- 动态调查详情使用隔离 finding `01a16e5e-e2a6-725a-83cb-aa5d70ac92cb`。
- 截图代码基线：`codex/flow-visual-language` 分支当前工作树（基线提交 `8115e5d242b966cc28c68b2db043e7c1fb2252f2` 加本轮未提交改动）；提交后仍需将提交 SHA 回填并重采图。
- 截图体积：约 22 MB；仅用于当前实现与概念图逐页比对，不覆盖旧版截图资产。

## 路由覆盖

修复 `/operations` 报告读取端点的 UUID 参数类型后，60 组路由视口均为 HTTP 200、无横向溢出、无前端错误；页面从加载态离开后截图。矩阵结果保存在 `results.json`，统计为 `total=60, bad=0`。这只代表页面路由、渲染和溢出检查通过，不代表每个页面、交互状态或图表已完成概念图逐项视觉验收。

| 路由 | 覆盖视口 | 当前验收备注 |
|---|---|---|
| `/` | 1440 / 1024 / 390 | 完成截图与溢出/浏览器错误检查 |
| `/analysis` | 1440 / 1024 / 390 | 同上 |
| `/cockpit` | 1440 / 1024 / 390 | 图表、行动、来源数据已加载；synthetic 事实明确标注 |
| `/cockpit/balance-sheet` | 1440 / 1024 / 390 | 完成截图与溢出/浏览器错误检查 |
| `/cockpit/cashflow` | 1440 / 1024 / 390 | 同上 |
| `/cockpit/consolidation` | 1440 / 1024 / 390 | 同上 |
| `/cockpit/expenses` | 1440 / 1024 / 390 | 同上 |
| `/cockpit/profitability` | 1440 / 1024 / 390 | 同上 |
| `/cockpit/risk` | 1440 / 1024 / 390 | 同上 |
| `/cockpit/working-capital` | 1440 / 1024 / 390 | 同上 |
| `/data` | 1440 / 1024 / 390 | 完成截图；导入/映射交互仍需专门覆盖 |
| `/internal` | 1440 / 1024 / 390 | 完成截图与溢出/浏览器错误检查 |
| `/investigations` | 1440 / 1024 / 390 | 同上 |
| `/investigations/01a16e5e-e2a6-725a-83cb-aa5d70ac92cb` | 1440 / 1024 / 390 | 隔离 Finding 详情截图完成 |
| `/login` | 1440 / 1024 / 390 | 登录页视觉单独检查；不包 AppShell |
| `/metric-library` | 1440 / 1024 / 390 | 完成截图；搜索、筛选和键盘状态仍需专门覆盖 |
| `/operations` | 1440 / 1024 / 390 | UUID 类型修复后完成数据态截图与溢出/浏览器错误检查 |
| `/public` | 1440 / 1024 / 390 | 完成截图与溢出/浏览器错误检查 |
| `/reports` | 1440 / 1024 / 390 | 完成截图；报告生成、下载交互仍需专门覆盖 |
| `/statements` | 1440 / 1024 / 390 | 完成截图与溢出/浏览器错误检查 |

## 视觉方向与剩余工作

本轮已经建立 `packages/flow-visual-language/` 可移植视觉语言包，包含语义 token 唯一源、生成 CSS、React/报表消费映射、模式手册和无经营事实的静态 specimen；网页共享主题、外壳、主要页面的颜色 token、ECharts / SVG 财务图色板及离线驾驶舱预览已开始消费该包。

仍需完成：

1. 按截图逐页对照概念板的版式、字体、内容层级、表格/筛选器、图表、来源区与窄屏状态，补齐所有页面级固定颜色与字形；不能仅以无溢出代替视觉一致性。
2. 逐一登记页面内图表和数据表达，并核对每幅图标题、单位、图例、来源、空/错/降级状态及等价数据表；当前路由截图矩阵没有替代逐图表清点。
3. 完成 HTML、PDF、PPTX、XLSX 及离线包全量视觉映射与打印检查；当前仅处理图表配色映射和离线驾驶舱 CSS。
4. 执行键盘焦点、放大阅读、颜色对比、搜索/筛选和页面交互状态核验；核对全部剩余 CSS 与导出格式映射。
5. 最终提交后以准确代码 SHA 重新采集截图，更新结果与文件清单，完成 M1/M6、计划视图、链接检查及独立复核。

此报告链接至 [视觉语言设计规格](../../superpowers/specs/2026-10-24-flow-visual-language-system-design.md)、[全项目视觉统一工作包](../../50_plans/work_items/FLOW--portable-visual-language-and-full-project-restyle.md)、[截图矩阵 JSON](visual-language-20261024/results.json) 和 [可复用视觉语言包](../../../packages/flow-visual-language/README.md)。
