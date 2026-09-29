---
doc_id: FLOW-WI-COCKPIT-CFO-001
title: CFO 财务总监驾驶舱产品化
doc_type: work-item
status: active
version: 1.1
created_at: 2026-09-30
updated_at: 2026-09-30
owner: FLOW
depends_on: [FLOW-WI-DAMAI-FULL-YEAR-001, FLOW-WI-ORG-LEDGER-001, FLOW-WI-S01-POST-U8-001]
acceptance_refs: [FLOW-PLAN-COCKPIT-IMPL-20260930]
applies_to: web-frontend
decision_refs: [D001, D052, D053]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
source_refs:
  - docs/05_design/2026-09-29-cfo-cockpit-design.md
  - docs/05_design/prototypes/2026-09-29-cfo-cockpit-prototype-v2.html
related_plan: docs/superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md
confidentiality: project-internal
---

# CFO 财务总监驾驶舱产品化

## 目标

把 `docs/05_design/prototypes/2026-09-29-cfo-cockpit-prototype-v2.html`（v2.0，51 图表、三模式、全卡穿透）**产品化**为 `apps/web/cockpit/*` 真实路由页面：Next.js 组件化实现、接真实 API 数据、受既有前端门禁（AppShell / workflow-nav / navigation.spec / 五态 / CI 17 job）约束。

不做通用自助 BI（拖拽建模、多维探索）——D001 铁律；不做合并报表编制（只消费合并结果）；不做通用任务管理。

## 用户裁决（2026-09-30）

1. **交付形式**：真实产品页面，不是静态原型；
2. **队列位置**：**抢在 U04 盲评复评之前当队首**（盲评复评暂停，非取消）；
3. **数据源**：第一版用**大麦物流演示数据**跑通真实链路，不等待 U04 / C 级。

## 为什么不阻塞 C 级

驾驶舱与 C 级出口无数据依赖：驾驶舱用已验证的大麦数据（verify 19/19、隔离 E2E 157/157、CI 17/17），不消耗 C 级证据预算。盲评复评暂停是可逆的。

**驾驶舱用演示数据不构成公开财报能力证明，不解除 C 级门禁。**

## 批次与状态

| 批次 | 范围 | 状态 | 门禁摘要 |
|---|---|---|---|
| **A** | 框架 + 集团总览页（真实数据链路） | **completed** | ✅ 同 SHA CI `36601612612` 17/17 success（commit `b7dc4983`） |
| B | 安全规格 V1.1.1 + ActionItem + 行动项闭环 | blocked（待 §6 Q2 裁决） | approved-spec 门禁 + 安全规格 §11 九类断言 + route-inventory 双向零差集 |
| C | 其余 8 模块（利润/盈利/资产负债/营运/费用/现金/风险/合并/数据中心） | **next** | 每批同 A 门禁；开工前须裁决实施计划 §6 Q1 图表选型 |
| D | 经分会计期增强（结论条自动生成、Findings 跨页联动、问数入口） | pending | 设计文档 §8 批次 D |

### 批次 A 交付清单（2026-09-30 完成，commit `ae56e96f` + `b7dc4983`）

| 项 | 位置 | 状态 |
|---|---|---|
| 聚合 endpoint | `services/api/src/flow_api/api/routes/cockpit.py` · `GET /api/v1/cockpit/overview` | ✅ 复用已批准的 `Action.DASHBOARD_OVERVIEW_READ`，未引入新 Action |
| 投影服务 | `services/api/src/flow_api/cockpit/service.py` | ✅ 从 `/dashboard/overview` 同一批冻结事实投影，零重复查询、零重算 |
| 前端组件 | `apps/web/components/cockpit/`（kpi-card / drill-drawer / trend-panel / filter-bar / conclusion-bar） | ✅ 三基准 + 口径注 + 穿透 + 五态 |
| 页面路由 | `apps/web/app/cockpit/page.tsx`（包 AppShell） | ✅ `workflow-nav` + `navigation.spec.ts` 已登记 |
| 契约 | `packages/contracts/openapi.json` + `schema.d.ts` | ✅ `/api/v1/cockpit/overview` 已生成 |
| 测试 | API 24 + domain 11；Web 11 驾驶舱用例（vitest 154/154） | ✅ |
| 门禁 | mypy 207 · typecheck · lint 0 errors · build · contracts-check · docs m1 | ✅ |
| **同 SHA CI** | run `36601612612`（commit `b7dc4983`） | ✅ **17/17 success** |

**批次 A 期间修复的两个真实回归**（本地全绿但 CI 抓出）：

1. **CSS 全局污染**（7 job 连锁失败）：`cockpit.css` 原在 `app/layout.tsx` 全局引入，裸类名（`.kpi`/`.trend`/`.concl`/`.cmp`/`.drill`）参与全局层叠，破坏既有 dashboard 视觉基线与 axe 无障碍判定。修复：改为组件级引入（`cockpit-overview-app.tsx` 内 import），只作用于 `/cockpit`。
2. **ruff 导入序**（`static-python` 失败）：`api/router.py` 中 `cockpit_router` 位置违反 isort 字母序。已归位。

批次 A 开工前必须先裁决实施计划 §6 的 **Q1（图表技术选型）**。

## 范围边界（不做什么）

- ❌ 通用自助 BI（拖拽建模、多维探索器、自助取数）
- ❌ 合并报表编制（只消费已合并结果）
- ❌ 通用任务/项目管理（排期、协作、通知、甘特）
- ❌ 因果推断（只做数学分解 + 证据分层，驱动不可证实时标 `unknown`）
- ❌ 解除 C 级门禁

## 关键约束

1. **只消费已冻结事实**：驾驶舱读 `MetricSnapshot` / `ReportSnapshot`，不重算；
2. **每个上屏数字带 `snapshot_id`**，否则前端拒绝渲染（可追溯铁律）；
3. **结论条文本来自 `Finding` / 已终审 `ReportSnapshot` 章节**，不接受裸文本入参；
4. **API 聚合 endpoint**：每模块一个（`GET /api/v1/cockpit/<module>`），禁止逐图调现有 endpoint（N+1）；
5. **演示数据源全局标注**，避免被误认为真实企业数据；
6. 前端规范硬要求：交互页包 `<AppShell>`、在 `workflow-nav.tsx` 登记、`navigation.spec.ts` 遍历断言。

## 当前证据

- 原型 v2.0：1.16MB 单文件、ECharts 内联离线可开、51 图表、Playwright 逐页渲染 51/51 成功、0 JS 错误；
- 设计文档 v0.5：§1–§10 完整，§4.2 模块清单已绑定 FLOW 数据源，§10 安全前置清单（3 个新 Action + ActionItem 表 + route 登记 + 4 个待裁决问题）；
- 大麦演示数据已入库（verify 19/19、CI run `36371507389` 17/17）；
- ORG-LEDGER 企业建制完成（`2c7d6eb4`、CI run `36270782272` 17/17）。

## 路线影响

- U04 盲评复评：`active（队首）` → `active（暂停，驾驶舱让位）`，恢复条件 = 批次 A 完成；
- ZTO 2026Q1：维持封存（用户 2026-09-29 裁决）；
- C 级出口：仍 No-Go，状态不变。

## 关联文档

- 实施方案：[2026-09-30-cfo-cockpit-implementation-plan.md](../../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md)
- 设计文档：[2026-09-29-cfo-cockpit-design.md](../../05_design/2026-09-29-cfo-cockpit-design.md)
- 主线：[CURRENT_ROADMAP.md](../CURRENT_ROADMAP.md)
- 安全规格：[internal-workbench-rbac-audit-v1.md](../../40_specs/security/internal-workbench-rbac-audit-v1.md)
