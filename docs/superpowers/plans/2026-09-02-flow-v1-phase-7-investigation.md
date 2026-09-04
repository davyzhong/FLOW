# FLOW V1 Phase 7 Investigation & Review Implementation Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：Phase 7 功能切片已有实现与[阶段验收](../../implementation/phase-7-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。 接入映射、审批资格、Copilot 审计或冻结报告相关实现以本次修复验收为补充。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Apply `superpowers:test-driven-development` to every behavior change and `superpowers:verification-before-completion` before declaring the phase complete. Keep the seven root-level user files untracked and out of every commit.

**Goal:** Turn a published Finding identity from the dashboard handoff into a governed evidence-first Investigation: reproduce the anomaly context (definition, impact, drivers, formula, engine version, quality, reconciliation, lineage), let a Finance BP verify or reject evidence, record structured conclusions, and move the Finding through enforced review states so only fully verified Findings become report-eligible.

**Architecture:** A domain-layer state machine owns Finding transitions (`candidate → in_review → approved|rejected`, `returned` back transitions) and Evidence decisions (`pending ⇄ verified|rejected`), each appending an immutable `ReviewEvent`. New migration `0008` extends `review_event.decision` with evidence-level decisions. A read-only Investigation API binds `finding_id + batch_id + metric_snapshot_id + analysis_run_id` (D036), projects run-local Driver/Evidence/formula/quality/reconciliation context, and resolves canonical records to immutable source file, sheet, and row references by reading published canonical tables — never recomputing analysis money. The Next.js workbench page consumes the generated typed client only.

**Tech Stack:** Python 3.13, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 18, FastAPI, pytest, Ruff, strict mypy, Next.js 16, React 19, TypeScript 5, Playwright.

**Approved design:** `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §10; visual reference `docs/knowledge-base/03_assets/visual_prototypes/investigation-evidence-v2.html`.

## Global constraints

- Read only the published `AnalysisRun`, its bound `MetricSnapshot`, `ImportVersion`, and canonical tables. No Investigation endpoint recalculates driver money, Finding qualification, or ranking.
- All investigation money values are displayed from persisted `Numeric`/exact strings; Decimal only.
- Finding approval requires every attached Evidence row `verified` and a Conclusion with four non-empty sections; pending or rejected evidence blocks approval (roadmap task 7).
- `ReviewEvent` rows are append-only; `ReviewEvent.decision` gains `evidence_verified`/`evidence_rejected` values via migration 0008.
- Record-level tables display canonical values and lineage references only; contribution amounts stay at driver level.
- Browser reads Investigation data only through typed `/api/v1/investigations` endpoints via the same-origin proxy; no direct canonical/metric/analysis persistence access.
- Published runs, findings rank, and dashboard numbers remain immutable; Investigation changes Finding review state only.
- Do not stage or modify the seven pre-existing root-level untracked user files.

## Task 1: Review state machines and migration 0008

**Files:**

- Create: `services/api/src/flow_api/investigation/__init__.py`
- Create: `services/api/src/flow_api/investigation/state_machines.py`
- Create: `services/api/migrations/versions/0008_investigation_review_decisions.py`
- Test: `services/api/tests/investigation/test_state_machines.py`
- Test: `services/api/tests/investigation/test_migration_0008.py`

- [ ] **Step 1: Write failing state machine tests** — allowed/forbidden transitions, eligibility errors (`evidence_pending`, `evidence_rejected`, `conclusion_incomplete`, `invalid_transition`), append-only event sequence, reviewer/comment capture.
- [ ] **Step 2: Run tests, observe module missing failure.**
- [ ] **Step 3: Implement frozen typed state machines** (pure domain, Session-free decision functions + session-bound appliers that write `ReviewEvent` with `sequence = max+1`).
- [ ] **Step 4: Write migration 0008** extending the `review_event` decision check constraint; test upgrade/downgrade on a scratch database.
- [ ] **Step 5: Focused tests pass.**

## Task 2: Investigation read model and review service

**Files:**

- Create: `services/api/src/flow_api/investigation/repositories.py`
- Create: `services/api/src/flow_api/investigation/service.py`
- Create: `services/api/src/flow_api/investigation/models.py`
- Test: `services/api/tests/investigation/test_service.py`

- [ ] **Step 1: Write failing service tests** using the Phase 5 analysis-run fixtures: identity binding (404/409 semantics), context projection (finding, result, drivers, evidence, metric definition formula + engine version, quality issue counts, reconciliation results, conclusion, review history), evidence decision persistence, finding transitions with blocked approval while evidence pending and while conclusion incomplete, source-record resolution returning file name + sheet + row + canonical values for operating and AR playbooks without recomputing money.
- [ ] **Step 2: Run tests, observe missing modules.**
- [ ] **Step 3: Implement repositories** (identity-bound read queries, source-record lenses per playbook code reading `fact_operating_actual`/`fact_ar_collection` joined to `source_record`/`source_file`, ordered by canonical amount, limited).
- [ ] **Step 4: Implement service + typed Pydantic models** with strict Decimal string serialization.
- [ ] **Step 5: Focused tests pass.**

## Task 3: Typed Investigation API + contract regeneration

**Files:**

- Create: `services/api/src/flow_api/api/routes/investigations.py`
- Create: `services/api/src/flow_api/api/schemas/investigation.py`
- Modify: `services/api/src/flow_api/main.py` (register router)
- Modify: `packages/contracts/openapi.json`, `packages/contracts/src/schema.d.ts` (generated)
- Test: `services/api/tests/api/test_investigations.py`

- [ ] **Step 1: Write failing API tests** — `GET /api/v1/investigations/{finding_id}` (with and without binding query), `POST .../evidence/{evidence_id}/decision`, `PUT .../conclusion`, `POST .../transition`; typed error envelopes with stable codes; unknown finding → 404; identity mismatch → 409 `investigation_identity_mismatch`; blocked approval → 409 with `evidence_pending`/`conclusion_incomplete`.
- [ ] **Step 2: Implement routes + schemas**, register router, regenerate OpenAPI and TypeScript contracts (`bash scripts/generate_contracts.sh`), `make contracts-check` passes.
- [ ] **Step 3: Focused API tests + full unit scope pass.**

## Task 4: Evidence-first Investigation workbench (web)

**Files:**

- Modify: `apps/web/app/investigations/[findingId]/page.tsx` (workbench replaces receipt shell)
- Create: `apps/web/components/investigation/*` (header + review flow strip, driver table, bridge panel, formula panel, checks row, source-records table, conclusion editor, evidence inspector, review history)
- Create: `apps/web/components/investigation/investigation.css`
- Modify: `apps/web/lib/api/client.ts` (typed `getInvestigation`, `decideEvidence`, `saveConclusion`, `transitionFinding`)
- Test: `apps/web/tests/investigation-*.test.tsx`

- [ ] **Step 1: Component tests** — identity receipt strip, driver table ordering, blocked-approval notice rendering, conclusion editor sections, evidence inspector actions, accessibility landmarks, single `h1`.
- [ ] **Step 2: Implement workbench** using the v2 prototype layout (left process rail, main context + evidence flow, right inspector), full loading/error/not-found/identity-mismatch states, Chinese labels consistent with dashboard.
- [ ] **Step 3: `pnpm -r lint && pnpm -r typecheck && pnpm --filter @flow/web test` pass.**

## Task 5: Phase 7 exit gate and verification

**Files:**

- Create: `scripts/test_investigation_e2e.sh`
- Modify: `Makefile` (`test-investigation-e2e`), `.github/workflows/ci.yml` (`investigation-e2e` job)
- Test: `apps/web/e2e/investigation.spec.ts`
- Create: `docs/implementation/phase-7-verification.md`
- Modify: knowledge base state files + manifests

- [ ] **Step 1: Write Playwright e2e** — open finding from dashboard handoff, review evidence (reject one → approval blocked with visible reason, re-verify), edit conclusion, submit, approve; verify audit history grows append-only; identity mismatch state renders.
- [ ] **Step 2: Wire `make test-investigation-e2e` + CI job.**
- [ ] **Step 3: Full local regression** (unit, integration, invariants, dashboard, investigation, lint/typecheck/contracts).
- [ ] **Step 4: Verification doc + knowledge base update, commit, push, green CI.**

Exit command: `make test-investigation-e2e`

Expected: a Finance BP can reproduce, review, approve, and reject the core profit and cash findings with complete audit history; pending/rejected critical evidence provably prevents approval and report eligibility.
