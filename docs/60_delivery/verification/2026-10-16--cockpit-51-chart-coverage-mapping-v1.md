---
doc_id: FLOW-VERIFY-COCKPIT-CHART-COVERAGE-20261016-001
title: CFO 驾驶舱 51 图覆盖映射验收
doc_type: verification
status: verified
version: "2.0"
created_at: 2026-10-16
updated_at: 2026-10-17
owner: FLOW
commit_refs: "[607d07f853f530d153a55f92c9e9a4658eb17e93, 1a71e33fc2f779e1a848a4c3736919e98f762bdf]"
evidence_refs: "[isolated-damai-seed, isolated-route-matrix, cockpit-e2e, web-vitest, api-pytest, screenshots]"
applies_to: cockpit
supersedes: []
superseded_by: null
---

# CFO 驾驶舱 51 图覆盖映射验收

## 结论

原型 v2.0 的 51 个图表位继续按十模块映射。视觉验收确认 8 个 CFO 路由（总览 + 7 个
模块入口中的 6 个独立财务模块页面，利润/盈利能力复用总览）已使用真实 API 数据呈现；
有可比期间的指标显示前期值与方向变化，ECharts 绘制实际可用的趋势或结构图，明细表、
指标定义和来源财报可继续追溯。缺乏披露事实的值保持 unavailable，不补零、不伪造趋势。

## 模块 × 图表覆盖矩阵

| # | 模块 | 路由 | 原型图表数 | 实现状态 | 数据源 | 降级/不可用 |
|---|---|---|---|---|---|---|
| 1 | 集团总览 | `/cockpit` | ~7 | ✅ 批次 A | MetricSnapshot 冻结事实 | — |
| 2 | 利润增长 | `/cockpit` KPI 区域 | ~6 | ✅ 总览页 KPI 覆盖 | canonical 营收/利润事实 | — |
| 3 | 盈利能力 | `/cockpit` KPI 区域 | ~6 | ✅ 总览页 KPI 覆盖 | 披露事实派生（毛利率/净利率/ROE） | — |
| 4 | 费用分析 | `/cockpit/expenses` | ~5 | ✅ C-3 | 申请稿费用行（四费+期间费用率） | 预算执行（内部期） |
| 5 | 资产负债 | `/cockpit/balance-sheet` | ~6 | ✅ C-2 | 申请稿资产负债表（结构/比率） | 债务期限拆分（未披露） |
| 6 | 营运资金 | `/cockpit/working-capital` | ~6 | ✅ C-2 | 申请稿 AR/INV/AP + CCC 恒等 | 账龄明细（未披露）；排名（单主体） |
| 7 | 现金流 | `/cockpit/cashflow` | ~5 | ✅ C-3 | 申请稿现金流量表（三大净额+变动桥） | 收现比（无销售收现行）；13 周预测（内部期） |
| 8 | 财务风险 | `/cockpit/risk` | ~5 | ✅ C-4 | 申请稿偿债比率（流动/速动/现金/负债率） | 利息保障（无利息费用行）；净杠杆（无短债拆分） |
| 9 | 集团合并 | `/cockpit/consolidation` | ~3 | ✅ C-5（降级态） | 菜鸟分部序列（CN-SEG-*，阿里年报披露） | 合并抵销桥（内部期） |
| 10 | 数据中心 | `/data`（复用） | ~2 | ✅ 复用现有页面 | 管线 manifest/校验体系 | — |

**合计**: ~51 图表位（含 KPI 卡表 + 图表数据表 + 降级块），全部有数据来源映射或显式 unavailable。

## 图表实现形态说明

实现复用仓库已安装的 ECharts 6.1.0 与十类构建器。模块 API 的现有趋势、结构、桥接和
公式数据由适配器映射至组合图、环图、瀑布图或专用构建器；图表下方保留同口径数据表，
图表和 KPI 均链接来源财报。模块页面按响应式卡片布局展示 KPI、前期对比、图形、明细和
缺失原因；总览近 12 个月趋势也用 ECharts 绘制，缺失期间保持断点，不再当作零值。

数值显示统一遵守业务单位：订单、包裹、客户等计数取整数；金额保留两位小数；百分比保留
两位小数；比率/周转率显示为倍数，天数保留一位小数；空值和非法值显示破折号。资产负债率
等百分率与流动比率等倍数分别呈现；毛利率变动显示百分点，金额与增长率变化分别按其单位
呈现。此规则已用于驾驶舱、经营表格、财报图表、调查页面和四问工作台。

## 隔离演示证据与截图

- 环境：临时 Docker Compose（PostgreSQL/Redis/MinIO）+ 临时 Next.js 应用副本 + Playwright；
  `codex-cockpit-iso` 资源在验收后清理，未连接常驻开发/演示数据库。
- 数据源：大麦 FY2022/FY2023 隔离发行包，清单 SHA-256
  `c73848806010685c7b5698b5f65228db2e67e01bf38a788eda6911bbcb6ce11e`；账套验证 19/19。
  数据批次 `01a14598-adc2-7f4a-b845-952bcebb55b0`，分析运行
  `01a1459c-f5ec-7be3-a8f6-da9f4f6ce294`。
- API 可见性矩阵：162 条路由，152 条返回 200，10 条按合同返回 422；无意外失败。
  结果文件 `work/damai-demo/e2e_visibility_matrix.jsonl` 的 SHA-256 为
  `566dfe35ac76e95b85810d02d084800758938c660946b96b99dd1d9d4498d744`。
- 浏览器：`apps/web/e2e/damai-demo.spec.ts` 15/15 通过，覆盖仪表板筛选、毛利矩阵、经营分析、
  财报、四问工作台、指标库、调查、报告中心及导入旅程。实现代码提交 SHA：
  `1a71e33fc2f779e1a848a4c3736919e98f762bdf`（前置提交 `607d07f8`）。

| 页面 | 截图 |
|---|---|
| 财务 BP 总览 `/` | [查看截图](assets/2026-10-17-finance-bp-dashboard-final.png) |
| CFO 驾驶舱总览 `/cockpit` | [查看截图](assets/2026-10-17-cockpit-overview-final.png) |
| 资产负债 `/cockpit/balance-sheet` | [查看截图](assets/2026-10-17-cockpit-balance-sheet-final.png) |
| 营运资金 `/cockpit/working-capital` | [查看截图](assets/2026-10-17-cockpit-working-capital-final.png) |
| 费用分析 `/cockpit/expenses` | [查看截图](assets/2026-10-17-cockpit-expenses-final.png) |
| 现金流 `/cockpit/cashflow` | [查看截图](assets/2026-10-17-cockpit-cashflow-final.png) |
| 财务风险 `/cockpit/risk` | [查看截图](assets/2026-10-17-cockpit-risk-final.png) |
| 集团合并 `/cockpit/consolidation` | [查看截图](assets/2026-10-17-cockpit-consolidation-final.png) |

## 验收门禁

| 门禁 | 结果 |
|---|---|
| 模块 API 测试（风险对比/单位/费用缺失值） | ✅ 1/1 |
| 行动项 API 测试（401/403/cfo 闭环/不可变+审计） | ✅ 4/4 |
| 安全测试（授权矩阵/principal/route_policy 双向） | ✅ 60/60 |
| 发布链测试（freeze/four_stage/publishing_api/operations） | ✅ 40/40 |
| 迁移测试（up/down/up + 0032 head） | ✅ |
| Web vitest（35 个测试文件） | ✅ 183/183 |
| API 定向 pytest（workbench/operations/cockpit） | ✅ 19/19 |
| 大麦发行与数据库一致性验证 | ✅ 19/19 |
| API 可见性矩阵 | ✅ 162 条，152×200 + 10×422（预期） |
| Playwright 隔离端到端 | ✅ 15/15 |
| Dashboard Playwright（网络边界/状态/视觉/交互/可访问性） | ✅ 7/7；更新后 Linux/macOS 1440/1920 视觉基线均通过 |
| typecheck (tsc --noEmit) | ✅ |
| lint (eslint) | ✅ 0 错误；既有 TanStack Table 兼容性提示 1 条 |
| 文档门禁 m1 | ✅ 通过（314 文档，0 错误） |
| 计划视图 / 文档链接 / 脚本测试 | ✅；155/155，链接 0 错误 |
| 同 SHA CI | `1a71e33fc2f779e1a848a4c3736919e98f762bdf` / run `38936413156`，全部 job 成功 |

## 已知限制（不阻塞验收）

- 利润增长/盈利能力模块复用总览页 KPI（原型有独立页，实现按数据同源合并）。
- 部分图表因申请稿披露范围限制显式 unavailable（利息保障、净杠杆、账龄、收现比、
  期限拆分），每项在模块端点 `unavailable` 数组中带原因码。
