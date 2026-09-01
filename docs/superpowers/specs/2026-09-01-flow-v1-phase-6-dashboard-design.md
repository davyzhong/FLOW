# FLOW V1 Phase 6 Finance BP Dashboard Design

**Status:** Approved for autonomous implementation under the project owner's standing authorization

**Date:** 2026-09-01

**Scope:** Read-only dashboard projection API, high-density Finance BP workspace, governed filters, states, accessibility, and visual regression

## 1. Purpose

Phase 6 turns the governed outputs of Phase 4 and Phase 5 into the first production user surface. It must let a logistics Finance BP scan results, locate the financially important variances, and enter an Investigation without allowing the browser to read source files, canonical facts, or recalculate metrics and Findings.

The approved `dashboard-density-v2.html` remains the visual and information-density reference. This phase implements its operating structure with real governed objects and removes prototype-only claims that the current data contracts cannot prove.

```text
Published Metric Snapshot series + published Analysis Run
                            ↓
              Read-only Dashboard Projection
                            ↓
           Generated TypeScript client contract
                            ↓
       Finance BP Dashboard + Investigation links
```

## 2. Non-negotiable decisions

1. The browser calls only the versioned Dashboard API through the generated client. It does not call source-file, canonical-fact, metric-value, or analysis persistence endpoints.
2. Dashboard code formats values but does not calculate financial metrics, variances, Driver Contributions, Finding qualification, or ranking.
3. Every response binds and exposes `batch_id`, `import_version_id`, `metric_snapshot_id`, `analysis_run_id`, definition/policy identity, and as-of period.
4. Only published Metric Snapshots and a published Analysis Run bound to the same snapshot/import are eligible.
5. Missing comparison windows, unsupported dimensional grains, degraded Analysis Results, and stale data are explicit states. The API never fills gaps with zero, estimates, or hidden allocations.
6. Findings remain the immutable total-scope results produced by Phase 5. When a dashboard dimension filter is active, the UI labels them `全局分析结果`; it does not imply that Findings were recalculated for that slice.
7. The profit bridge is the available T12 prior-year operating-profit bridge. The approved prototype's budget-bridge label is not copied because Phase 5 does not yet publish a budget bridge.
8. The data-quality strip reports governed status and issue counts. It does not invent a percentage score such as the prototype's `98.7%`.
9. The prototype's AI summary is replaced in Phase 6 by a deterministic `本期重点` digest containing existing Finding titles and impacts. AI narration belongs to Phase 8.
10. The visual system keeps the approved blue-white, dense enterprise-analysis direction: dark workflow rail, compact controls, eight metrics, chart/table/matrix density, restrained semantic color, and minimal decoration.

## 3. User workflow and routes

### 3.1 Primary route

`/` is the Finance BP operating dashboard.

The first viewport at 1440×900 contains:

- workflow navigation;
- dashboard title, as-of context, filters, and report action;
- data-quality/reconciliation/snapshot state;
- eight metric cards;
- 12-month operating/financial trend;
- operating-profit bridge;
- ranked Findings.

The lower viewport contains:

- logistics-product performance table;
- customer-segment × logistics-product gross-margin matrix;
- deterministic period highlights and full-analysis entry.

### 3.2 Investigation handoff

Every Finding links to:

```text
/investigations/{finding_id}
  ?batch_id={batch_id}
  &metric_snapshot_id={metric_snapshot_id}
  &analysis_run_id={analysis_run_id}
```

Phase 6 provides a context-receipt shell so the link is valid and the immutable IDs remain visible. Phase 7 replaces that shell with the complete evidence and review workspace.

### 3.3 Navigation

The left rail follows the approved Finance BP workflow:

- 本期工作：数据导入、数据质量、经营驾驶舱、分析调查；
- 分析专题：规模与收入、盈利与成本、应收与现金；
- 管理与交付：指标与口径、洞察与结论、报告中心、批次与发布记录。

Only implemented routes are active links. Future modules render disabled navigation items with accessible `即将开放` text rather than dead interactive controls.

## 4. Dashboard projection API

### 4.1 Endpoint

```http
GET /api/v1/dashboard/overview
```

Optional query parameters:

- `period_view=month|ytd`, default `month`;
- `organization_id`;
- `customer_segment_id`;
- `logistics_product_id`;
- `region_id`.

The endpoint selects the latest eligible published Analysis Run and its bound snapshot. A future explicit-history endpoint may select older identities; Phase 6 never silently combines different imports, metric definition sets, or analysis policies.

### 4.2 Response sections

`DashboardOverviewResponse` contains:

- `context`: immutable IDs, period, metric definition set/hash, metric engine, analysis policy/hash/engine, generated timestamp;
- `filter_options`: typed dimension IDs/names and a capability matrix describing supported combinations;
- `active_filters`: normalized selections and `is_total_scope`;
- `data_status`: batch/import state, quality status, issue counts, warning acknowledgements, reconciliation state, snapshot/run state, freshness status;
- `metric_cards`: exactly eight ordered cards with precomputed primary, budget, YoY, and YTD-budget displays or typed unavailable reasons;
- `trends`: up to 12 published month snapshots from the same import/definition lineage, with explicit coverage count and missing months;
- `profit_bridge`: Phase 5 `operating_profit_bridge` result and ordered Driver Contributions, reconciliation and comparison basis;
- `findings`: Phase 5 order, score, exact impact, evidence count/status, Finding IDs, scope label, and Investigation URL inputs;
- `product_table`: revenue, orders, gross margin, fulfillment-cost rate, and the best available explicitly labelled published comparison from snapshot grains;
- `margin_matrix`: customer-segment × logistics-product actual gross margin and an explicitly labelled published comparison point variance;
- `highlights`: deterministic projection of the leading published Findings, without new causal or recommendation text;
- `degradations`: typed, panel-scoped codes and messages.

All financial numbers cross the JSON boundary as exact decimal strings. Display-ready signed text may be included only when produced by one tested formatter shared by the projection layer; the browser must not derive percentages or financial differences.

### 4.3 Read boundary

The projection repository may read:

- published `MetricSnapshot`, `MetricDefinition`, and `MetricValue` rows;
- published `AnalysisRun`, `AnalysisResult`, `AnalysisDriver`, `Finding`, `FindingScoreComponent`, and `Evidence` rows;
- their bound batch/import/period/dimension, quality, warning, and reconciliation metadata.

It may not read raw object bytes, workbook sheets, source values, canonical fact rows, or lineage payloads. Those belong to Intake and Investigation, not the Dashboard.

### 4.4 Snapshot series

One Metric Snapshot stores comparison windows for one as-of period; it is not a 12-month time series. The dashboard trend therefore reads up to 12 published snapshots with:

- the same `import_version_id`;
- the same metric definition set/hash and engine version;
- successive as-of periods;
- `actual_month` total-scope values.

The Phase 6 deterministic fixture bootstrap publishes the required monthly snapshot series through the existing Metric Snapshot service. If fewer than 12 snapshots exist, the trend renders the available points and reports `partial_series`; it never computes missing months from canonical facts.

## 5. Filter semantics

The UI exposes period view, organization, customer segment, logistics product, and region. Available combinations come from metric grain coverage, not from assumptions.

- total scope supports all eight cards;
- organization supports operating and financial metrics that declare organization grain;
- customer segment supports operating and AR metrics but not organization-only financial metrics;
- logistics product and region support operating metrics but not financial or AR metrics;
- customer segment × logistics product supports operating metrics and the margin matrix;
- unsupported combinations are disabled by `filter_options`; a manually supplied unsupported query returns a typed `422 unsupported_filter_combination` response;
- a supported slice can still degrade individual cards whose metric definition does not support that grain;
- product table and matrix remain honest projections of available snapshot grains and state their scope.

Changing a filter issues a new typed Dashboard API request. No client-side aggregation of rows is allowed.

## 6. Dashboard content

### 6.1 Eight metric cards

Stable order:

1. 履约订单量 — `orders`;
2. 营业收入 — `revenue`;
3. 单均收入 — `revenue_per_order`;
4. 毛利率 — `gross_margin`;
5. 履约成本率 — `fulfillment_cost_rate`;
6. 经营利润 — `operating_profit`;
7. 应收账款 — `ar_balance`, with DSO companion;
8. 经营现金流 — `operating_cash_flow`, with cash-conversion companion.

Cards show the selected month/YTD actual, budget variance, YoY variance, and YTD budget variance when those governed values exist. Missing catalog support—such as an order budget or product-grain operating cash flow—shows `—` plus an accessible reason, never `0`.

Semantic direction is metric-specific. Higher revenue is not automatically healthy if profitability falls; colors represent only the sign against the configured comparison meaning for that field, not a universal good/bad inference.

### 6.2 Trend

The 12-month combined chart shows:

- revenue as bars;
- operating profit as a line;
- gross margin as a second line or compact aligned strip;
- operating cash flow in a synchronized lower band when space permits.

Each point is a published `actual_month` Metric Value from a distinct snapshot. The chart exposes text/table equivalents for accessibility.

### 6.3 Profit bridge

The bridge renders the Phase 5 `operating_profit_bridge` Driver Contributions in persisted order. It displays comparison basis, impact, reconciliation status, and degraded message. It does not reinterpret Driver labels or recalculate bar totals.

### 6.4 Findings

The list is sorted by persisted `total_score`, then stable Finding identity. Each row shows:

- factual title;
- signed impact and unit;
- score;
- verified/total evidence count;
- comparison basis;
- total/global scope label when filters are active;
- Investigation link with all required identities.

No `confidence` marketing label is generated from evidence counts. The persisted legacy confidence field is not presented as causal certainty.

### 6.5 Product table and margin matrix

The product table uses persisted logistics-product grains. It never allocates organization-only operating profit or organization-only budget to products. Comparison columns use the available published grain with this priority: budget comparison when that exact grain exists, otherwise YoY comparison, otherwise typed unavailability. The visible header always names the selected basis.

The matrix uses the supported customer-segment × logistics-product grain. Cell color maps the persisted gross-margin point variance for the explicitly labelled comparison basis. Current fixture budget exists only at organization grain, so V1 uses the published YoY point variance for matrix cells and states `同比`; it never allocates organization budget. The displayed primary number is actual gross margin. A legend and non-color comparison value make the matrix accessible.

## 7. State model

The app has first-class states:

- `loading`: stable skeletons preserving the dashboard geometry;
- `empty`: no eligible published Analysis Run, with a link to data import;
- `error`: API/network failure with retry and a non-sensitive error code;
- `degraded`: panel-level unavailable data with exact cause;
- `partial_series`: fewer than 12 aligned monthly snapshots;
- `stale`: snapshot freshness threshold exceeded, without hiding the data;
- `ready`: all required primary sections available.

An unavailable panel is not removed because disappearance would make the user mistake missing analysis for a healthy state.

## 8. Visual system

The accepted concept is a dense, restrained Finance BP command surface rather than a marketing dashboard.

### 8.1 Tokens

- page background: cool gray `#f3f6fa`;
- primary surface: true white `#ffffff`;
- workflow rail: deep navy `#15243a`;
- rail active: `#29435f` with teal rule `#63d0bc`;
- primary text: `#18273b`;
- secondary text: `#66768b`;
- borders: `#dce4ee` / `#e8edf3`;
- positive: `#16816a`;
- negative: `#c8504c`;
- warning: `#b87920`;
- information: `#426683`.

No decorative gradients, glass effects, oversized typography, generic bento layout, or nested card stacks are introduced.

### 8.2 Typography and density

Use a deliberate Chinese enterprise typography stack led by Aptos/PingFang SC with tabular numerals. UI chrome is 12–13px, panel titles 13–14px, metric values 22–26px, and the page title 18–20px. Controls never inherit browser-default typography.

Desktop grid:

- 192px workflow rail;
- four-column metric grid;
- trend / bridge / Findings row in approximately `1.25 / 0.85 / 0.9` proportion;
- product table / matrix row in approximately `1.35 / 1` proportion.

At narrower desktop widths, the rail compacts and lower panels wrap without converting the table-driven design into a card grid. At mobile width, content becomes a readable vertical review surface; desktop density remains the primary V1 target.

## 9. Component architecture

Frontend modules:

- `DashboardApp`: data state and filter orchestration only;
- `WorkflowNav` and `DashboardHeader`;
- `DataStatusBar`;
- `MetricGrid` / `MetricCard`;
- `TrendPanel`;
- `ProfitBridgePanel`;
- `FindingsPanel` / `FindingRow`;
- `ProductPerformanceTable`;
- `MarginMatrix`;
- `DashboardState` primitives for loading, empty, error, stale, and degraded states;
- exact display utilities that never accept raw floats.

Backend modules:

- typed dashboard schemas;
- dashboard eligibility/query repository;
- pure projection/formatting service;
- versioned route;
- deterministic fixture/bootstrap support used by integration and browser tests.

## 10. Accessibility and interaction

- semantic landmarks and one page `h1`;
- visible keyboard focus and logical tab order;
- filter labels associated with controls;
- tables retain headers and captions;
- charts provide a hidden or expandable data table;
- matrix includes text variance and does not rely on color alone;
- status and unavailable reasons use text plus iconography;
- minimum contrast meets WCAG AA;
- motion is limited to loading/selection transitions and respects `prefers-reduced-motion`;
- Investigation links have descriptive accessible names.

## 11. Verification

`make test-dashboard` is the phase gate and must prove:

1. projection schemas and generated client stay in sync;
2. only published, identity-consistent snapshot/run pairs are returned;
3. the eight cards display exact known answers or typed unavailability;
4. 12-month trend values come from 12 published snapshots, not browser or API recomputation from canonical rows;
5. profit bridge and Finding order/impact equal the persisted Phase 5 outputs;
6. dimension coverage and unsupported combinations degrade honestly;
7. Investigation URLs preserve batch, snapshot, run, and Finding identities;
8. component tests cover ready/loading/empty/error/degraded/stale states;
9. Playwright observes no source-file/canonical/metric-value network calls;
10. accessibility checks pass;
11. deterministic screenshots pass at 1440×900 and 1920×1080;
12. the final browser render is visually compared with the approved `dashboard-density-v2.html` reference and recorded in a fidelity ledger.

## 12. Deferred scope

- evidence drill-down and review actions: Phase 7;
- AI narrative and Q&A: Phase 8;
- live report generation: Phase 9;
- role-based permissions and multi-tenant isolation;
- arbitrary user-authored dashboard layouts;
- client-side pivoting or ad-hoc metric formulas;
- budget Driver bridge until a published Phase 5 budget analysis exists.

## 13. Completion boundary

Phase 6 is complete when a clean checkout can bootstrap deterministic governed data, render the Finance BP dashboard through the real API/client boundary, pass component/API/Playwright/accessibility/screenshot gates, and preserve all immutable identities into Investigation links. A static mockup, a page backed by fixture constants, or a visually correct screen that recomputes numbers in JavaScript does not satisfy this phase.
