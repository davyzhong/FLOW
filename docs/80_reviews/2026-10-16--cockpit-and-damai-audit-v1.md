---
doc_id: FLOW-REVIEW-COCKPIT-AUDIT-20261016
title: CFO 驾驶舱与大麦演示数据独立审计报告
doc_type: review
status: open
version: 1.0
created_at: 2026-10-16
updated_at: 2026-10-16
owner: FLOW
last_reviewed_at: 2026-10-16
applies_to: web-frontend
decision_refs: [D001, D052, D053, D054, D055]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
subject_ref: FLOW-WI-COCKPIT-CFO-001
findings: |-
  详见本报告正文；核心结论：驾驶舱 8 模块全量交付，来源事实门禁和披露边界已落地。
source_refs:
  - docs/50_plans/work_items/COCKPIT--cfo-dashboard-implementation.md
  - docs/50_plans/work_items/FINMETRIC--financial-metric-catalog.md
  - docs/60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md
  - docs/05_design/2026-09-29-cfo-cockpit-design.md
related_code:
  - apps/web/components/cockpit/
  - services/api/src/flow_api/cockpit/
  - config/metrics/damai_demo_metric_coverage_v1.yaml
  - config/damai/source_facts_v1.yaml
commit_refs: ["14016297"]
evidence_refs: []
confidentiality: project-internal
---

# CFO 驾驶舱与大麦演示数据独立审计报告

> 审计基准：`14016297`（批次 D 合入 main）。审计方式：两路独立只读调查 + 主审交叉核对 + 竞品对标。
> **审计性质**：能力与数据完整性审计，不含代码审查；所有结论均标注证据路径，可复核。

## 0. 一句话结论

**架构完整、呈现未完成、数据有条件可用。**

| 维度 | 判定 | 关键数字 |
|---|---|---|
| 大麦物流数据 | 🟡 **有条件可用** | 财务三表已逐行溯源（325 条事实 100% 带 source + 页锚 + SHA）；但件量口径与披露值差 **3.6 倍** |
| CFO 驾驶舱功能 | 🔴 **不可对标竞品** | 模块 8/10；**ECharts 图表实际渲染 0/50**（10 个构建器是死代码）；三会闭环 0 实现 |
| 缺陷 | 🔴 2 个 P0 + 3 个 P1 | 图表全链路断裂、三会闭环缺失 |

---

## 1. 竞品对标基准

| 能力 | 数据熊原型（我们的目标） | 主流财务 BI（帆软/观远类） | FLOW 现状 |
|---|---|---|---|
| 指标卡 | 三基准（同比/环比/行业分位）+ 口径注 | 值 + 同比 + 预算 | ✅ 达标 |
| 图表可视化 | ~50 个图表（趋势/象限/瀑布/仪表/雷达/热力/杜邦/玫瑰/账龄） | 数十至上百 | 🔴 **0 个以 ECharts 渲染** |
| 穿透溯源 | 口径 → 来源 → 结论 → 历史 → 版本 | 部分支持 | ⚠️ 只有前 3 段 |
| 经营结论 | 底部结论条，可溯源 Finding | 多数无 | ✅ 达标 |
| 三会闭环 | 红灯聚焦 / 经分会模式 / 导出管理层版 | 头部厂商有「数字经分会」产品线 | 🔴 **0 实现** |
| 行动项闭环 | create / acknowledge / close | 支持 | ⚠️ **2/3**（缺 close） |
| 数据血缘 | 原件可追溯 | 通常无 | ✅ **超竞品**（325 条 100% 溯源） |

**对标结论**：FLOW 在**数据治理与可追溯**上已超过主流竞品，但在**可视化呈现与经营会场景化**上远落后——这两项恰是驾驶舱的核心价值主张。

---

## 2. 维度一：大麦物流数据完整性

### 2.1 判定：有条件可用

**已修复**（用户 2026-10-12 提出的第一项门禁）：65% 利息拆分、10% 折旧估算、负债/现金流构成拆分**已从 v2 发行包移除**，并在 `config/damai/source_facts_v1.yaml:7309-7325` 登记为 unavailable。

### 2.2 覆盖现状

| 维度 | 覆盖 | 证据 |
|---|---|---|
| 三表期间 | FY2022 / FY2023（财年截止 3-31） | `fixtures/damai/statements/damai_fy2022.yaml:12` |
| 指标覆盖 | **32/50 = 64%**，18 个不可算 | `config/metrics/damai_demo_metric_coverage_v1.yaml:17-27` |
| 不可算原因 | 利息 8 项、短债 4 项、NOPAT 2 项、现金收现/销量/单价等 | 同上 `missing` 字段 |
| 分部 | FY2019–FY2025 收入；FY2026 **unavailable** | `fixtures/damai/operations/damai_segment_series.yaml:9-55` |
| 运营 | 件量 FY2021–FY2023；业务线占比**仅 FY2023** | `damai_operating_metrics.yaml:59-70` |
| 明细维度 | 40 客户 / 4 事业部 / 6 区域 / 8 产品 / 24 月 | `fixtures/damai/manifest.json:3-28` |
| 物流行业指标 | 15 个**完全不在覆盖矩阵** | `build_damai_metric_coverage.py:99,112` 只取 `metrics_general` |

### 2.3 缺陷清单

| # | 严重度 | 问题 | 证据 |
|---|---|---|---|
| D1 | **阻断** | 件量口径差 **3.6 倍**：生成 648.3 百万单 vs 披露 2,311 百万单（FY2023）。根因是「收入 ÷ 120 万元/单 × 2 件/单」倒推 | `manifest.json:93` |
| D2 | 严重 | `operations.py:131,177` 硬编码「演示期间 FY2025/FY2026」，实际 canonical 已迁至 FY2022/FY2023 → unavailable 判定挂在错误期间 | `operations.py:131` vs `manifest.json:105-111` |
| D3 | 严重 | 两个 demo_detail 条目仍标 `status: pending_timeline_migration`，实际迁移已完成 | `source_facts_v1.yaml:7330,7335` |
| D4 | 一般 | 覆盖矩阵 `total: 50` 仅含 `metrics_general`，15 个物流指标无覆盖评估 → 易被误读为「全指标 64%」 | `build_damai_metric_coverage.py:99` |
| D5 | 一般 | 6 条分部事实无页锚（`page_verification: pending`）；FY2021 三表有 102 条事实但无 statements 文件 | `source_facts_v1.yaml` |
| D6 | 提示 | 遗留 v1 包仍带 65%/10% 假设文本（运行时未读，但易误用） | `data/enterprise/damai-logistics/v1/business/statements/damai_fy2025.yaml:11` |
| D7 | 提示 | `scripts/build_damai_demo.py:10` 文档串仍描述旧 FY2025/FY2026 口径 | 同上 |

### 2.4 未能验证

- 未运行 `verify_damai_demo.py` 与测试套件（只读审计约束）
- 未连库验证 UI 实际渲染的 unavailable 展示
- 未逐页打开 PDF 复核 6 条无页锚分部值（仅校验原件 SHA）

---

## 3. 维度二：CFO 驾驶舱功能完整性

### 3.1 模块实现矩阵

| # | 模块 | 路由 | 图表数 | 状态 |
|---|---|---|---|---|
| 1 | 集团总览 | `/cockpit` | 1（手写 SVG） | ⚠️ **路由名与设计不符**（设计为 `/cockpit/overview`） |
| 2 | 利润增长 | — | 0 | ❌ **未实现**（无路由、无端点） |
| 3 | 盈利能力 | — | 0 | ❌ **未实现**（批次 A 应含，缺失） |
| 4 | 费用分析 | ✅ | 1 | 🟡 降级呈现（HTML 表格） |
| 5 | 资产负债 | ✅ | 3 | 🟡 降级呈现 |
| 6 | 营运资金 | ✅ | 2 | 🟡 降级呈现（账龄 unavailable） |
| 7 | 现金流 | ✅ | 1 | 🟡 降级呈现 |
| 8 | 财务风险 | ✅ | **0** | 🔴 **有骨架无图**（`modules.py:429` 返回 `"charts": {}`） |
| 9 | 集团合并 | ✅ | 1 | 🔴 降级态（抵销桥 unavailable） |
| 10 | 数据中心 | 复用 `/data` | — | ⚠️ 导航无入口 |

**API 端点**：9 个（`/cockpit/overview` + 6 modules + action-items 3 个），聚合单次返回无 N+1 ✅，数据源为冻结 `MetricSnapshot` ✅，运行时测试 7 passed ✅。

### 3.2 功能清单判定

| 功能 | 状态 | 证据 |
|---|---|---|
| 聚合 API（禁 N+1） | ✅ | openapi.json 9 端点 |
| 数据源为冻结事实 | ✅ | `modules.py:79-82` 按 batch+version 取快照 |
| 指标三基准 + 口径注 | ✅ | `kpi-card.tsx` |
| 经营结论条（可溯源 Finding） | ✅ | `service.py:203` |
| 行动项 create / acknowledge | ✅ | `cockpit.py:194/234/307` |
| 安全规格（cfo 角色 + Action + route 登记） | ✅ | 规格 L258/L678；route-inventory 10 条 |
| **行动项 close** | ❌ | 规格 §10.2 要求，未进 Action 枚举，无端点 |
| **穿透抽屉历史趋势 + 版本历史** | ⚠️ | `drill-drawer.tsx:60-83` 注释明确延后 |
| **三会闭环（红灯/经分会/导出）** | ❌ | 生产代码零命中 |
| **ECharts 图表渲染** | ❌ | **10 个构建器 + ChartBox + useEChart 全是死代码** |

### 3.3 缺陷清单

| # | 严重度 | 问题 | 证据 |
|---|---|---|---|
| **F1** | **P0** | **图表全链路断裂**：原型 50 个图表，只有 8 个数据块到达浏览器，且 **0 个以 ECharts 渲染**——模块页把「期间 × 系列」渲染成 HTML 表格。`builders.ts` 10 个构建器只被单测引用 | `module-page.tsx:126-146`；`grep buildCombo` 在 `apps/web` 生产代码零命中 |
| **F2** | **P0** | **三会闭环完全缺失**：原型核心的「预警 → 管理层关注 → 应对措施」跨页闭环，无任何生产代码 | `grep 红灯\|经分会\|window.print` 零命中 |
| F3 | P1 | **「演进替换」未落地**：`/`（旧 DashboardApp）与 `/cockpit` **新旧两套并存**，违反设计 §9-Q2 裁决「不产生新旧两套驾驶舱」 | `app/page.tsx:2` |
| F4 | P1 | 财务风险模块零图表，页面无实质信息 | `modules.py:429` |
| F5 | P1 | 穿透链路缺环（历史/版本），削弱可追溯铁律 | `drill-drawer.tsx:60-83` |
| F6 | P2 | 利润增长 / 盈利能力两个模块缺失（openapi.json 零命中） | 路由 + 契约 |
| F7 | P2 | 数据中心无导航入口 | `workflow-nav.tsx` |

### 3.4 一处需澄清（非缺陷）

`cfo` 角色持有 `cockpit.action_item.create` 与 `acknowledge` 写权限，与「CFO 驾驶舱只读」的表述冲突。但这是安全规格 L687 的**显式决策**（acknowledge 归为独立写 Action 以保证可审计），**符合设计意图**——CFO 确认动作必须留审计痕迹。

### 3.5 未能验证

- 前端**未运行时验证**：未启动 Next.js，图表实际像素、筛选联动、E2E 均未实测
- 原型图表容器实测为 50（设计文档记 51，差 1 未定位）
- `action-panel.test.tsx` 未执行

---

## 4. 修复优先级建议

| 优先级 | 事项 | 理由 |
|---|---|---|
| **P0-1** | 把 10 个 ECharts 构建器接进 6 个模块页 | 图表是驾驶舱核心价值；当前 0 渲染 = 产品不可用 |
| **P0-2** | 修复件量单价（120 万 → 披露隐含 33.66 万/单）并加聚合断言 | 3.6 倍误差会让 CFO 质疑全部数据 |
| **P1-1** | 实现三会闭环三件套 | 竞品对标项，也是原型核心交互 |
| **P1-2** | 补盈利 / 利润增长模块（端点 + 页面） | 设计 §8 批次 A/B 承诺项 |
| **P1-3** | 落地「演进替换」：`/` 重定向或合并 | 避免两套驾驶舱并存 |
| **P2** | 补 `action_item.close`；穿透补历史/版本；修 D2/D3/D4 | 闭环完整性与数据诚实度 |

---

## 5. 审计方法与局限

- 两路独立只读调查（大麦数据 / 驾驶舱功能）+ 主审交叉核对关键事实（路由数、图表调用点、Action 枚举、route 登记）
- 竞品基准来自公开市场调研（帆软财经数智化五层架构、行业经分会三会 SOP、数据熊原型自身形态）
- **局限**：前端未运行时验证；未连库；未逐页复核 PDF；未运行测试套件（除驾驶舱 7 passed）
