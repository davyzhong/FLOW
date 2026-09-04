# FLOW V1 Phase 6 Finance BP Dashboard Implementation Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：Phase 6 功能切片已有实现与[阶段验收](../../implementation/phase-6-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **Execution mode:** Autonomous, test-driven, checkpoint commits to `main`, push every completed task.

**Goal:** Deliver a production Finance BP dashboard that projects published Metric Snapshots and Analysis Runs through one typed API/client boundary, preserves the approved high-density design, and passes API, component, accessibility, network-boundary, and visual-regression gates.

**Architecture:** Add a read-only dashboard projection module to FastAPI. It selects one eligible published Analysis Run and its bound Metric Snapshot, queries only governed metric/analysis/metadata tables, and returns exact decimal strings plus typed availability state. The Next.js app consumes only this response via generated contracts and renders the approved dashboard as focused components. A deterministic fixture bootstrap publishes a 12-snapshot series for real API/browser acceptance.

**Tech stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL, React 19, Next.js 16, TypeScript 5.9, Vitest, Testing Library, Playwright, axe-core, CSS modules/global tokens, SVG charts.

**Design reference:** `docs/knowledge-base/03_assets/visual_prototypes/dashboard-density-v2.html`

**Formal design:** `docs/superpowers/specs/2026-09-01-flow-v1-phase-6-dashboard-design.md`

---

## Task 1: Freeze dashboard response contracts and known answers

**Files:**

- Create: `services/api/src/flow_api/dashboard/__init__.py`
- Create: `services/api/src/flow_api/dashboard/models.py`
- Create: `services/api/src/flow_api/api/schemas/dashboard.py`
- Create: `services/api/tests/dashboard/test_dashboard_models.py`
- Create: `fixtures/expected/dashboard_overview_v1.json`
- Create: `services/api/tests/dashboard/test_dashboard_oracle.py`

### Steps

1. Write failing tests for exact-decimal strings, the eight stable card codes/order, typed availability/degradation, immutable identity context, filters, trend coverage, bridge, Findings, product rows, matrix cells, and state enum values.
2. Build the expected response from the independent Phase 2/4/5 known-answer fixtures, not from production Dashboard code.
3. Define frozen internal Pydantic models with `extra="forbid"` and public API schemas with explicit enums.
4. Assert JSON round-trip equality with `dashboard_overview_v1.json`.
5. Run:

```bash
cd services/api && uv run pytest tests/dashboard/test_dashboard_models.py tests/dashboard/test_dashboard_oracle.py -q
```

Expected: PASS.

6. Commit and push:

```bash
git commit -m "test: freeze dashboard projection contract"
git push origin main
```

## Task 2: Build published dashboard eligibility and query repository

**Files:**

- Create: `services/api/src/flow_api/dashboard/repositories.py`
- Create: `services/api/tests/integration/test_dashboard_repository.py`
- Modify: `services/api/tests/integration/analysis_run_support.py`

### Steps

1. Write failing integration tests proving the repository:
   - selects only published Analysis Runs;
   - rejects mismatched snapshot/import identities;
   - returns the latest eligible run deterministically;
   - reads Metric Values, analysis outputs, dimension labels, issue counts, warning acknowledgements, and reconciliation metadata;
   - never queries source objects, Source Records, canonical facts, or lineage values.
2. Add a query-spy/statement allow-list test around Dashboard repository execution.
3. Implement typed repository records and stable ordering.
4. Run:

```bash
cd services/api && uv run pytest tests/integration/test_dashboard_repository.py -q
```

Expected: PASS.

5. Commit and push:

```bash
git commit -m "feat: bind dashboard to published analysis outputs"
git push origin main
```

## Task 3: Project context, data status, filters, and eight metric cards

**Files:**

- Create: `services/api/src/flow_api/dashboard/service.py`
- Create: `services/api/src/flow_api/dashboard/formatting.py`
- Create: `services/api/tests/dashboard/test_dashboard_service.py`
- Create: `services/api/tests/dashboard/test_dashboard_formatting.py`
- Create: `services/api/tests/integration/test_dashboard_cards.py`

### Steps

1. Write failing tests for:
   - exact IDs and version/hash context;
   - quality/reconciliation/freshness states without invented quality percentages;
   - month/YTD primary-value switching;
   - budget, YoY, and YTD budget values read from persisted comparison types;
   - metric-specific display/unit/sign formatting;
   - explicit unavailable reasons for unsupported comparisons/grains;
   - supported and rejected filter combinations.
2. Implement a pure formatter that accepts Decimal/string values and never float.
3. Implement filter capability construction from persisted metric definition grain configuration.
4. Implement the ordered eight-card projection without doing variance arithmetic.
5. Run:

```bash
cd services/api && uv run pytest tests/dashboard tests/integration/test_dashboard_cards.py -q
```

Expected: PASS.

6. Commit and push:

```bash
git commit -m "feat: project governed dashboard metric cards"
git push origin main
```

## Task 4: Publish and project the 12-month Metric Snapshot series

**Files:**

- Create: `services/api/src/flow_api/dashboard/fixture.py`
- Create: `scripts/seed_dashboard_demo.py`
- Create: `services/api/tests/integration/test_dashboard_snapshot_series.py`
- Modify: `services/api/tests/integration/analysis_run_support.py`

### Steps

1. Write a failing integration test that bootstraps the deterministic published import and publishes aligned monthly snapshots from 2025-09 through 2026-08 using the existing Metric Snapshot service.
2. Assert each trend point comes from one published snapshot with the same import, definition hash, and engine version.
3. Assert the repository returns `partial_series` and exact missing months when snapshots are removed; it must not backfill from canonical facts.
4. Implement an idempotent demo bootstrap callable from tests and local development.
5. Run:

```bash
cd services/api && uv run pytest tests/integration/test_dashboard_snapshot_series.py -q
```

Expected: 12-point exact series PASS; partial-series degradation PASS.

6. Commit and push:

```bash
git commit -m "feat: publish dashboard metric snapshot series"
git push origin main
```

## Task 5: Project profit bridge, Findings, evidence state, and handoff URLs

**Files:**

- Modify: `services/api/src/flow_api/dashboard/service.py`
- Create: `services/api/tests/integration/test_dashboard_analysis_projection.py`

### Steps

1. Write failing tests proving:
   - the bridge reads persisted `operating_profit_bridge` drivers in order;
   - bridge impact, tolerance, basis, and degraded state equal Phase 5 values;
   - Findings preserve persisted score order and exact impact;
   - verified/total Evidence counts are exact;
   - active dimension filters add a total/global scope label but do not rerank or recalculate Findings;
   - every handoff contains Finding, batch, snapshot, and run IDs.
2. Implement the projection without causal confidence labels or new narrative.
3. Run:

```bash
cd services/api && uv run pytest tests/integration/test_dashboard_analysis_projection.py -q
```

Expected: PASS against the frozen Phase 5 oracle.

4. Commit and push:

```bash
git commit -m "feat: expose ranked findings to dashboard"
git push origin main
```

## Task 6: Project product table and customer-segment × product matrix

**Files:**

- Modify: `services/api/src/flow_api/dashboard/service.py`
- Create: `services/api/tests/integration/test_dashboard_dimension_views.py`

### Steps

1. Write failing tests for product revenue, orders, actual gross margin, fulfillment-cost rate, and the best available explicitly labelled published comparison from Metric Value grains.
2. Write failing matrix tests for every customer-segment × logistics-product cell, stable row/column order, exact actual margin, and exact published YoY point variance when that grain has no budget.
3. Assert no organization-only operating profit or organization-only budget is allocated to product rows or matrix cells.
4. Implement projections and panel-scoped degradation.
5. Run:

```bash
cd services/api && uv run pytest tests/integration/test_dashboard_dimension_views.py -q
```

Expected: PASS.

6. Commit and push:

```bash
git commit -m "feat: add dashboard dimensional performance views"
git push origin main
```

## Task 7: Publish the Dashboard API and generated client boundary

**Files:**

- Create: `services/api/src/flow_api/api/routes/dashboard.py`
- Modify: `services/api/src/flow_api/api/router.py`
- Create: `services/api/tests/api/test_dashboard.py`
- Modify: `packages/contracts/openapi.json`
- Modify: `packages/contracts/src/schema.d.ts`
- Modify: `apps/web/lib/api/client.ts`
- Modify: `apps/web/tests/api-client.test.ts`

### Steps

1. Write failing API tests for ready response, `404 dashboard_not_ready`, typed `422 unsupported_filter_combination`, and exact response schema.
2. Add `GET /api/v1/dashboard/overview` and dependency-injected repository/service construction.
3. Regenerate OpenAPI and TypeScript contracts.
4. Add `flowApi.getDashboard(filters)` using generated query/response types.
5. Assert the client calls only `/api/v1/dashboard/overview` and serializes supported filters.
6. Run:

```bash
make contracts
make contracts-check
cd services/api && uv run pytest tests/api/test_dashboard.py -q
make test-web
```

Expected: PASS and no generated diff after `contracts-check`.

7. Commit and push:

```bash
git commit -m "feat: publish typed dashboard API"
git push origin main
```

## Task 8: Build dashboard data orchestration and all state variants

**Files:**

- Create: `apps/web/components/dashboard/dashboard-app.tsx`
- Create: `apps/web/components/dashboard/dashboard-state.tsx`
- Create: `apps/web/components/dashboard/dashboard-types.ts`
- Create: `apps/web/components/dashboard/dashboard-format.ts`
- Modify: `apps/web/app/page.tsx`
- Create: `apps/web/app/loading.tsx`
- Modify: `apps/web/tests/home.test.tsx`
- Create: `apps/web/tests/dashboard-states.test.tsx`

### Steps

1. Write failing component tests for ready, loading, empty, error/retry, stale, degraded, and partial-series states.
2. Write a source-boundary test proving frontend modules contain no financial arithmetic helpers and accept display strings from the API.
3. Implement `DashboardApp` with request cancellation, retry, URL-synchronized supported filters, and stable skeleton geometry.
4. Preserve error codes without exposing stack traces or source data.
5. Run:

```bash
make test-web
```

Expected: all state tests PASS.

6. Commit and push:

```bash
git commit -m "feat: orchestrate dashboard application states"
git push origin main
```

## Task 9: Implement the approved high-density dashboard surface

**Files:**

- Create: `apps/web/components/dashboard/workflow-nav.tsx`
- Create: `apps/web/components/dashboard/dashboard-header.tsx`
- Create: `apps/web/components/dashboard/data-status-bar.tsx`
- Create: `apps/web/components/dashboard/metric-grid.tsx`
- Create: `apps/web/components/dashboard/trend-panel.tsx`
- Create: `apps/web/components/dashboard/profit-bridge-panel.tsx`
- Create: `apps/web/components/dashboard/findings-panel.tsx`
- Create: `apps/web/components/dashboard/product-performance-table.tsx`
- Create: `apps/web/components/dashboard/margin-matrix.tsx`
- Create: `apps/web/components/dashboard/icons.tsx`
- Create: `apps/web/components/dashboard/dashboard.css`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/app/layout.tsx`
- Create: `apps/web/tests/dashboard-content.test.tsx`
- Create: `apps/web/tests/dashboard-accessibility.test.tsx`

### Steps

1. Turn the approved HTML reference into explicit tokens, type scale, container rules, icon inventory, and component variants in `dashboard.css`.
2. Write failing content/semantics tests for navigation, eight cards, chart data alternative, bridge, Finding links, product table, matrix legend, filter labels, and one `h1`.
3. Implement code-native UI in focused components. Use accessible SVG for trend and bridge graphics; do not ship screenshot UI or placeholder assets.
4. Preserve tables and matrix anatomy; do not convert the accepted dense surface into a card grid.
5. Add responsive rules for 1440×900, 1920×1080, narrow desktop, and readable mobile stacking.
6. Run:

```bash
make test-web
make lint
make typecheck
```

Expected: PASS.

7. Commit and push:

```bash
git commit -m "feat: build Finance BP dashboard surface"
git push origin main
```

## Task 10: Add Investigation context-receipt shell

**Files:**

- Create: `apps/web/app/investigations/[findingId]/page.tsx`
- Create: `apps/web/tests/investigation-handoff.test.tsx`

### Steps

1. Write a failing test that opens a Finding URL and verifies all immutable context IDs are retained and shown in an accessible summary.
2. Implement the Phase 7 handoff shell with a clear `调查工作台将在下一阶段展开` state and back navigation.
3. Do not implement evidence review early or fake Investigation conclusions.
4. Run:

```bash
make test-web
```

Expected: PASS.

5. Commit and push:

```bash
git commit -m "feat: preserve dashboard investigation context"
git push origin main
```

## Task 11: Add Playwright, accessibility, network, and screenshot gates

**Files:**

- Modify: `package.json`
- Modify: `pnpm-lock.yaml`
- Create: `playwright.config.ts`
- Create: `apps/web/e2e/dashboard.spec.ts`
- Create: `apps/web/e2e/dashboard-states.spec.ts`
- Create: `apps/web/e2e/dashboard-visual.spec.ts`
- Create: `apps/web/e2e/dashboard-network.spec.ts`
- Create: `apps/web/e2e/__snapshots__/dashboard-1440-linux.png`
- Create: `apps/web/e2e/__snapshots__/dashboard-1920-linux.png`
- Create: `scripts/test_dashboard.sh`
- Create: `scripts/summarize_dashboard.py`
- Modify: `Makefile`
- Modify: `.github/workflows/ci.yml`

### Steps

1. Add pinned Playwright and axe dependencies and a CI-compatible Chromium install step.
2. Seed the real database through `seed_dashboard_demo.py`, start API/Web, and wait for readiness.
3. Test filters, stale/degraded panel messaging, Finding handoff, table/matrix semantics, and retry behavior.
4. Intercept all browser requests and fail if any request targets source-file, source-record, canonical, Metric Value, or Analysis persistence endpoints.
5. Run axe accessibility checks with zero serious/critical violations.
6. Capture deterministic screenshots at 1440×900 and 1920×1080 and freeze baselines.
7. Add `make test-dashboard` and an `dashboard` GitHub Actions job.
8. Run:

```bash
make test-dashboard
```

Expected: API, component, accessibility, network-boundary, and both screenshot assertions PASS.

9. Commit and push:

```bash
git commit -m "test: enforce dashboard acceptance gate"
git push origin main
```

## Task 12: Browser fidelity QA, regression, and project handoff

**Files:**

- Create: `docs/implementation/phase-6-dashboard-fidelity.md`
- Create: `docs/implementation/phase-6-verification.md`
- Modify: `docs/knowledge-base/00_start_here/PROJECT_STATE.md`
- Modify: `docs/knowledge-base/00_start_here/AGENT_START_HERE.md`
- Modify: `docs/knowledge-base/04_decisions/DECISION_LOG.md`
- Modify: `docs/knowledge-base/04_decisions/CHANGE_IMPACT_MAP.md`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`

### Steps

1. Open the approved HTML reference and real Dashboard in the in-app Browser; verify filter and Investigation-handoff interactions.
2. Capture the implementation at 1440×900 and 1920×1080.
3. Use `view_image` on both the accepted reference and latest implementation screenshot.
4. Write a fidelity ledger covering at least navigation/density, copy, typography, palette, metric grid, chart/bridge, Findings, table/matrix, filters, and responsive behavior. Fix every material mismatch before proceeding.
5. Run final verification:

```bash
make test-dashboard
make test-analysis-invariants
make test-api
make test-web
make contracts-check
make lint
make typecheck
git diff --check
```

Expected: all PASS.

6. Record exact results, known limitations, screenshots, CI URL, and the next Phase 7 boundary in `phase-6-verification.md`.
7. Update project state/decision navigation and regenerate/verify all knowledge-base hashes.
8. Stage only Phase 6 files, preserving the seven unrelated root user files.
9. Commit and push:

```bash
git commit -m "docs: record phase 6 dashboard verification"
git push origin main
```

10. Verify the final `main` HEAD GitHub Actions run is green and local/remote `main` match.

## Phase exit criteria

Phase 6 is complete only when:

- a fresh checkout can publish deterministic dashboard data and open the real Dashboard;
- all visible numbers come from the typed Dashboard API and match governed snapshots/runs exactly;
- unavailable grains/comparisons and partial history are explicit;
- the accepted high-density visual structure is faithfully implemented;
- the core workflow is keyboard accessible and screen-reader legible;
- network inspection proves no browser request bypasses the Dashboard boundary;
- 1440×900 and 1920×1080 screenshots pass;
- GitHub Actions is green on the pushed `main` HEAD.
