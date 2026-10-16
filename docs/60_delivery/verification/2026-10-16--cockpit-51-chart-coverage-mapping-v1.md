---
doc_id: FLOW-VERIFY-COCKPIT-CHART-COVERAGE-20261016-001
title: CFO 驾驶舱 51 图覆盖映射验收
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-10-16
updated_at: 2026-10-16
owner: FLOW
commit_refs: "[14016297]"
evidence_refs: "[module-api-tests, web-vitest, navigation-spec, production-build]"
applies_to: cockpit
supersedes: []
superseded_by: null
---

# CFO 驾驶舱 51 图覆盖映射验收

## 结论

原型 v2.0 的 51 个图表（设计文档验证 51/51 渲染成功）已按十模块全部映射到实现页面。
8 个模块页面（总览 + 7 子模块）交付真实数据链路（两期披露财报归一化行），2 个模块
按设计文档降级处理（合并→主体对比，数据中心→复用 /data）。每个图表有来源事实、
可复算派生值或明确 unavailable 状态，不留静态占位。

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

实现分两层：
1. **数据基线层**（本轮交付）：每模块 KPI 网格 + 图表数据表（期间×系列）+ 降级块五态。
   所有值来自披露财报归一化行（千元→百万元），带 report_ids 和 snapshot_id 可追溯。
2. **ECharts 视图层**（渐进增强）：`charts/builders.ts` 已有 10 类构建器
   （buildCombo/buildDonut/buildWaterfall/buildRadar/buildGauges/buildDupont/buildRankBar/
   buildAgingBars/buildHeatmap/buildQuadrant）。批次 C-1 已集成 ECharts 6.1.0。
   模块页当前以数据表为基线，ECharts 视图按 builders 逐图增强（不阻塞本验收——
   数据契约已成立，视图层增强是 UI 迭代）。

## 验收门禁

| 门禁 | 结果 |
|---|---|
| 模块 API 测试（balance-sheet/working-capital 3 项） | ✅ 3/3 |
| 行动项 API 测试（401/403/cfo 闭环/不可变+审计） | ✅ 4/4 |
| 安全测试（授权矩阵/principal/route_policy 双向） | ✅ 60/60 |
| 发布链测试（freeze/four_stage/publishing_api/operations） | ✅ 40/40 |
| 迁移测试（up/down/up + 0032 head） | ✅ |
| Web vitest（含 module-page + action-panel + 状态覆盖） | ✅ 174/174 |
| typecheck (tsc --noEmit) | ✅ |
| lint (eslint) | ✅ |
| 生产构建 (pnpm build) | ✅ |
| 文档门禁 m1 | ✅ |
| 同 SHA CI | 本提交触发 |

## 已知限制（不阻塞验收）

- 利润增长/盈利能力模块页面复用总览页 KPI（原型有独立页，实现按数据同源合并）；
  C 阶段后续可拆独立路由。
- ECharts 视图层为渐进增强（数据表为基线）；批次 C-1 已引入 ECharts 6.1.0 与
  10 类构建器，逐图增强属 UI 迭代不阻塞数据验收。
- 部分图表因申请稿披露范围限制显式 unavailable（利息保障、净杠杆、账龄、收现比、
  期限拆分），每项在模块端点 `unavailable` 数组中带原因码。
