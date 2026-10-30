---
doc_id: FLOW-VERIFY-CONCEPT-CHART-20261030-001
title: 概念板图表统一收尾验收
doc_type: verification
status: draft
version: 1.0
created_at: 2026-10-30
updated_at: 2026-10-30
owner: FLOW
commit_refs: "[e7e2be03d27ff472894ce35170e534c411a47d67]"
evidence_refs: "[web-vitest-221, web-typecheck, web-build, statement-chart-pytest-6, isolated-route-matrix-60, manual-screenshot-review-8]"
applies_to: repository
---

# 概念板图表统一收尾验收

## 结论

本轮针对用户指出的“饼图、柱状图等图表与概念图视觉方案不一致”完成剩余差距修正。最终实现以代码提交 `e7e2be03d27ff472894ce35170e534c411a47d67` 为准：普通趋势、KPI 微图、瀑布图、期间分组柱和现金流类别色已统一为概念板的墨蓝、古金、翡翠绿与中性灰语义；未修改业务数据、指标口径、数据库 schema 或 CI 配置。

准确代码 SHA 下，隔离演示数据的 20 个路由 × 3 个视口共 60/60 组均为 HTTP 200 且内容就绪，bad、API 错误、浏览器错误、外部请求和页面横向溢出均为 0。本文及截图目录是本轮最终证据；早期截图保留在原目录，不覆盖历史记录。

## 最终修正

| 对象 | 最终表达 | 验证重点 |
|---|---|---|
| 普通趋势线 | 移除面积填充，以线条、标记、图例和同值表表达趋势 | 不再用大色块淹没网格与数据结构 |
| 收入与营业利润趋势 | 两项共用同一亿元刻度，不强制双 Y 轴 | 页面明确说明同一刻度，避免双轴造成视觉误读 |
| 收入、营业利润、经营现金流 KPI | 最近三期零基线微柱；正值向上、负值向下 | 营业利润亏损不再退回折线，方向与零基线可读 |
| 瀑布图 | 增加项使用翡翠绿，与 SVG 瀑布一致；负向及总计沿用既有结构语义 | ECharts 与手绘 SVG 不再对同一增加语义使用不同颜色 |
| 财报期间分组柱 | 本期墨蓝、上期中性灰；负值不自动改风险红 | 颜色表示期间与类别，数值正负由零轴、方向和标签表达 |
| 现金流三类 | 经营墨蓝、投资古金、筹资翡翠绿 | 类别颜色跨期间保持稳定，不因正负改变类别色 |
| 视觉规范 | `patterns.md` v1.1 补充趋势、微图、瀑布与现金流色义 | token 生成物和图表例外具有同一可复用规则 |

## 证据绑定

- 代码：`e7e2be03d27ff472894ce35170e534c411a47d67`。
- 最终矩阵：[`results.json`](visual-language-20261030-concept-closeout/results.json)，采集时间 `2026-10-30T01:19:54.686Z`。
- 隔离数据目录：`work/flow-visual-audit-20261030-concept-closeout`，未纳入提交。
- 发行包 manifest SHA-256：`6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`。
- 动态调查详情使用隔离 Finding `01a18a60-e6b4-7485-83cd-95e2943d52e1`。
- 视口：桌面 1440×1000、平板 1024×900、手机 390×844。
- 修改前证据：[`visual-language-20261030/`](visual-language-20261030/)；最终证据：[`visual-language-20261030-concept-closeout/`](visual-language-20261030-concept-closeout/)。

## 路由与视口矩阵

| 指标 | 结果 |
|---|---:|
| 路由 × 视口 | 20 × 3 = 60 |
| HTTP 200 / 内容就绪 | 60 / 60 |
| bad | 0 |
| API 错误 | 0 |
| 浏览器错误 | 0 |
| 外部请求 | 0 |
| 页面横向溢出 | 0 |

路由为 `/`、`/analysis`、`/cockpit`、六个驾驶舱主题页及 `/cockpit/profitability`、`/data`、`/internal`、`/investigations`、隔离调查详情、`/login`、`/metric-library`、`/operations`、`/public`、`/reports`、`/statements`。逐项状态和截图文件名见最终结果 JSON。

## 重点截图目检

重新打开并检查以下 8 张最终截图，重点核对图表色义、趋势与微柱形态、零轴、图例、同值表及窄屏阅读流：

1. [驾驶舱总览 · 桌面](visual-language-20261030-concept-closeout/cockpit--desktop.png)：趋势无面积填充；收入/利润同轴；现金桥增加项为绿；KPI 微柱可见。
2. [驾驶舱总览 · 手机](visual-language-20261030-concept-closeout/cockpit--mobile.png)：图表按内容流纵向排列，无页面级横向溢出。
3. [现金流 · 桌面](visual-language-20261030-concept-closeout/cockpit--cashflow--desktop.png)：经营/投资/筹资固定为蓝/金/绿，负值仍保留类别色。
4. [费用分析 · 桌面](visual-language-20261030-concept-closeout/cockpit--expenses--desktop.png)：环图、分组柱、堆叠柱和趋势使用有限品牌色阶。
5. [公开财报 · 桌面](visual-language-20261030-concept-closeout/statements--desktop.png)：期间分组柱以蓝/灰区分，负值不自动变红；瀑布增加项为绿。
6. [公开财报 · 手机](visual-language-20261030-concept-closeout/statements--mobile.png)：图表、明细表和来源说明保留窄屏阅读路径。
7. [盈利能力 · 桌面](visual-language-20261030-concept-closeout/cockpit--profitability--desktop.png)：杜邦关系和两期比较保持墨蓝/古金/翡翠绿层级。
8. [营运资金 · 桌面](visual-language-20261030-concept-closeout/cockpit--working-capital--desktop.png)：趋势及效率比较使用统一线色、图例和同值表。

## 自动化复验

| 检查 | 实际结果 |
|---|---|
| `apps/web`: `pnpm test` | 40 个测试文件，221/221 通过 |
| `apps/web`: `pnpm typecheck` | 通过 |
| `apps/web`: `pnpm lint` | 0 error；5 条既有 warning |
| `apps/web`: `pnpm build` | Next.js production build 通过 |
| API 定向 pytest | 6/6 通过 |
| 对应 Ruff | 通过 |
| `python3 scripts/build_flow_visual_language.py --check` | 通过 |
| 最终隔离矩阵 | 60/60 ready；错误、外部请求、溢出均为 0 |
| GitHub Actions | 代码 SHA 对应 run `40985033178`，28/28 jobs success |

## 范围与限制

- 本轮只统一视觉表达，不重算或改写财务事实，不启动 K3/K4–K6，不读取全量知识库，不启动银行流水交叉核对或下一产品工作包。
- 截图使用隔离 synthetic 演示数据，不能作为真实经营事实或公开财报准确性的证明。
- 390 CSS px 手机视口仅验证响应式布局，**不等价于原生浏览器 200% 缩放**。原生 200% 缩放仍需在设备解锁且具备可控缩放工具时单独补验。
- 临时 API/Web 采集进程已关闭；常驻 `make flow` 服务及其数据未用于隔离验收。
