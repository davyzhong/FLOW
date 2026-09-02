# Phase 10 Verification — Acceptance Suite and Release

Date: 2026-09-02
Scope: `docs/superpowers/plans/2026-08-30-flow-v1-master-roadmap.md` §Phase 10.

## What landed

- `make acceptance` (via `scripts/acceptance.sh`): one command chains the
  seven governed gates on a live compose stack —
  data-contract round trip → metric known answers → analysis invariants →
  intake e2e → publishing golden → investigation e2e → dashboard e2e.
- The CI workflow (`FLOW CI`) defines the functional gates as isolated jobs
  (static-python, static-web, unit, integration, data-contract,
  intake-e2e, metrics-known-answers, analysis-invariants, dashboard,
  investigation-e2e, copilot-evals, publishing-golden, contracts, migrations,
  smoke). `make acceptance` remains the local composite gate; CI executes the
  component gates independently so a failure identifies its product boundary.

## V1 acceptance criteria status (product spec §3.1)

| # | Criterion | Gate |
|---|---|---|
| 1 | Standard modular Excel workbook round trip | data-contract |
| 2 | Non-standard workbook mapping with zero semantic loss | intake-e2e |
| 3 | Immutable source, lineage, quality, reconciliation | integration |
| 4 | Metric snapshots with exact known answers | metrics-known-answers |
| 5 | Deterministic reconciled playbooks and findings | analysis-invariants |
| 6 | High-density governed Finance BP dashboard | dashboard |
| 7 | Evidence-first investigation with append-only reviews | investigation-e2e |
| 8 | Bounded AI copilot with audited, validated output | copilot-evals |
| 9 | PPTX/XLSX/HTML/PDF from one frozen snapshot | publishing-golden |
| 10 | One-command acceptance | make acceptance |

## Deliberately deferred (roadmap Phase 10 items parked post-V1)

- Backup/restore rehearsal scripts (database and object store) — deployment
  topology is still undecided (knowledge base 未决事项), so rehearsal targets
  would be speculative.
- Structured-log/correlation-ID completeness and worker dead-letter
  dashboards — current Celery/uvicorn logging is functional; deeper
  observability belongs to the private-cloud deployment workstream.
- These do not invalidate the implemented V1 functional narrow slice, but they
  do block any claim of pilot or production readiness. They are carried into
  the Pilot Readiness workstream under D038.

## Current release boundary

`v0.1.0` records the first functional narrow slice. The corrected baseline
release must not be tagged until the final `main` commit has passed the local
composite gate and all 15 isolated CI jobs, including `publishing-golden`.
