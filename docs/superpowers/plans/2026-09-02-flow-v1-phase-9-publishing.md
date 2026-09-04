# FLOW V1 Phase 9 Unified Publishing Implementation Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：Phase 9 功能切片已有实现与[阶段验收](../../implementation/phase-9-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 接入映射、审批资格、Copilot 审计或冻结报告相关实现以本次修复验收为补充。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Apply `superpowers:test-driven-development` to every behavior change and `superpowers:verification-before-completion` before declaring the phase complete. Keep the seven root-level user files untracked and out of every commit.

**Goal:** Render PPTX, analytical XLSX, semantic HTML, and PDF from one frozen, immutable Report Snapshot with publication attempts persisted for retry, and prove via golden extraction that all four formats carry identical key values, versions, and evidence index.

**Architecture:** A `ReportSnapshotService` freezes a snapshot version from the published Metric Snapshot plus approved Findings (status check enforced), items referencing metric/finding/evidence/conclusion objects. Renderers are pure functions `bytes/data = render(snapshot_view)` for PPTX (python-pptx), XLSX (openpyxl), and HTML (dependency-free semantic markup with evidence footnotes). PDF prints the frozen HTML through the repository's pinned Chromium via `npx playwright pdf` — no extra Python dependency. `PublicationService` records each `PublicationAttempt` (queued→running→succeeded/failed) with the stored object, so failures retry without rebuilding the snapshot. A golden gate extracts key values from all four artifacts and diffs them against the snapshot view.

**Tech Stack:** Python 3.13, python-pptx, openpyxl, SQLAlchemy 2, PostgreSQL, Node/Playwright (pinned Chromium) for PDF printing, pytest, Ruff, strict mypy, Make.

**Approved design:** `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §13.

## Global constraints

- Only `approved` Findings enter a Report Snapshot; snapshot freeze is idempotent per (metric_snapshot_id, version).
- Renderers never compute money: every value comes from the frozen snapshot view (exact decimal strings).
- Publication attempts persist independently; failed rendering retries without rebuilding the snapshot.
- All formats carry the same identity footer: batch id, snapshot id, analysis run id, report version, engine versions, generation timestamp.
- HTML/PDF include evidence footnotes with finding/evidence IDs; XLSX includes definitions, quality and lineage index sheets.

## Task 1: Snapshot freeze service

**Files:**

- Create: `services/api/src/flow_api/publishing/__init__.py`
- Create: `services/api/src/flow_api/publishing/models.py`
- Create: `services/api/src/flow_api/publishing/service.py`
- Test: `services/api/tests/publishing/test_freeze.py`

- [ ] Freeze from published Metric Snapshot + approved findings; reject when no approved findings exist (typed error); idempotent versioning; item ordering stable.

## Task 2: Renderers

**Files:**

- Create: `services/api/src/flow_api/publishing/renderers.py`
- Test: `services/api/tests/publishing/test_renderers.py`

- [ ] PPTX: conclusion-first slide order (overview, scale/revenue, profit/cost, AR/cash, recommendations, metric definitions, evidence index).
- [ ] XLSX: metrics, variance, drivers, definitions, quality, lineage index sheets.
- [ ] HTML: semantic sections + tables + evidence footnotes; identity footer.
- [ ] PDF: print frozen HTML via `npx playwright pdf` (pinned Chromium), file→bytes.

## Task 3: Publication service and API

**Files:**

- Create: `services/api/src/flow_api/publishing/publication.py`
- Create: `services/api/src/flow_api/api/routes/publishing.py`
- Create: `services/api/src/flow_api/api/schemas/publishing.py`
- Modify: router, contracts
- Test: `services/api/tests/publishing/test_publication.py`, `tests/api/test_publishing.py`

- [ ] Attempts persist per format with stored object; retry creates a new attempt; typed API `POST /api/v1/publishing/snapshots/{id}/publish` and `GET .../attempts`.

## Task 4: Golden gate

**Files:**

- Create: `scripts/test_publishing_golden.sh`
- Modify: `Makefile` (`test-publishing-golden`), `.github/workflows/ci.yml` (`report-golden` job)
- Test: `services/api/tests/publishing/test_golden.py`

- [ ] Extract key values from PPTX/XLSX/HTML/PDF and compare with the snapshot view; verify page count ≥ 1 for PDF and identity footers in all formats.

Exit command: `make test-publishing-golden`

Expected: all formats open, contain identical key values and versions, and pass Chinese-font/layout checks.
