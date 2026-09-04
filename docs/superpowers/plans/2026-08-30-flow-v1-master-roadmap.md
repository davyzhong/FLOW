# FLOW V1 Master Implementation Roadmap

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本路线图保留 V1 Phase 1–10 原始分期；功能窄切片已交付，Phase 10 的部署、备份恢复和深度可观测性按 D038 转入 Pilot Readiness。当前为 Pilot Phase 2 部分完成，不应从历史任务列表推断生产就绪。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a deployable end-to-end FLOW V1 that converts logistics-supply-chain Excel data into a canonical financial data layer, deterministic analysis, evidence-backed Finance BP findings, and consistent PPTX/XLSX/HTML/PDF outputs.

**Architecture:** Build a modular monolith with three runtime processes: a Next.js web application, a FastAPI application exposing versioned domain APIs, and a Celery worker reusing the same Python domain modules. PostgreSQL is the sole canonical analytical store, S3-compatible object storage preserves immutable source and report files, and Redis carries background jobs; every downstream view consumes versioned snapshots rather than raw Excel.

**Tech Stack:** Node.js 24 LTS, pnpm 10, Next.js 16.3.3, React 19.2, TypeScript 5, Tailwind CSS 4, Apache ECharts 6, Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 18, Polars, openpyxl, Celery, Redis 8, S3/MinIO, python-pptx, Jinja2, Playwright/Chromium, pytest, Vitest, Playwright Test, Docker Compose.

## Global Constraints

- V1 user is Finance BP in a logistics enterprise's supply-chain business; no management-only dashboard or role switch.
- Analysis grain is monthly, with current month, YTD, budget, prior-year comparison, and trailing 12-month trend.
- The core analytical dimensions are customer segment × logistics product; organization, region, customer, period, and management account are auxiliary dimensions.
- All downstream functions read only canonical tables and immutable metric/report snapshots; no page, AI prompt, or renderer reads raw Excel directly.
- Original files and original values are immutable; each normalization creates a new import version with value-level lineage.
- Deterministic code calculates every financial number, variance, bridge, and driver contribution; AI may explain and arrange only referenced objects.
- Facts, judgments, and hypotheses remain separate typed objects.
- A Finding with unverified critical evidence cannot enter a formal Report Snapshot.
- PPTX, analytical XLSX, HTML, and PDF render from the same immutable Report Snapshot.
- V1 accepts one multi-sheet workbook per analysis batch and does not promise arbitrary-workbook compatibility.
- V1 includes blocking errors, confirmable warnings, explicit analytical degradation, and retryable rendering.
- The system must run with Docker Compose locally and remain portable to a private or managed container platform.
- All monetary values use `Decimal`/PostgreSQL `NUMERIC`; binary floating point is forbidden for persisted financial values.
- All timestamps are stored as UTC and rendered in the workspace time zone; analysis periods use calendar month keys (`YYYY-MM`).
- Each phase ends with automated verification, an independently reviewable commit, and a push to `origin`.

---

## 1. Delivery Shape

### 1.0 Architecture decision rationale

- Next.js 16.3.3 is the Active LTS security line at the planning date, so the web baseline avoids a maintenance-only major: <https://nextjs.org/blog>.
- Importing workbooks, calculating snapshots, and rendering reports are heavy, retryable operations. FastAPI's own guidance recommends a separate queue/worker tool such as Celery for heavy background computation: <https://fastapi.tiangolo.com/tutorial/background-tasks/>.
- PostgreSQL 18 supplies the canonical relational and numeric foundation while keeping deployment portable: <https://www.postgresql.org/docs/18/>.
- The modular-monolith boundary is deliberate: V1 needs strong domain transactions and fast iteration more than independent service scaling. API and worker remain separate processes but share one tested application/domain package.

### 1.1 Runtime topology

```text
Browser
  │
  ▼
Next.js web ───────► FastAPI /api/v1
                        │
              ┌─────────┼──────────┐
              ▼         ▼          ▼
         PostgreSQL   S3/MinIO   Redis queue
                                    │
                                    ▼
                              Celery worker
                        import / metrics / reports
```

The API owns transactions and domain policy. The worker calls application services, never database tables directly. The web app consumes an OpenAPI-generated TypeScript client and contains no duplicate metric formulas.

### 1.2 Repository map

```text
FLOW/
├── apps/web/                         # Next.js Finance BP workspace
│   ├── app/                          # routes and layouts
│   ├── components/                   # page-owned and shared UI
│   ├── features/                     # intake, dashboard, investigation, publishing
│   ├── lib/api/                      # generated client adapter
│   └── tests/                        # Vitest and Playwright tests
├── services/api/
│   ├── src/flow_api/
│   │   ├── api/                      # thin HTTP routes and dependencies
│   │   ├── application/              # use cases and transaction boundaries
│   │   ├── domain/                   # entities, value objects, policies
│   │   ├── infrastructure/           # SQLAlchemy, S3, Redis, AI adapters
│   │   ├── intake/                   # workbook recognition and normalization
│   │   ├── metrics/                  # deterministic metric engine
│   │   ├── analysis/                 # driver models and finding generation
│   │   ├── investigation/            # evidence, reviews, conclusions
│   │   ├── copilot/                  # referenced AI prompts and validators
│   │   └── publishing/               # report snapshots and renderers
│   ├── migrations/                   # Alembic schema history
│   └── tests/                        # unit, contract, integration, golden tests
├── packages/contracts/               # committed OpenAPI document and TS types
├── fixtures/
│   ├── canonical/                    # known-answer canonical rows
│   ├── workbooks/                    # standard and non-standard Excel samples
│   ├── expected/                     # expected metrics, bridges, findings
│   └── reports/                      # report golden metadata and visual baselines
├── templates/
│   ├── excel/                        # workbook contract definitions
│   └── reports/                      # PPTX, analytical XLSX, HTML templates
├── infra/                            # Docker Compose and container definitions
├── scripts/                          # reproducible developer and CI commands
└── docs/                             # product spec, plans, contracts, runbooks
```

### 1.3 Stable cross-module interfaces

The following identifiers are fixed across all phase plans:

```python
BatchId = UUID
SourceFileId = UUID
ImportVersionId = UUID
MetricDefinitionId = str
MetricSnapshotId = UUID
FindingId = UUID
EvidenceId = UUID
ReportSnapshotId = UUID
PublicationId = UUID
```

```python
class JobReceipt(BaseModel):
    job_id: UUID
    resource_id: UUID
    status: Literal["queued", "running", "succeeded", "failed"]

class ObjectRef(BaseModel):
    object_type: Literal["metric", "finding", "evidence", "source_record"]
    object_id: str
    version_id: str

class Money(BaseModel):
    amount: Decimal
    currency: str = "CNY"
```

## 2. Phase Sequence and Release Gates

| Phase | Independently testable deliverable | Entry dependency | Exit gate |
|---|---|---|---|
| 1. Foundation & Contracts | Running web/API/worker stack and migrated canonical schema | Approved V1 spec | Health checks, migrations, generated client, CI all pass |
| 2. Canonical Fixture & Excel Contract | Known-answer 12-month logistics dataset and generated FLOW workbook | Phase 1 schema | Workbook round trip has zero semantic loss |
| 3. Intake, Mapping & Quality | Standard and non-standard workbook ingestion into an immutable batch | Phase 2 fixtures | Mapping, lineage, quality, reconciliation, retry tests pass |
| 4. Metric Snapshots | Versioned month/YTD/budget/YoY metrics from canonical facts | Published batch | Known-answer metrics and aggregation invariants pass |
| 5. Analysis & Findings | Profit/cash driver models and ranked Finding candidates | Metric Snapshot | Bridges add to total variance and impacts are reproducible |
| 6. Finance BP Dashboard | High-density dashboard backed only by snapshot APIs | Findings available | Visual, filter, snapshot-consistency, accessibility tests pass |
| 7. Investigation & Review | Evidence-first drill-down and release eligibility workflow | Dashboard findings | Source-line lineage and evidence gate pass end to end |
| 8. AI Copilot | Referenced explanations, questions, and narrative drafts | Approved domain objects | Citation and no-invented-number evaluations pass |
| 9. Unified Publishing | PPTX/XLSX/HTML/PDF from one Report Snapshot | Approved findings | Cross-format metric equality and open/render checks pass |
| 10. Operational Hardening | Recovery, audit, observability, backups, security baseline | Full narrow slice | V1 acceptance suite and deployment rehearsal pass |

## 3. Phase Plans

### Phase 1: Foundation & Contracts

Detailed executable plan: [2026-08-30-flow-v1-phase-1-foundation.md](2026-08-30-flow-v1-phase-1-foundation.md)

Deliverables:

- reproducible Node/Python/container toolchain;
- web, API, and worker processes;
- typed domain identifiers and lifecycle enums;
- PostgreSQL schema covering source, canonical, metric, investigation, and publication object identities;
- versioned `/api/v1` health/workspace endpoints;
- committed OpenAPI contract and generated TypeScript types;
- CI gates for format, lint, type, unit, migration, and smoke tests.

### Phase 2: Canonical Fixture & Excel Contract

Create a phase plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-2-data-contract.md` before implementation, using the verified migration head from Phase 1.

Required tasks and gates:

1. Define field contracts for the ten core workbook sheets in `templates/excel/flow_v1_contract.yaml`.
2. Generate 12 months of actuals and monthly budget for two customer segments, eight logistics products, organizations, regions, customers, management accounts, and AR aging in `fixtures/canonical/`.
3. Encode the known business story and exact expected totals in `fixtures/expected/known_answers.json`.
4. Generate `fixtures/workbooks/flow_standard_v1.xlsx` with stable field IDs, validations, instructions, and version metadata.
5. Import the generated workbook into temporary canonical tables and export it again.
6. Assert row counts, IDs, decimals, null semantics, totals, and relationships are unchanged.
7. Document the contract in `docs/data-contract/flow-v1.md` and commit the actual template artifact.

Exit command:

```bash
make test-data-contract
```

Expected: all workbook contract, known-answer, and round-trip tests pass.

### Phase 3: Intake, Mapping & Quality

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-3-intake.md` after Phase 2 freezes contract version `flow.excel.v1`.

Required tasks and gates:

1. Store source bytes by SHA-256 under immutable object keys and reject accidental overwrite.
2. Detect workbook roles, headers, data regions, types, and row grain.
3. Implement deterministic alias/type matching before calling the AI mapping adapter.
4. Return mapping confidence, rationale, and required confirmations; persist every accepted mapping version.
5. Normalize values through versioned pure functions that emit before/after audit records.
6. Run structural, relationship, business-rule, and reconciliation checks with typed severity.
7. Block publication on missing required sheets/fields, duplicate keys, broken required relations, or reconciliation outside tolerance.
8. Permit warning acknowledgement only with actor and reason.
9. Publish canonical rows and an immutable Batch version atomically.
10. Prove a corrected import creates a new version without changing the previous one.

Exit command:

```bash
make test-intake-e2e
```

Expected: the standard workbook and one deliberately non-standard workbook both produce the same canonical totals; all lineage assertions pass.

### Phase 4: Metric Snapshots

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-4-metrics.md` against the published canonical fixture.

Required tasks and gates:

1. Seed versioned definitions for orders, fulfilled units, revenue, revenue/order, direct cost, cost/order, gross profit, gross margin, fulfillment cost rate, operating profit, AR balance, collection rate, DSO, operating cash flow, and cash conversion.
2. Implement dimension-safe aggregation with explicit semi-additive behavior for balances.
3. Calculate month, YTD, budget variance, prior-year variance, and trailing 12-month series.
4. Persist immutable snapshot values and formula dependency records.
5. Reject snapshot creation when required reconciliation or metric dependencies fail.
6. Prove totals equal the sum of allowed slices and balances do not incorrectly sum across periods.

Exit command:

```bash
make test-metrics-known-answers
```

Expected: exact Decimal comparisons match `fixtures/expected/known_answers.json`.

### Phase 5: Analysis & Findings

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-5-analysis.md` using only Metric Snapshot and canonical-detail repositories.

Required tasks and gates:

1. Implement revenue Volume/Price/Mix decomposition.
2. Implement gross-profit and operating-profit variance bridges.
3. Implement fulfillment-cost rate/volume/efficiency decomposition.
4. Implement AR aging, DSO, collection, and operating-cash impact analysis.
5. Generate typed Finding candidates with fact, impact, materiality, persistence, evidence completeness, and management relevance.
6. Rank findings with a transparent deterministic score and retain component scores.
7. Persist Driver Contributions whose amounts exactly reconcile to each Finding impact.
8. Explicitly degrade analyses when fixture fields are removed.

Exit command:

```bash
make test-analysis-invariants
```

Expected: every bridge reconciles within `0.01 CNY`, and the intended profit/cash deterioration story ranks in the top findings.

### Phase 6: Finance BP Dashboard

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-6-dashboard.md`, using the approved `dashboard-density-v2.html` as visual reference and the generated client as the only data boundary.

Required tasks and gates:

1. Implement workflow navigation and global period/dimension filters.
2. Display batch, quality, reconciliation, and snapshot state.
3. Build eight metric cards with budget, YoY, and YTD budget comparisons.
4. Build 12-month operating/financial trends and profit bridge.
5. Build impact-ranked findings, product table, and customer-segment × product matrix.
6. Link every finding to Investigation with batch/snapshot context preserved.
7. Add loading, empty, degraded, stale, and error states.
8. Verify no browser request accesses source-file endpoints or computes metrics.

Exit command:

```bash
make test-dashboard
```

Expected: component, API-contract, Playwright, accessibility, and screenshot assertions pass at 1440×900 and 1920×1080.

### Phase 7: Investigation & Review

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-7-investigation.md`, using `investigation-evidence-v2.html` as visual reference.

Required tasks and gates:

1. Present anomaly definition, financial impact, bridge, and dimensional drill-down.
2. Expose formula, engine version, data quality, and reconciliation context.
3. Resolve standard records to immutable source file, sheet, and row references.
4. Support Evidence states `pending`, `verified`, and `rejected` with append-only reviews.
5. Provide structured Conclusion sections for verified facts, judgment, open items, and recommendation.
6. Enforce allowed Finding state transitions and report eligibility in the domain layer.
7. Prove rejected/pending critical evidence prevents approval and publishing.

Exit command:

```bash
make test-investigation-e2e
```

Expected: a Finance BP can reproduce, review, approve, and reject the core profit and cash findings with complete audit history.

### Phase 8: AI Copilot

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-8-copilot.md` after Investigation object contracts are stable.

Required tasks and gates:

1. Define a provider-neutral `CopilotProvider` protocol and a deterministic fake provider.
2. Build allow-listed context packets containing only current Batch, Snapshot, Finding, Evidence, and formula references.
3. Require structured output separating facts, judgments, hypotheses, questions, and cited object references.
4. Reject output containing uncited numbers or unknown IDs.
5. Add mapping-explanation, investigation-Q&A, and report-outline use cases.
6. Record prompt template version, provider/model, request references, response, validation, and actor.
7. Run fixed evaluation cases for citation completeness, numeric consistency, insufficient-data degradation, and prohibited unapproved findings.

Exit command:

```bash
make test-copilot-evals
```

Expected: deterministic fake tests pass offline; live-provider tests are opt-in and never gate normal CI.

### Phase 9: Unified Publishing

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-9-publishing.md` after approved Findings exist.

Required tasks and gates:

1. Freeze Report Snapshot content and source object references before rendering.
2. Generate conclusion-first PPTX with overview, scale/revenue, profit/cost, AR/cash, recommendations, metric definitions, and evidence index.
3. Generate analytical XLSX with metrics, variance, trends, drivers, filterable canonical extracts, definitions, quality, and lineage index.
4. Generate semantic HTML with chart/table assets and evidence footnotes.
5. Print PDF from the frozen HTML using pinned Chromium.
6. Persist publication attempts separately so failed rendering can retry without rebuilding the snapshot.
7. Extract rendered values from all formats and compare them to the Report Snapshot.
8. Open PPTX/XLSX packages, inspect PDF pages, and run screenshot regression for HTML/PDF.

Exit command:

```bash
make test-publishing-golden
```

Expected: all formats open, contain identical key values and versions, and pass Chinese-font/layout checks.

### Phase 10: Operational Hardening and V1 Acceptance

Create the executable plan at `docs/superpowers/plans/2026-08-30-flow-v1-phase-10-acceptance.md` after the complete narrow slice works.

Required tasks and gates:

1. Add structured logs, request/job correlation IDs, metrics, and health/readiness probes.
2. Enforce file size/type limits, workbook decompression limits, formula non-execution, and safe object keys.
3. Add database/object-store backup and restore rehearsal scripts.
4. Test worker retry, idempotency, dead-job visibility, and publication retry.
5. Run migration upgrade from an empty database and from the previous release tag.
6. Verify all ten V1 acceptance criteria from the product specification.
7. Produce deployment, recovery, data-contract, and Finance BP user runbooks.
8. Tag the verified release `v0.1.0` only after the full acceptance suite passes.

Exit command:

```bash
make acceptance
```

Expected: one command provisions the stack, imports both workbook fixtures, publishes a batch, computes snapshots/findings, approves evidence, and generates all four report formats.

## 4. Cross-Cutting Test Pyramid

```text
Few:     Playwright end-to-end + report visual/package regression
Some:    API/application integration + PostgreSQL/MinIO/Redis containers
Many:    pure domain, workbook, metric, bridge, policy, and serializer unit tests
Always:  known-answer fixtures + Decimal equality + lineage assertions
```

Required CI jobs:

```text
static-python
static-web
unit-python
unit-web
contracts
integration
migrations
e2e-narrow-slice
report-golden
```

## 5. Requirement Traceability

| Product-spec requirement | Implementing phase(s) |
|---|---|
| Standard modular Excel workbook | 2 |
| Non-standard Excel mapping and cleaning | 3, 8 |
| Immutable source, batch, lineage, quality, reconciliation | 1, 3 |
| Canonical facts and dimensions | 1, 2, 3 |
| Metric definition, version, snapshot | 1, 4 |
| Deterministic variance and drivers | 4, 5 |
| High-density Finance BP dashboard | 6 |
| Evidence-first Investigation and review | 7 |
| Bounded AI interpretation and orchestration | 8 |
| PPTX/XLSX/HTML/PDF from one snapshot | 9 |
| Blocking errors, warnings, degradation, retry | 3, 5, 9, 10 |
| Deployment neutrality and operational readiness | 1, 10 |

## 6. Planning and Execution Policy

- Phase 1 is fully decomposed in the accompanying executable plan.
- Before each later phase begins, convert that phase's fixed deliverables above into the same test-first step format, using the actual interfaces and migration head produced by the prior phase.
- Do not write all later low-level plans against imagined generated schemas; this prevents stale paths and type signatures while preserving the complete scope and exit gates here.
- A phase may start only when its entry dependency is merged, verified, and pushed.
- A failed exit gate keeps the phase open; it is not deferred to a later phase.

## 7. Plan Self-Review Record

- **Specification coverage:** Product-spec sections 1–18 map to Phases 1–10; the traceability table has no uncovered V1 requirement.
- **Scope control:** Management-only views, daily/realtime monitoring, issue-assignment workflow, rolling forecasts, Word output, and arbitrary multi-file ingestion are absent from implementation phases.
- **Boundary consistency:** `BatchId`, `ImportVersionId`, `MetricSnapshotId`, `FindingId`, `EvidenceId`, `ReportSnapshotId`, and `PublicationId` retain the same meanings in every phase.
- **Numeric consistency:** Persisted and calculated financial values use Decimal/NUMERIC; no renderer or AI adapter calculates money.
- **Publication consistency:** Every output renderer consumes one immutable Report Snapshot and can retry independently.
- **Placeholder scan:** The roadmap and Phase 1 plan contain no deferred field, unnamed error handling, or unassigned test requirement.
