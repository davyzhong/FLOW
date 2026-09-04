# FLOW Pilot Readiness Phase 1 — Excel Intake and Report Delivery Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：Pilot Phase 1 已有[历史出口门禁记录](../../implementation/phase-pilot-1-user-closure.md)，用户闭环实现及后续发现的映射、警告确认、冻结和下载问题已有补修。原始步骤保留；历史门禁通过不等于当前真实对象存储发布链路已通过验收。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **Execution rule:** Apply `superpowers:test-driven-development` to every behavior change,
> `superpowers:systematic-debugging` to failures, and
> `superpowers:verification-before-completion` before closing the phase. Keep the seven
> root-level user archive files untracked and out of every commit.

**Goal:** Give a Finance BP two complete, browser-visible workflows: (1) download the
governed FLOW template or upload an external XLSX, inspect and confirm mappings, review
automatic cleaning/quality/reconciliation results, and publish the canonical import; and
(2) freeze an approved report snapshot, generate PPTX/XLSX/HTML/PDF artifacts, inspect
attempt status, and download the exact persisted bytes.

**Product boundary:** FLOW remains a governed analysis product, not an in-browser
spreadsheet editor. Cleaning is versioned normalization plus explicit quality decisions.
Blocking source-cell errors are corrected in the source workbook and re-uploaded as a new
version; FLOW never silently overwrites raw values. Manual mapping overrides are allowed
only against profiled source sheets/columns and produce a new immutable mapping version.

**Architecture:** Extend the existing Phase 3 Intake and Phase 9 Publishing services rather
than creating parallel pipelines. The browser talks only to typed `/api/v1` routes through
the Next proxy. Generated files live in the content-addressed object store; database rows
hold their immutable identity and download authorization boundary. Every screen renders
explicit loading, empty, blocked, ready, failed, and retry states.

## Exit gate

```bash
make test-user-closure-e2e
```

The gate must start from a clean database and prove in a real browser that a Finance BP can
complete both workflows. It also re-runs Intake, Publishing Golden, Investigation, and
Dashboard regression gates.

## Task 1 — Freeze user journeys and typed contracts

**Files:**

- Create API contract tests for template download, mapping override, cleaning summary,
  standardized workbook export, report snapshot list/freeze, artifact status, and download.
- Create web component tests for all workflow states and accessible keyboard operation.
- Create browser specs for the standard-workbook happy path and report download path.

**Acceptance:** Tests fail for missing behavior before implementation. No test may bypass
the public API with direct database writes except fixture setup.

## Task 2 — Deliver a governed FLOW Excel template

- Add a deterministic blank `flow.excel.v1` renderer with instructions, stable field IDs,
  types, validations, protected contract rows, and empty editable data regions.
- Expose `GET /api/v1/intake/templates/flow.excel.v1` with a fixed safe filename, exact XLSX
  content type, content length, and no-store headers.
- Prove the downloaded template parses as the frozen contract and remains byte-stable.

## Task 3 — Make mapping review corrective, versioned, and auditable

- Add typed sheet and field override requests that reference only profiled source names and
  columns plus valid contract IDs.
- Reject duplicate source-column use, incompatible or unknown targets, stale source hashes,
  and cross-batch mapping identities.
- Applying an override creates a new `MappingVersion`; confirmation records actor and time.
- Return mapping coverage, unresolved requirements, confidence, rationale, and source field
  types needed by the browser.

## Task 4 — Expose governed cleaning and standardized output

- Add an import cleaning summary: raw/transformed counts, transform rules and versions,
  representative before/after samples, quality issues, and reconciliation results.
- Never return whole source workbooks or sensitive cell dumps in list responses; samples are
  strictly bounded and tied to sheet/row/column lineage.
- Add standardized-workbook export for a validated import using the canonical package and
  frozen `flow.excel.v1` renderer. The export is derived data and never replaces source bytes.
- Preserve the correction path: a blocked version stays immutable; re-upload creates a new
  source/mapping/import history entry.

## Task 5 — Build the Finance BP Data Workbench

- Add `/data` with a dense five-stage workflow: prepare → upload/profile → map/confirm →
  clean/validate → publish.
- Support drag/drop and file picker, upload progress, size/type errors, mapping tables with
  confidence and override controls, issue/reconciliation panels, warning acknowledgement,
  standardized-workbook download, and immutable version history.
- Replace dashboard placeholder anchors with real navigation while keeping the dashboard
  visual baseline stable.
- Meet accessible labels, focus order, status announcements, and non-color-only severity.

## Task 6 — Repair publication persistence before exposing downloads

- Persist or reuse the `StoredObject` row returned by content-addressed storage before a
  successful `PublicationAttempt` may reference it.
- A renderer/storage/database failure must leave a failed attempt with no downloadable
  object; retry creates a new append-only attempt.
- Validate allowed formats at the API boundary and keep rendered bytes immutable.

## Task 7 — Complete report snapshot and artifact APIs

- Add `POST /api/v1/publishing/snapshots` to freeze from a published metric snapshot and
  approved findings, plus `GET /api/v1/publishing/snapshots` for discovery.
- Expand attempt responses with stable attempt identity, size, content type, timestamps, and
  download availability.
- Add `GET /api/v1/publishing/attempts/{attempt_id}/download`; stream only succeeded,
  database-linked objects, validate their SHA-256 on read, use a server-owned filename, and
  set content-disposition/no-store/nosniff headers.
- Wire a pinned Chromium PDF printer into the supported deployment path; if unavailable,
  expose an explicit failed/retryable state rather than a false success.

## Task 8 — Build the Report Center

- Add `/reports` with report snapshot identity, governed source status, format selection,
  generation progress, append-only attempt history, retry action, and direct download.
- Explain why report freeze is blocked when findings are unapproved and link back to the
  Investigation flow.
- Show PPTX/XLSX/HTML/PDF as independent artifacts from the same frozen snapshot; never
  regenerate a snapshot merely to retry one format.

## Task 9 — End-to-end and regression gate

- Add `make test-user-closure-e2e` and isolated CI job.
- Prove template download, standard and non-standard upload, mapping confirmation/override,
  deterministic cleaning, warning acknowledgement, publication, standardized export,
  snapshot freeze, artifact generation, byte-for-byte download, failure, and retry.
- Re-run OpenAPI generation/drift, lint, typecheck, API tests, accessibility checks, and the
  Phase 3/6/7/9 gates.

## Task 10 — Evidence, knowledge base, release

- Record screenshots and exact gate results in a phase verification document.
- Update project state, decision log, change impact map, indexes, inventory, and checksums.
- Commit only phase files, push `main`, require all CI jobs to pass, and publish the next
  baseline tag only at the exact green commit.

## Explicitly deferred

- Multi-tenant roles and enterprise SSO (next minimal-security phase).
- In-browser arbitrary cell editing or formula execution.
- Scheduled ingestion, ERP connectors, and report distribution by email/chat.
- V1.1 feature expansion not supported by pilot evidence.
