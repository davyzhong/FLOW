---
doc_id: FLOW-WI-UX-POST-DAMAI-001
title: 大麦数据后的剩余体验收口
doc_type: work-item
status: active
version: 1.4
created_at: 2026-09-24
updated_at: 2026-09-26
owner: FLOW
depends_on: [FLOW-WI-DAMAI-FULL-YEAR-001]
acceptance_refs: [FLOW-PLAN-INTEGRATED-EXECUTION-20260924, frontend-route-state-viewport-matrix]
applies_to: web-frontend
---

# 大麦数据后的剩余体验收口

## 目标

让已装载的大麦合成数据在经分专员的核心页面中形成完整、可解释、可下钻的分析体验；明确区分“没有事实”“指标不适用”“快照未发布”“页面未展示”，不以空值补零，也不把静态 sidecar 说成已上线能力。

## 当前证据与判断（2026-09-26）

- 常驻开发库 G2 已完成，测试库隔离也已修复（`b60c51b`）；它们不再是本工作包的阻塞。
- 大麦 fixture 有 24 个月、1,920 条经营实际、10,752 条预算、4,800 条应收回款、672 条财务实际；40 个客户、8 个产品、6 个区域、4 个事业部。
- 当前只读 API 返回 2 份已发布财报（FY2025/FY2026），每份 40 个行项目，覆盖资产负债表、利润表、现金流量表、所有者权益变动表。
- 大麦 40 项指标覆盖矩阵为 FY2025 22/40、FY2026 25/40；需逐项分类，不可默认所有指标都适用于该企业。
- 驾驶舱 API 有 8 张 KPI 卡、12 个月趋势点（每点含4项趋势指标）、8 个产品、4 个客户群、2 条发现，但整体为 `degraded`：经营现金流趋势12/12不可用，毛利矩阵缺部分指标或比较值。
- 预测 sidecar 当前标记 `static-only` 且排除页面覆盖；本工作包不得把它计为已接入功能。

## 实施路线（本文件是规格；实施须按用户已批准的工作状态执行）

### Gate 1：逐页数据链路和缺口归因

盘点驾驶舱、报表分析、指标库、应收/经营分析、报告中心、数据工作台和公开经营分析页，建立“页面 → API → 已发布对象 → 源事实/指标”的覆盖表。每个空白/缺值只能归入：源事实不存在、口径/映射缺失、计算失败、快照未发布、过滤条件不匹配、前端未消费、按设计排除之一，并附可复现证据。

Files:
- Inspect: `apps/web/components/dashboard/`, `apps/web/components/statements/`, `apps/web/components/metric-library/`, `apps/web/components/operations/`, `apps/web/components/reports/`, `apps/web/components/data/`
- Inspect: `services/api/src/flow_api/dashboard/`, relevant statement/metric/operations API routes
- Evidence: add a versioned coverage table to this work item or its linked verification record; do not create another status ledger.

Acceptance: Gate 1 覆盖表必须逐项记录精确路由、请求参数/筛选、公司/组织、期间、数据集/批次、环境标识和 Git SHA；同一环境与 SHA 下冻结脱敏后的 GET 响应摘要或内容哈希。每个目标页有真实 GET 响应证据；缺口均有分类与 owner；已发布但未展示、或页面声称完整但 API 缺值的情况不得留作“无数据”笼统结论。

### Gate 1 诊断盘点（2026-09-26，只读；代码验收仍未关闭）

API 由本 worktree 的 `uvicorn --reload` 提供服务。最新整轮只读探测前后，运行时代码 overlay 指纹保持一致：Git 基线 `3ff95115` + 工作树 overlay SHA-256 `1ede264890932aefc595540885a3cc34feb891f7516a137637db8bab3723529d`。响应哈希与复现参数见[Gate 1 API 证据记录](../../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)。这是可复现的诊断快照，不是干净提交 SHA 的发布验收；源文件仍包含其他会话的未提交改动，不能据此宣称代码版本已验收。

| 页面 | 读取链路（观察到的 GET） | 初步观测 | 归因 / 待办 |
|---|---|---|---|
| `/` 经营总览 | `/api/v1/dashboard/overview?period_view=month\|ytd`（全公司、无维度筛选；截至2026-08） | 8 KPI卡；12个月趋势点、每点4指标；8产品、4客群、32格毛利矩阵。经营现金流趋势12/12不可用，码 `trend_metric_not_published`；经营现金流KPI主值1/8不可用、码 `metric_grain_not_published`；预算4/8及YTD预算4/8不可用、码 `comparison_not_published`；矩阵实际22/32为 `metric_grain_not_published`、比较24/32为 `comparison_not_published`；整体 `degraded`。顶层质量、对账、快照/分析发布与新鲜度状态均显示通过/已发布/新鲜。 | 主要是快照/指标粒度和比较值未发布，不是可以用补零处理的数值缺失；需追到快照构建、发布和聚合层。 |
| `/statements` 财报分析 | `/api/v1/statements` → `/api/v1/statements/{report_id}` | FY2025、FY2026各1份；每份40行：资产负债表15、利润表13、现金流量表8、权益变动表4。 | 年报期间已存在；月度财务报表是否属于范围须按产品合同裁决，不擅自扩成另一个口径。 |
| `/analysis` 四问工作台 | `/api/v1/statements` → `/api/v1/analysis/workbench/{report_id}` | FY2025 初始返回500；确定性提示 `leverage_rising` 带 `metric_code`，原响应模型却 `extra=forbid` 且未声明该字段。补齐响应契约后，本地热重载 API 返回200并带指标代码。FY2026原为200。 | 根因已确认并修复（`ManagementWatchItem.metric_code` 缺失）；回归测试已覆盖。待变更提交后在干净 SHA 复测；其余页面缺口仍需逐项归因。 |
| `/operations` 经营分析 | `/api/v1/operations/public-periods`、`/api/v1/operations/public/{stock_code}/{period}`、`/api/v1/operations/overview/{report_id}` | 7个期间（菜鸟5、大麦2）；概览端点返回6个主题。 | 逐主题核验内容、缺值与下钻。 |
| `/metric-library` 指标库 | `/api/v1/metric-library`、`/api/v1/metric-library/coverage?dataset=damai` | 65个定义、40项覆盖矩阵；FY2025可计算22项、FY2026可计算25项。未满足项的接口缺失字段为：利息费用 `is.interest_exp(cur)`（7项指标）、短债 `bs.short_debt(end)`（3项）、长债 `bs.long_debt(end)`（1项）、应付账款 `bs.ap(end)`（2项）、同比基期 `is.revenue/net_profit/operating_profit(prev_yoy)`（3项）、销售收现 `cf.cash_from_sales(cur)`（1项）、资本开支 `cf.capex(cur)`（1项）。 | 接口的 `missing` 只证明归一化事实缺失，不足以判断原件未披露、导入映射漏项或该指标对大麦不适用；Gate 2须逐项回看原始合成报表及公式合同后分类，不能将财务费用直接冒充利息费用。 |
| `/reports` 发布中心 | `/api/v1/publishing/snapshots`、`/api/v1/publishing/freeze-candidates`、`/api/v1/operations/snapshots` | 1个发布快照、12个冻结候选、2个经营快照。 | 核对候选/发布状态、期间与数据集。 |
| `/data` 数据工作台 | 当前界面为会话内上传/映射/校验；没有页面初始态批次 GET | 已 seed 的批次在此页不可通过历史列表浏览；仅有已知 batch ID 后查询版本的 API 路径，没有通用批次列表入口。 | “数据在库但无浏览入口”，纳入 Gate 4，不应误判为源数据不存在。 |
| `/investigations` 与详情 | `/api/v1/investigations`、`/api/v1/investigations/{finding_id}` | Finding 列表2条。 | 核对每条发现的事实、证据与财报关联。 |
| `/public`、`/internal` | 模块导航落地页 | 页面本身不展示业务数据。 | 不计作数据页；其链接目标页纳入本表；登录页排除。 |

**Gate 1 诊断盘点已完成；实现/发布验收仍未关闭**：只读 API 矩阵、请求口径和初始响应哈希已冻结。FY2025 工作台 500 根因已确认并在本地工作树修复：确定性 `leverage_rising` 提示携带 `metric_code`，严格响应模型漏字段导致校验失败；新增回归测试由红转绿，本地 API 重测返回200。其余缺口仍须逐项归类并指定后续 Gate；当前工作树含其他会话改动，待拥有者整理提交后，再以干净 SHA 重跑完整矩阵作为代码验收基线。不得覆盖、暂存或提交其他会话的变更。

#### 补充缺口码读数（2026-09-26，只读，未冻结响应哈希）

本轮继续从当前热重载服务 GET 读取到精确缺口码：驾驶舱12个月现金流趋势全部为 `trend_metric_not_published`；8张卡中现金流KPI主值为 `metric_grain_not_published`，4张预算及4张YTD预算比较为 `comparison_not_published`；毛利矩阵32格中22格实际值为 `metric_grain_not_published`，24格比较值为 `comparison_not_published`。该证据把责任收敛到 Gate 3 的指标快照粒度/趋势发布/比较快照生成，不可误归为“数据库无业务数据”。指标库覆盖接口列出的18个缺失规范事实字段，已分组记录在上表；是否属于源事实缺失、导入映射或不适用仍由 Gate 2裁定。此补充读数未绑定新的工作树内容哈希，须在稳定提交版本重新冻结。

### Gate 2：形成正确且够用的合成财务事实

先把 40 个指标按“适用且可计算 / 适用但源事实缺失 / 不适用 / 有意不展示”裁决。仅为适用且缺失的指标补齐源事实；所有金额继续由确定性生成器产出，遵守借贷与报表勾稽、单位/币种和 24 个月期间合同。不得手工编辑生成文件、以零代缺值或人为塞入不可能的业务科目。

Files:
- Modify as evidence requires: `scripts/build_damai_demo.py`, `scripts/build_damai_metric_coverage.py`
- Regenerate only through generator: `fixtures/damai/canonical/`, `fixtures/damai/statements/`, `fixtures/damai/manifest.json`
- Tests: existing `scripts/tests/` and API fixture/metric tests; add focused regression tests for every newly computable metric and accounting invariant.

Acceptance: 40项指标逐项有“适用且可计算 / 适用但缺源事实 / 不适用 / 有意不展示”结论；对适用指标在 FY2025/FY2026 有确定性结果或有可核验缺失原因。逐项将覆盖矩阵数值和缺失原因与 API 响应对账；核心报表恒等式和预算/实际勾稽通过；重复构建零漂移。

### Gate 3：修快照发布与分析聚合

追踪当前驾驶舱降级到具体月度快照和指标定义，修复快照生成/发布或聚合逻辑；验证 24 个月趋势、预算对比、同比/环比以及客户群、产品、组织、区域筛选。月度 API 只展示当前已发布且口径一致的快照；未满足条件的值保留显式缺失原因。

Files:
- Inspect/modify if root-caused: `services/api/src/flow_api/dashboard/fixture.py`, `services/api/src/flow_api/dashboard/repositories.py`, `services/api/src/flow_api/dashboard/service.py`, `scripts/seed_damai_demo.py` and the owning metric snapshot service
- Tests: `services/api/tests/dashboard/` and dashboard API integration tests

Acceptance: 形成逐条 `degraded` reason 对照表，明确每条当前原因须消除还是合理保留及其证据；对 Gate 2 的40项指标逐项把“覆盖矩阵→API 返回值/缺失→驾驶舱或报表展示”对账。所有声明应完整的面板无非预期 `degraded`；24个月时间序列可核对；过滤前后总额、预算差异和明细 drill-through 可复算。若降级是有意且合理，必须明确展示面板级原因，而非静默缺项。

### Gate 4：页面可见性、可理解性和下钻

让页面直接显示当前选择期间、数据批次/新鲜度、口径、可计算覆盖与明确缺口；建立从 KPI/趋势/矩阵到筛选明细或财报原行的真实链接。覆盖 390/1024/1440 视口、加载/空/错误/403/部分降级状态。和全站深链实施计划协同，不重复实现已完成的批次一。

Files:
- Modify only after Gate 1 proves the gap: relevant files under `apps/web/components/dashboard/`, `apps/web/components/statements/`, `apps/web/components/metric-library/`, and `apps/web/e2e/`
- Reuse: `apps/web/lib/deep-links.ts` and `2026-09-26-ui-deep-link-implementation-plan.md`

Acceptance: Gate 1 覆盖表中的每条目标路由都必须逐页通过，不得抽样漏页；对每项覆盖指标/缺失原因同时断言 API 返回与 UI 呈现（正向值和缺失/不适用状态）；页面显示值与 API/源事实一致；点击维度和指标可到达对应记录；状态与响应式 E2E 通过。

### Gate 5：全链回归并关闭

Run: `make damai-demo-build`
Run: `make test-dashboard && make test-damai-demo-e2e`
Run: `make lint && make typecheck && make test-web`
Run: `python3 scripts/check_docs.py --phase m1` and the repository link check

验收上述命令、覆盖报告与同 SHA CI 全绿后，更新本工作包、`CURRENT_ROADMAP.md` 和 `PROJECT_STATE.md`。演示 seed/verify 只能在 `test-damai-demo-e2e` 的隔离 Compose 环境中执行；任一 DB 测试必须使用隔离后的 `flow_test`，不得对常驻 `flow` 执行写入或清理。

## 不做 / 保护边界

- 不重做已关闭的前端一致性 Task 0–9，也不把深链批次一重复记为未完成。
- 不为填满页面将指标字典定义数冒充数据覆盖率；不把不适用指标硬造为适用。
- 不把公开财报 C 级未通过、真实企业授权未取得的状态包装成产品验收通过。
- 不改数据库 schema 或迁移；若 Gate 1 证明必须迁移，先更新路线图与获批规格再另行授权。

## 工作状态

用户已于 2026-09-26 批准实施。Gate 1 初始只读诊断快照固定于基线 `3ff95115` + overlay `1ede2648…`；其中 FY2025 四问工作台 500 根因已由响应模型契约不匹配确认，修复及回归测试在当前工作树通过、本地 API 返回200。代码验收未关闭：其他数据缺口归因待逐项完成；工作树变更归属整理后须在干净 SHA 复验。然后按 Gate 2–5 串行推进。各 Gate 独立验证、更新主线状态并提交推送。
