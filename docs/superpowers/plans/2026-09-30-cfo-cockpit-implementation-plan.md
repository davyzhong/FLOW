---
doc_id: FLOW-PLAN-COCKPIT-IMPL-20260930
title: CFO 财务总监驾驶舱产品化实施方案（抢队首）
doc_type: plan
status: active
version: 1.0
created_at: 2026-09-30
updated_at: 2026-09-30
owner: FLOW
applies_to: web-frontend
depends_on: [FLOW-DESIGN-CFO-COCKPIT-20260929, FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1]
acceptance_refs: [cockpit-batch-gates]
decision_refs: [D001, D052, D053]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
source_refs:
  - docs/05_design/2026-09-29-cfo-cockpit-design.md
  - docs/05_design/prototypes/2026-09-29-cfo-cockpit-prototype-v2.html
related_work_item: docs/50_plans/work_items/COCKPIT--cfo-dashboard-implementation.md
confidentiality: project-internal
---

# CFO 财务总监驾驶舱产品化实施方案

> **用户裁决（2026-09-30）**：
> 1. **交付形式**：把 v2.0 HTML 原型做成**真实产品页面**——Next.js 组件化实现、接真实 API 数据、进 `apps/web/cockpit/*` 路由（不做单文件静态原型）；
> 2. **插队位置**：驾驶舱**抢在 U04 盲评复评之前当队首**（盲评复评暂停，非取消）；
> 3. **数据源**：第一版**先用大麦物流演示数据跑通真实链路**（不等待 U04 / C 级通过）。
>
> 本方案是执行依据，不是讨论稿。任何批次开工前须先核对本文件的验收门禁。

## 0. 为什么可以抢在 U04 之前

驾驶舱与 C 级出口**没有数据依赖关系**：

| | 依赖 | 现状 |
|---|---|---|
| 驾驶舱 | 大麦演示数据（已入库）+ ORG-LEDGER 企业建制 + MetricSnapshot/Findings/StatementReport | ✅ 全部具备（CI 17/17） |
| C 级出口 | U04 完整独立 oracle（14 份）+ 成品盲评 | ❌ No-Go，小米/阿里泛化失败 |

驾驶舱用**已验证的大麦数据**，不消耗 C 级证据预算，也不占用 U04 队首的人力。
盲评复评的暂停是可逆的（驾驶舱批次 A/B 完成后立即恢复），且驾驶舱的成品本身就是
C 级盲评的**被评审对象之一**（管理层版报告），不冲突。

**风险与对冲**：

| 风险 | 对冲 |
|---|---|
| 抢队首导致 C 级出口进一步延后 | 驾驶舱批次 A/B 有明确退出条件（见 §4），完成后立即回队 U04 |
| 驾驶舱用演示数据被误当作产品能力 | 页面全局标注「演示数据源」，不解除 C 级门禁（沿用大麦既有口径） |
| 原型 51 图表一次性实现导致质量失控 | 分批交付，每批独立验收门禁（见 §4） |

## 1. 现状基线（2026-09-30 核实）

### 1.1 已有资产

| 资产 | 位置 | 状态 |
|---|---|---|
| 高保真原型 v2.0 | `docs/05_design/prototypes/2026-09-29-cfo-cockpit-prototype-v2.html` | 1.16MB 单文件、ECharts 内联离线可开、**51 图表**、三模式（红灯聚焦 / 经分会 / 导出管理层版）、全卡穿透抽屉 |
| 设计文档 v0.5 | `docs/05_design/2026-09-29-cfo-cockpit-design.md` | §1–§10 完整；§4.2 模块清单已绑定 FLOW 数据源；§10 安全前置清单（3 个新 Action + ActionItem 表 + route 登记 + 4 个待裁决问题） |
| 逐页截图 | `docs/05_design/prototypes/v2-*.jpg` | 10 张全页 |
| 大麦演示数据 | `flow` 常驻库（已入库） | verify 19/19、隔离 E2E 157/157、CI run `36371507389` 17/17 |
| ORG-LEDGER 企业建制 | `2c7d6eb4` | 母公司/子公司/事业部/账套，CI run `36270782272` 17/17 |

### 1.2 缺口

| 缺口 | 影响批次 | 说明 |
|---|---|---|
| `apps/web/cockpit/*` 路由为零 | A | 需新建 10 个路由页 |
| API 侧无 `/api/v1/cockpit/*` endpoint | A | 需新建聚合 endpoint（不能逐图调现有 endpoint，N+1 不可接受） |
| 图表组件库为零 | A | 51 个图表需抽象为 8–10 类可复用组件 |
| `workflow-nav.tsx` 未登记驾驶舱入口 | A | 前端规范硬要求 |
| 安全规格需修订（3 个新 Action + `cfo` 角色） | B | 见设计文档 §10；**实现 Step 0 门禁** |
| ECharts 未进 apps/web 依赖 | A | 需决策：引 ECharts / Recharts / 沿用手写 SVG（Recharts 曾暂缓，见设计文档 §6） |

## 2. 目标形态

```text
apps/web/app/cockpit/
├── layout.tsx              # 包 AppShell（规范硬要求）
├── page.tsx                # 集团总览（演进替换现有 dashboard 快照页，见设计文档 §9-Q2）
├── profit-growth/page.tsx
├── profitability/page.tsx
├── expenses/page.tsx
├── balance-sheet/page.tsx
├── working-capital/page.tsx
├── cash-flow/page.tsx
├── risk/page.tsx
├── consolidation/page.tsx
└── data-center/page.tsx

apps/web/components/cockpit/
├── cockpit-shell.tsx           # 全局筛选条（主体/期间/口径/币种/累计）+ URL state
├── kpi-card.tsx                # 三基准（同比+环比+行业分位）+ 口径注 + 状态色
├── charts/                     # 图表组件库
│   ├── combo-trend.tsx         # 柱+线双轴
│   ├── waterfall.tsx           # 差异桥（含守恒核对块）
│   ├── quadrant-matrix.tsx     # 四象限散点
│   ├── gauge-control.tsx       # 仪表盘 + 管控线
│   ├── stacked-trend.tsx       # 堆叠柱 + 率线
│   ├── donut.tsx               # 环形/玫瑰
│   ├── radar.tsx               # 雷达
│   ├── treemap.tsx             # 结构树
│   ├── bar-rank.tsx            # 排名条形
│   ├── heatmap.tsx             # 热力
│   ├── dupont-tree.tsx         # 杜邦树（HTML/CSS，不用图表库）
│   └── ccc-formula.tsx         # CCC 公式图（纯 HTML）
├── conclusion-bar.tsx          # 经营结论条（可溯源 Finding）
├── drill-drawer.tsx            # 穿透抽屉（口径→来源→Finding→历史→版本）
└── action-panel.tsx            # 管理层关注/行动项（B 批次后可用）
```

### 2.1 图表技术选型（需在批次 A 开工前定）

| 方案 | 优点 | 代价 | 建议 |
|---|---|---|---|
| **手写 SVG**（沿用 statements/trend-panel 惯例） | 零新依赖、完全可控、无 bundle 膨胀 | 51 图表工作量大 | 复杂图表（仪表盘/热力/杜邦）推荐 |
| **ECharts** | 原型已验证、图表类型全 | +1MB 依赖、设计文档 §6 记载「Recharts 暂缓，零依赖手写 SVG 惯例」 | 简单图表（柱线/环形/雷达）可用 |
| **Recharts** | React 原生、组合式 | 设计文档明确「暂缓」 | 暂不引入 |

**建议**：混合方案——简单图表用**手写 SVG**（复用现有 `trend-panel` 模式），复杂图表按需评估。
**这是待定项，需在批次 A 开工前由用户裁决**（见 §6 未决问题 Q1）。

## 3. API 侧设计

### 3.1 聚合 endpoint（不逐图调现有 endpoint）

51 个图表若逐个调现有 endpoint，会产生 N+1 请求。设计**每模块一个聚合 endpoint**：

```text
GET /api/v1/cockpit/overview?subject=&period=&scope=&currency=&mode=
GET /api/v1/cockpit/profit-growth?...
GET /api/v1/cockpit/profitability?...
...（共 10 个）
```

每个 endpoint 一次返回该模块所需的全部 KPI + 图表数据 + 结论条文本 + 关联 Finding ID。

### 3.2 首版数据源（大麦演示数据）

| 模块 | 数据来源 | 现有实体 |
|---|---|---|
| 总览 | 大麦 ORG-LEDGER 汇总 + MetricSnapshot | `MetricSnapshot` / `MetricValue` |
| 利润/费用 | 利润表事实 + 期间费用行项目 | `StatementReport` / `StatementLineItem` |
| 盈利 | 指标字典（毛利率/净利率/ROA/ROE/EBITDA）+ 平均口径 | 指标库 v1.1（64 指标） |
| 资产负债/营运/现金/风险 | 四表事实 + 计算衍生（DSO/DIO/DPO/CCC、偿债指标） | 同上 |
| 合并 | **降级为「主体对比」**（大麦有母子结构，可用内部交易抵销前的主体口径） | ORG-LEDGER |
| 数据中心 | 导入管线状态 + manifest + 校验结果 | 已有 |

### 3.3 门禁约束

- 驾驶舱**只消费已冻结事实**（`MetricSnapshot` / `ReportSnapshot`），不重算；
- 每个上屏数字必须带 `snapshot_id`，否则前端拒绝渲染（可追溯铁律）；
- 结论条文本来自 `Finding` / `ReportSnapshot` 已终审章节，**不接受裸文本入参**。

## 4. 分批实施与验收门禁

### 批次 A：框架 + 总览页（真实数据链路打通）

| # | 任务 | 产出 |
|---|---|---|
| A1 | 图表技术选型裁决 + 组件库骨架 | `components/cockpit/charts/*` 基础 4 类 |
| A2 | `cockpit-shell` 全局筛选条 + URL state | 筛选状态可分享可复现 |
| A3 | `kpi-card` 三基准 + 口径注 + 状态色 | 复用原型视觉规范 |
| A4 | `drill-drawer` 穿透抽屉 | 口径→来源→Finding→历史 |
| A5 | API：`GET /api/v1/cockpit/overview` | 聚合 endpoint |
| A6 | `app/cockpit/page.tsx` 总览页（5 图表） | 演进替换现有 dashboard 快照页 |
| A7 | `workflow-nav.tsx` 登记入口 + `e2e/navigation.spec.ts` 加路由 | 前端规范门禁 |
| A8 | 五态（loading/error/403/empty/loaded）+ 演示数据源标注 | 规范硬要求 |

**批次 A 验收门禁**：

- [ ] `pnpm --filter @flow/web typecheck` 通过
- [ ] `pnpm --filter @flow/web lint` 通过
- [ ] `pnpm --filter @flow/web test`（vitest）通过
- [ ] `e2e/navigation.spec.ts` 遍历断言驾驶舱路由导航可见
- [ ] `frontend-states.spec.ts` 状态矩阵覆盖驾驶舱页（loading/error/403/empty）
- [ ] 生产构建 `pnpm build` 通过
- [ ] 真实数据验证：总览 5 图表数值与 API 返回一致（抽样 3 个 KPI 与 `MetricSnapshot` 核对）
- [ ] 提交后**同 SHA CI run 17/17 success**

### 批次 B：安全前置 + 行动项闭环

| # | 任务 | 依赖 |
|---|---|---|
| B1 | 安全规格 V1.1.1 修订（新增 `cfo` 角色 + 3 个 `cockpit.action_item.*` Action） | 用户裁决设计文档 §10.6 的 4 个问题 |
| B2 | 规格独立审查 + 用户重新批准（门禁硬要求） | B1 |
| B3 | `ActionItem` 表 + 迁移 | B2 |
| B4 | `action-panel` + `POST /api/v1/cockpit/action-items` | B3 |
| B5 | CFO 确认动作（只写 AuditEvent） | B2、B3 |

**批次 B 验收门禁**：`require_approved_specs.py` 通过 + 安全规格 §11 九类断言绿 + route-inventory 双向零差集。

### 批次 C：其余 8 模块

按依赖与数据就绪度排序：

| 批次 | 模块 | 理由 |
|---|---|---|
| C1 | 利润增长、盈利能力 | 数据最全（利润表 + 指标字典 64 指标） |
| C2 | 资产负债、营运资金 | 四表事实直接可算 |
| C3 | 费用分析、现金流 | 需期间费用行项目 + 现金流勾稽 |
| C4 | 财务风险 | 需偿债指标 + 管控线配置 |
| C5 | 集团合并（降级态）、数据中心 | 合并抵销需前置；数据中心复用现有管线状态 |

每批同样走 A 的八项门禁。

### 批次 D：经分会计期增强

结论条自动生成 + Findings 跨页联动 + 问数入口嵌入（设计文档 §8 批次 D）。

## 5. 不做什么（边界）

- 不做通用自助 BI（拖拽建模、多维探索）——D001 铁律；
- 不做合并报表**编制**（只消费合并结果，不生成）；
- 不做行动项通用任务管理（排期/协作/通知）——只做财务结论闭环；
- 不做因果推断（只做数学分解 + 证据分层）；
- **不解除 C 级门禁**——驾驶舱用演示数据不构成公开财报能力证明。

## 6. 未决问题（需用户裁决，阻塞对应批次）

| # | 问题 | 阻塞 | 建议 |
|---|---|---|---|
| Q1 | 图表技术选型：手写 SVG / ECharts / Recharts | 批次 A1 | 混合方案（简单手写、复杂评估 ECharts） |
| Q2 | 安全规格 §10.6 的 4 个问题：是否新增 `cfo` 角色、`acknowledge` 语义归类、筛选是否需独立 Action、公开期跨企业风险 | 批次 B1 | 新增 `cfo` 角色；筛选沿用 `dashboard.overview.read` |
| Q3 | 批次 A/B 完成后是否立即恢复 U04 盲评复评 | 路线 | 建议 A 完成即恢复（驾驶舱与 C 级并行） |
| Q4 | 总览页「演进替换」现有 dashboard 快照页的切换策略（原地替换 / 双路由并存期） | 批次 A6 | 原地替换，同一路由重设计（设计文档 §9-Q2 已裁决） |

## 7. 路线影响登记

本方案抢队首，用户已确认承担 C 级延后影响。登记如下：

- **U04 盲评复评**：`active（队首）` → `active（暂停，驾驶舱让位）`，恢复条件 = 批次 A 完成；
- **ZTO 2026Q1**：维持封存（`wip/zto-integration-20260929`，用户 2026-09-29 裁决）；
- **驾驶舱**：新建 work_item，列为队首；
- **C 级出口**：仍 No-Go，状态不变，驾驶舱不改变其证据状态。

## 8. 关联文档

- 设计文档（含 §10 安全前置清单）：[2026-09-29-cfo-cockpit-design.md](../../05_design/2026-09-29-cfo-cockpit-design.md)
- 原型 v2.0：[2026-09-29-cfo-cockpit-prototype-v2.html](../../05_design/prototypes/2026-09-29-cfo-cockpit-prototype-v2.html)
- 工作包：[COCKPIT--cfo-dashboard-implementation.md](../../50_plans/work_items/COCKPIT--cfo-dashboard-implementation.md)
- 主线：[CURRENT_ROADMAP.md](../../50_plans/CURRENT_ROADMAP.md)
- 安全规格：[internal-workbench-rbac-audit-v1.md](../../40_specs/security/internal-workbench-rbac-audit-v1.md)
