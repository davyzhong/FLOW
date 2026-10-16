---
doc_id: FLOW-WI-COCKPIT-CFO-001
title: CFO 财务总监驾驶舱产品化
doc_type: work-item
status: completed
version: 2.0
created_at: 2026-09-30
updated_at: 2026-10-13
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

## 目标## 目标

把 `docs/05_design/prototypes/2026-09-29-cfo-cockpit-prototype-v2.html`（v2.0，51 图表、三模式、全卡穿透）**产品化**为 `apps/web/cockpit/*` 真实路由页面：Next.js 组件化实现、接真实 API 数据、受既有前端门禁（AppShell / workflow-nav / navigation.spec / 五态 / CI 17 job）约束。

不做通用自助 BI（拖拽建模、多维探索）——D001 铁律；不做合并报表编制（只消费合并结果）；不做通用任务管理。

## 用户裁决（2026-09-30）

1. **交付形式**：真实产品页面，不是静态原型；
2. **队列位置**：**抢在 U04 盲评复评之前当队首**（盲评复评暂停，非取消）；
3. **数据源**：第一版用**大麦物流演示数据**跑通真实链路，不等待 U04 / C 级。

## 为什么不阻塞 C 级

驾驶舱与 C 级出口无数据依赖：驾驶舱用已验证的大麦数据（verify 19/19、隔离 E2E 157/157、CI 17/17），不消耗 C 级证据预算。盲评复评暂停是可逆的。

**驾驶舱用演示数据不构成公开财报能力证明，不解除 C 级门禁。**

## 用户补充验收基线（2026-10-12）

用户重申：大麦物流的经营 Mock 必须以阿里巴巴/菜鸟原始公开披露为依据，贴近菜鸟真实业务，不能把无来源假设冒充企业事实；基于这套数据验证全系统功能；CFO/BP 驾驶舱所有指标、图表和交互一次性完整交付；界面一致、真实有据、可链接、可跳转；成熟开源组件优先复用，无法满足具体需求时才自建。此基线覆盖原型中的 51 个图表与既有十模块，以及现有系统功能验收，不扩大成通用自助 BI。

### 数据分型和披露边界

1. **披露事实**：每个事实记录官方来源机构、报告标题/版本、URL、财年/期间、页码或表格、原始值、单位/币种、文件 SHA-256 与提取定位；必须能回到来源原件复核。
2. **可复算派生值**：只能由已登记披露事实按明确公式、单位换算或可验证的汇总/分摊关系计算；记录输入事实 ID、公式版本、舍入规则和输出。不能反推出的细分分布不得描述为历史实际。
3. **Mock 交互明细**：如需订单、月份、组织切片等公开材料未披露的粒度来验证系统，必须标识为“演示生成明细”，其金额/数量须与来源聚合事实对账，保存确定性生成规则及来源锚点，并与事实层隔离，页面不得称为真实披露或实际经营明细。
4. **测试建制数据**：用户、岗位、角色、权限、账号和个人身份信息是此前明确授权生成的隔离测试夹具；它们不属于阿里/菜鸟事实，不进入财务分析事实源，也必须有醒目测试标识。
5. 无公开依据且无法从来源值复算的财务/经营指标应显示 unavailable 和原因；不沿用财务费用 65% 拆利息、固定资产 10% 折旧等无来源假设作为事实。若仅作为 Mock 场景变量验证功能，必须隔离并清楚标注，不能混入事实分析结果。

### 完整功能验收

- 以原型逐图清单为基线完成全部 51 个图表的“图表—指标—数据源—页面”映射；十模块的全部指标/图表必须有来源事实、可复算派生值或明确 unavailable 状态，不留静态占位。
- 所有 KPI、图表元素、指标定义与公式、财报行、Finding、导入批次和数据来源按既有权限可点击下钻/上算/追溯；路由、筛选、期间、组织范围、返回路径、深链和空/错误/无权限/加载态通过 E2E。
- 使用整套发行包执行系统全功能验收；校验关键汇总与源报告、相邻层级及财务恒等式对账，确认 fixture、生成批次、隔离环境和代码 SHA 可追溯，不改写来源原件。
- 图表优先使用已引入并封装的 ECharts 6.1.0 构建器；表格、筛选、页面状态、权限与路由优先复用现有成熟组件。每项自建能力须记录已有方案为何不适用。
- 数据资产完成来源血缘、确定性重建、manifest 哈希、导入/重置与租户边界验收后，才作为驾驶舱最终验收数据包。

公开资料的颗粒度有边界：阿里 FY2024 年报披露菜鸟业务/分部财务信息，菜鸟 FY2024 跨境及国际包裹日均量公开披露为超过 500 万；这些聚合数据不能证明未披露的逐月、逐客户或逐笔经营值。来源入口优先使用[阿里巴巴官方财务报告](https://www.alibabagroup.com/en-US/ir-financial-reports-financial-results)、[阿里巴巴 FY2024 年报菜鸟业务介绍](https://static.alibabagroup.com/reports/fy2024/ar/ebook/EN/34/index.html)和[菜鸟官方介绍](https://www.alibabagroup.com/en-US/document-1747836787297878016)。

## 批次与状态

| 批次 | 范围 | 状态 | 门禁摘要 |
|---|---|---|---|
| **A** | 框架 + 集团总览页（真实数据链路） | **completed** | ✅ 同 SHA CI `36601612612` 17/17 success（commit `b7dc4983`） |
| B | 安全规格 V1.1.1 + ActionItem + 行动项闭环 | blocked（待 §6 Q2 裁决） | approved-spec 门禁 + 安全规格 §11 九类断言 + route-inventory 双向零差集 |
| C | 其余 8 模块（利润/盈利/资产负债/营运/费用/现金/风险/合并/数据中心） | **next** | C-1 图表组件库已实现 ECharts 6.1.0 与 10 类构建器；F1/F2 已由同 SHA CI 关闭。先完成 2026-10-12 来源事实与 Mock 血缘门禁，再依次推进 F3–F4、C-2～C-5 |
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

图表技术选型已记录于实施方案 §6 Q1：ECharts 6.1.0 + 10 类可复用构建器；复杂语义关系图保留 HTML/CSS。F1 指标目录哈希兼容由 `d6afe463` 修复；其准确 SHA CI 余下三个失败已定位为固定演示数据日期与真实时钟错位。API 现提供可覆盖时钟依赖，数据库生命周期测试固定时间，dashboard/investigation E2E 使用只服务于验收的冻结时钟启动器。静态检查已通过；待数据库服务可用时的本地集成验证及修复提交后的准确 SHA CI。CI 全绿前不启动 F2。

### 2026-10-13 深夜接续状态（时间线迁移已交付）

演示时间线迁移完成（`087a72f2`，分支 `flow/timeline-migration-20261013`）：FY2022/FY2023 真实财年、明细↔披露零差异、IFRS 披露三表过勾稽门禁、覆盖矩阵 32/50×2、ORG-LEDGER v2。**当前唯一子步骤：同 SHA CI 全绿并合并 main 后，进入 F3（指标目录收尾）→ 批次 C-2（其余 8 模块页面）。**

### 2026-10-13 接续状态（来源登记 + 运营披露层已交付）

来源登记 `config/damai/source_facts_v1.yaml` 已交付（325 条 disclosed_fact、四分型、页锚机械核验、13 项 pytest 门禁，commit `842c8ea8`）；`fixtures/damai/operations` 已重建为披露事实层——分部序列改用菜鸟披露值（FY2019–FY2025，FY2026 如实缺省）、件量修复数量级与字段语义（FY2023 国际 1,519 百万件）、废弃「收入÷客单价」推导口径（commit `e5d8d2c6`）；大麦相关 108 项测试、发行版确定性对账、scripts 155 项、m1 全绿。**当前唯一子步骤：演示时间线迁移至真实财年**（比较期 FY2022、分析期 FY2023、FY2021 期初锚），迁移五步与验收见 [CURRENT_ROADMAP](../CURRENT_ROADMAP.md) 队首行。迁移完成前驾驶舱模块页面（C-2～C-5）不启动。

### 2026-10-12 接续状态（历史）

F1 准确 SHA CI run `38147756845`（提交 `11129263110d296f33c48b6cb94237a6fcedfd13`）17/17 success；F2 字典对齐及公式勾稽修正准确 SHA CI run `38188010174`（提交 `0d4b554f33bd1c9cdab3242b25d26eb2209a632c`）17/17 success。来源基线计划提交 `df0f2e6782e60d65edc955918a892c34868a9c51` 的准确 SHA CI run `38188972800` 17/17 success。首轮数据来源和语义审计见[验证记录](../../60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md)：已存在的菜鸟 P5 三表抽取、运营事实和分部序列可复用；当前大麦模拟生成器未使用它们，且有件量数量级/语义问题。当前唯一子步骤为建立机器可读来源登记和适配设计，逐项补足原件页表/期间/原值单位/哈希，再将这些事实用于大麦演示包，明确隔离生成明细及不可用指标。未通过来源门禁前不启动 F3 或后续模块。

### 批次 B 交付记录（2026-10-14）

- **B1 安全规格 V1.1.1**（`docs/40_specs/security/internal-workbench-rbac-audit-v1.md`）：新增 `cfo` 角色、`cockpit.action_item.*` 3 Action、§4.3 allow set、§14 修订记录（§10.6 四问裁决：新增 cfo / acknowledge 独立写 Action（allow 决策即 durable 凭证，不改业务行）/ 筛选沿用既有 Action / 跨企业校验保留、公开期不触发）；连带回写枚举文本漏登的 `metric_snapshot.read`/`analysis_run.read` 与四角色 allow 行（独立审查 P1）。
- **B2 独立审查**：隔离会话完成（结论 NEEDS_FIXES → 全部 P0/P1 修复：测试种子链、规格枚举回写、措辞；P2 中 snapshot FK、注释漂移一并修复）。
- **B3**：`cockpit_action_item` 表 + 迁移 0032（含 role 枚举 CHECK 增加 cfo 与 downgrade 清理；up/down/up 验证）。
- **B4/B5**：`GET/POST /api/v1/cockpit/action-items` + `POST …/{id}/acknowledge`（只写 durable 审计）；route-inventory 双向零差集恢复（**修复批次 A 遗留：cockpit overview 未登记即 403**）；web `ActionItemPanel` + flowApi 三方法 + vitest。
- **门禁**：§11 九类断言全绿（5 组命令）；`require_approved_specs` 通过；web 单测 173、typecheck、mypy 208、ruff 全绿。

### 批次 C-2 交付记录（2026-10-14）

- **后端**：`cockpit/modules.py`（披露事实装配：两期发布报表的归一化 canonical 行，千元→百万元）+ `GET /api/v1/cockpit/modules/balance-sheet|working-capital`（单聚合端点；TSV 登记，双向零差集保持 81=81）；
- **前端**：`/cockpit/balance-sheet`、`/cockpit/working-capital` 两页（AppShell + 导航登记 + navigation.spec 路由清单）+ 共享 `module-page` 渲染器（KPI 网格 + 图表数据表 + 降级块五态）+ ActionItemPanel 集成总览页；
- **口径**：KPI 值全部来自披露事实（总资产 FY2023 = 71,850.931 百万）；CCC 恒等式模块内自洽；债务期限拆分/应收账龄/多主体排名如实缺省并注原因；
- **门禁**：模块 API 测试 3 项、web vitest 174、typecheck、lint、生产构建、m1 全绿。

### 批次 D 交付记录（2026-10-15）

- **结论条自动生成**：已在批次 A 实现（`CockpitProjectionService._conclusion()` 从冻结 Finding 生成，不接受裸文本；`CockpitConclusionBar` 渲染溯源链接）。本轮验证通过，无需改动。
- **Findings 跨页联动**：已在批次 A/B 实现（`CockpitDrillDrawer` 穿透至调查页；KPI 卡链接指标库；行动项面板链接审计）。本轮验证通过。
- **问数入口嵌入**：新增驾驶舱总览页「问数 → 四问工作台」入口链接（确定性检索引用 QA；LLM 通道另行裁决）。CSS + Link + 三检通过。

**结论**：批次 D 的实质交付已由批次 A/B 的架构覆盖（结论条和跨页联动为驾驶舱框架固有能力），本轮补齐了问数入口嵌入。设计文档 §8 "另行裁决" 项（LLM 通道）维持后置不阻塞。

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

- U04 盲评复评：`active（队首）` → `active（暂停，驾驶舱让位）`，恢复条件 = CFO 驾驶舱产品化工作包完成；
- ZTO 2026Q1：维持封存（用户 2026-09-29 裁决）；
- C 级出口：仍 No-Go，状态不变。

## 关联文档

- 实施方案：[2026-09-30-cfo-cockpit-implementation-plan.md](../../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md)
- 设计文档：[2026-09-29-cfo-cockpit-design.md](../../05_design/2026-09-29-cfo-cockpit-design.md)
- 主线：[CURRENT_ROADMAP.md](../CURRENT_ROADMAP.md)
- 安全规格：[internal-workbench-rbac-audit-v1.md](../../40_specs/security/internal-workbench-rbac-audit-v1.md)
