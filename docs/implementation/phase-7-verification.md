# Phase 7 Verification — Evidence-first Investigation & Review

Date: 2026-09-02
Scope: `docs/superpowers/plans/2026-09-02-flow-v1-phase-7-investigation.md`
Design: `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §10; visual reference `investigation-evidence-v2.html`.

## Exit gate

`make test-investigation-e2e` — Playwright driven, against a freshly seeded
demo batch (`seed_dashboard_demo.py --fresh-batch`), covering:

1. Dashboard → Investigation handoff preserves the D036 identity receipt
   (finding, batch, snapshot, run) on the workbench itself.
2. Driver table, impact bridge, formula/engine-version context, reconciliation
   and quality checks, and top source records with immutable file/sheet/row
   lineage all render from the published run.
3. A Finance BP records the four-section conclusion; saving a candidate
   finding submits it for review (candidate → in_review).
4. Rejecting any evidence blocks approval with a typed, human-readable
   reason (`evidence_rejected`); re-verifying unblocks; approval flips the
   finding to `approved`, the eligibility panel shows report eligibility,
   and the audit history records every decision append-only.

Result: 4/4 Playwright tests passed locally (11.6s), including the two
dashboard handoff/axe tests that share the workbench.

## Evidence

| Check | Command | Result |
|---|---|---|
| Domain state machines | `uv run pytest tests/investigation -q` | 15 passed |
| Typed API flow | `uv run pytest tests/api/test_investigations.py -q` | 1 passed |
| Unit scope (DB-free) | `pytest tests/domain tests/api tests/test_health.py --ignore=…intake --ignore=…dashboard --ignore=…investigations -q` | 13 passed |
| Integration scope | `pytest tests/integration tests/investigation tests/api/test_dashboard.py tests/api/test_investigations.py -q` | passed (see CI `integration` job) |
| Static python | `ruff check src tests && mypy src` | clean |
| Contracts | `bash scripts/generate_contracts.sh && make contracts-check` | in sync |
| Web unit/component | `pnpm --filter @flow/web test` | 12 passed |
| Web static | `pnpm -r lint && pnpm -r typecheck` | clean |
| Investigation E2E | `make test-investigation-e2e` | 4 passed |
| Migration round trip | GitHub Actions `migrations` job (check_migrations on 0008) | passed |

## Domain decisions encoded

- Finding transitions: `candidate→in_review (submitted)`, `in_review→approved`
  (gated), `in_review→rejected`, `in_review→candidate (returned)`,
  `approved→in_review (returned)`. `rejected` is terminal in V1.
- Approval eligibility: every Evidence row `verified` AND a Conclusion with
  four non-empty sections. Pending or rejected evidence blocks approval.
- Evidence decisions: `pending→verified|rejected`, `rejected→verified`,
  `verified→rejected`; every decision appends a `ReviewEvent` with
  `evidence_verified`/`evidence_rejected` (migration `0008_investigation_review`).
- Record-level tables display canonical values and lineage references only;
  contribution amounts remain at driver level from the immutable run. No
  Investigation endpoint recomputes analysis money.
- Demo re-seeding (`--fresh-batch`) publishes a brand-new batch so gates are
  repeatable without mutating published history.

## Carry-forward

- Phase 8 (AI Copilot) consumes the same identity-bound context packet and
  may only reference objects the workbench already exposes.
- Phase 9 (Unified Publishing) reads `finding.status == "approved"` as the
  report-eligibility boundary, backed by `eligibility_blockers == ()`.
