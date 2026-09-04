# FLOW V1 Phase 5 Analysis & Findings Implementation Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：Phase 5 功能切片已有实现与[阶段验收](../../implementation/phase-5-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Apply `superpowers:test-driven-development` to every behavior change and `superpowers:verification-before-completion` before declaring the phase complete. Keep the seven root-level user files untracked and out of every commit.

**Goal:** Publish one immutable Analysis Run from a Phase 4 Metric Snapshot and its version-bound canonical detail, with five reconciled analysis results, deterministic evidence-complete Finding candidates, transparent ranking, and explicit degradation.

**Architecture:** A registry invokes typed playbooks for revenue V/P/M, fulfillment-cost R/V/E, gross profit, operating profit, and AR/cash impact. Pure `Decimal` functions return frozen typed results. A version-scoped repository supplies canonical rows and snapshot values. A transactional service validates invariants, qualifies and ranks Findings, persists all children, and atomically publishes an idempotent Analysis Run. Later consumers read the published run instead of recomputing.

**Tech Stack:** Python 3.13, Pydantic 2, PyYAML, SQLAlchemy 2, PostgreSQL 18, Alembic, pytest, Ruff, strict mypy, Make, JSON, YAML.

**Approved design:** `docs/superpowers/specs/2026-09-01-flow-v1-phase-5-analysis-design.md`

## Global constraints

- Read only a published `MetricSnapshot`, its bound published `ImportVersion`, and version-scoped canonical repositories.
- Reject floats at all public calculation and policy boundaries; use `Decimal` throughout.
- Money driver sums must reconcile to the source impact within `0.01 CNY`.
- Never generate a Finding from a degraded, unreconciled, or evidence-incomplete result.
- Finding wording may describe mathematical drivers but must not claim unverified business causality.
- Preserve published runs and children as append-only.
- Do not stage or modify the seven pre-existing root-level untracked user files.

## Task 1: Define analysis policy and typed contracts

**Files:**

- Create: `services/api/src/flow_api/analysis/__init__.py`
- Create: `services/api/src/flow_api/analysis/models.py`
- Create: `services/api/src/flow_api/analysis/policy.py`
- Create: `services/api/config/analysis/flow-logistics-v1.yaml`
- Test: `services/api/tests/analysis/test_models.py`
- Test: `services/api/tests/analysis/test_policy.py`

- [ ] **Step 1: Write failing contract tests**

Test frozen models for source windows, driver contributions, complete/degraded results, evidence requirements, score components, and Finding drafts. Assert invalid status, duplicate driver codes, negative tolerance, missing degradation detail, and float inputs fail validation.

- [ ] **Step 2: Run tests and observe the missing-package failure**

Run: `cd services/api && uv run pytest tests/analysis/test_models.py tests/analysis/test_policy.py -q`

Expected: FAIL because `flow_api.analysis` does not exist.

- [ ] **Step 3: Implement the smallest typed contracts**

Use frozen Pydantic models, literal enums, explicit decimal validators, and canonical JSON serialization helpers. Define stable result statuses and degradation codes from the approved design.

- [ ] **Step 4: Write the versioned policy YAML and loader**

Set policy ID `flow.analysis.logistics.v1`, engine version `flow-analysis/1`, tolerance `0.01`, ranking weights `0.40/0.20/0.20/0.20`, materiality thresholds, persistence window 3, management relevance by Finding type, and required evidence sets. Hash canonicalized YAML content.

- [ ] **Step 5: Run focused tests**

Run: `cd services/api && uv run pytest tests/analysis/test_models.py tests/analysis/test_policy.py -q`

Expected: PASS.

## Task 2: Implement pure revenue and fulfillment decompositions

**Files:**

- Create: `services/api/src/flow_api/analysis/decimal_math.py`
- Create: `services/api/src/flow_api/analysis/bridges.py`
- Test: `services/api/tests/analysis/test_decimal_math.py`
- Test: `services/api/tests/analysis/test_revenue_vpm.py`
- Test: `services/api/tests/analysis/test_fulfillment_rve.py`

- [ ] **Step 1: Write exact known-answer tests**

Use small hand-computable product cells to assert:

```text
VPM volume + mix + price = current revenue - comparison revenue
RVE volume + efficiency + rate = current cost - comparison cost
```

Also test negative impacts, zero total impact, driver order, contribution-ratio omission for zero impact, and scale-4 persistence values.

- [ ] **Step 2: Write failing edge-case tests**

Assert float rejection, zero denominator, unmatched/new/lost mix cells, duplicated cell identity, source-total mismatch, and reconciliation outside tolerance return typed degradation or calculation errors as specified.

- [ ] **Step 3: Run tests and observe failures**

Run: `cd services/api && uv run pytest tests/analysis/test_decimal_math.py tests/analysis/test_revenue_vpm.py tests/analysis/test_fulfillment_rve.py -q`

Expected: FAIL because bridge functions are absent.

- [ ] **Step 4: Implement V/P/M and R/V/E pure functions**

Implement only the approved formulas. Quantize at output boundaries, retain exact values in traces, use stable driver codes/order, and run a shared invariant checker.

- [ ] **Step 5: Run focused tests**

Run the command from Step 3.

Expected: PASS with exact `Decimal` equality for known answers.

## Task 3: Implement profit and AR/cash playbooks

**Files:**

- Create: `services/api/src/flow_api/analysis/playbooks.py`
- Test: `services/api/tests/analysis/test_profit_bridges.py`
- Test: `services/api/tests/analysis/test_ar_cash.py`
- Test: `services/api/tests/analysis/test_playbook_registry.py`

- [ ] **Step 1: Write failing profit-bridge tests**

Prove gross-profit contribution signs, reuse of revenue V/P/M drivers, separation of warehousing/transportation/other-direct-cost changes, and operating-expense extension. Assert both bridges match their headline impacts and degrade when V/P/M is degraded.

- [ ] **Step 2: Write failing AR/cash tests**

Assert closing AR change, aging-bucket contributions, DSO comparison values, collection rate/shortfall, customer concentration context, and `estimated_working_capital_cash_impact = -AR increase`. Prove bucket drivers sum to the impact and customer concentration is not double-counted.

- [ ] **Step 3: Write registry tests**

Assert the five stable playbook codes and versions are registered exactly once, dependencies execute in topological order, and unknown or cyclic dependencies fail at registry construction.

- [ ] **Step 4: Run tests and observe failures**

Run: `cd services/api && uv run pytest tests/analysis/test_profit_bridges.py tests/analysis/test_ar_cash.py tests/analysis/test_playbook_registry.py -q`

Expected: FAIL because playbooks and registry are absent.

- [ ] **Step 5: Implement typed playbooks and registry**

Keep playbooks pure over typed input bundles. Encode dependency of profit bridges on `revenue_vpm`; expose required fields and safe descriptive values for degradation output.

- [ ] **Step 6: Run focused tests**

Run the command from Step 4.

Expected: PASS.

## Task 4: Implement deterministic Finding qualification and ranking

**Files:**

- Create: `services/api/src/flow_api/analysis/findings.py`
- Test: `services/api/tests/analysis/test_finding_qualification.py`
- Test: `services/api/tests/analysis/test_ranking.py`

- [ ] **Step 1: Write failing hard-gate tests**

Assert no Finding for degraded result, failed invariant, missing evidence, impact below threshold, unsupported abnormal direction, mismatched run identity, or duplicate fingerprint. Assert each suppression reason remains in the qualification trace.

- [ ] **Step 2: Write failing wording and evidence tests**

Assert generated titles and fact statements are deterministic and contain only verified amounts/comparison bases. Prohibit causal vocabulary from templates. Require metric value, calculation, source-record set, lineage, and invariant evidence.

- [ ] **Step 3: Write failing ranking tests**

Assert exact normalized and weighted scores, point-in-time persistence policy, three-period persistence, evidence score 100 for qualified Findings, deterministic tie order, and raw normalization parameters in each component trace.

- [ ] **Step 4: Run tests and observe failures**

Run: `cd services/api && uv run pytest tests/analysis/test_finding_qualification.py tests/analysis/test_ranking.py -q`

Expected: FAIL because qualification and ranking are absent.

- [ ] **Step 5: Implement qualification, templates, fingerprints, and scoring**

Separate hard qualification from ranking. Derive score only after all gates pass. Use canonical JSON and decimal strings for fingerprints and tie-breaks.

- [ ] **Step 6: Run focused tests**

Run the command from Step 4.

Expected: PASS.

## Task 5: Extend the analytics database schema

**Files:**

- Modify: `services/api/src/flow_api/infrastructure/models/analytics.py`
- Modify: `services/api/src/flow_api/infrastructure/models/__init__.py`
- Create: `services/api/migrations/versions/0007_add_analysis_runs.py`
- Modify: `services/api/tests/integration/test_analytics_schema.py`
- Create: `services/api/tests/integration/test_analysis_run_schema.py`

- [ ] **Step 1: Write failing schema tests**

Cover `analysis_run`, `analysis_result`, `analysis_driver`, and `finding_score_component`; Finding and Evidence extensions; unique identities; status checks; driver ordering; score ranges; snapshot/import consistency; and evidence object types.

- [ ] **Step 2: Write failing immutability tests**

Assert update/delete of a published run and its result/driver/score/evidence children raises append-only errors. Preserve existing review/publication tests.

- [ ] **Step 3: Run schema tests and observe failures**

Run: `cd services/api && uv run pytest tests/integration/test_analytics_schema.py tests/integration/test_analysis_run_schema.py -q`

Expected: FAIL because tables and columns do not exist.

- [ ] **Step 4: Implement ORM changes and migration**

Use explicit constraints and foreign keys. Backward-compatible new Finding columns are nullable where old schema fixtures require it; Phase 5 service always populates them. Extend Evidence checks and structured verification fields.

- [ ] **Step 5: Verify migrations on empty and upgraded schemas**

Run:

```bash
cd services/api
uv run alembic upgrade head
uv run python ../../scripts/check_migrations.py
uv run pytest tests/integration/test_analytics_schema.py tests/integration/test_analysis_run_schema.py -q
```

Expected: PASS.

## Task 6: Add snapshot-bound repositories and atomic Analysis Run service

**Files:**

- Create: `services/api/src/flow_api/analysis/repositories.py`
- Create: `services/api/src/flow_api/analysis/evidence.py`
- Create: `services/api/src/flow_api/analysis/service.py`
- Create: `services/api/tests/integration/analysis_run_support.py`
- Create: `services/api/tests/integration/test_analysis_repository.py`
- Create: `services/api/tests/integration/test_analysis_service.py`
- Create: `services/api/tests/integration/test_analysis_atomicity.py`

- [ ] **Step 1: Write failing repository-boundary tests**

Assert only the snapshot-bound published import is loaded; reject missing, unpublished, failed, or mismatched snapshots. Verify stable ordering, row counts, and deterministic source-record digests.

- [ ] **Step 2: Write failing service tests**

Assert the service loads policy and registry, executes dependencies, persists complete and degraded results, creates Findings only after evidence verification, ranks deterministically, and publishes the run.

- [ ] **Step 3: Write failing idempotence and atomicity tests**

Call the same identity twice and assert one run. Inject failures after results, after Findings, and before publication; assert no published partial run or orphan children remain.

- [ ] **Step 4: Run tests and observe failures**

Run: `cd services/api && uv run pytest tests/integration/test_analysis_repository.py tests/integration/test_analysis_service.py tests/integration/test_analysis_atomicity.py -q`

Expected: FAIL because repositories and service are absent.

- [ ] **Step 5: Implement version-scoped repositories, evidence verifier, and service**

Reuse Phase 4 source-row contracts where suitable without exposing workbook artifacts. Use nested transactions and explicit flush/verification before changing run status to `published`.

- [ ] **Step 6: Run focused tests**

Run the command from Step 4.

Expected: PASS.

## Task 7: Freeze Phase 5 known answers and degradation fixtures

**Files:**

- Create: `fixtures/expected/analysis_results_v1.json`
- Create: `services/api/src/flow_api/fixtures/analysis_known_answers.py`
- Modify: `services/api/tests/fixtures/test_known_answers.py`
- Create: `services/api/tests/analysis/test_analysis_oracle.py`
- Create: `services/api/tests/integration/test_analysis_invariants.py`

- [ ] **Step 1: Independently calculate the fixture oracle**

Derive V/P/M, R/V/E, profit, operating-profit, AR/cash, and ranking values from committed canonical JSONL—not from production analysis functions. Store decimal strings, driver order, bridge differences, Finding types, score components, and expected rank order.

- [ ] **Step 2: Write failing oracle tests**

Assert the oracle's internal sums and story predicates independently. Then compare production Analysis Run output field-by-field with the frozen oracle.

- [ ] **Step 3: Add controlled degradation variants**

Use repository/input doubles that remove shipment count, AR aging bucket, or comparison mix cells. Assert the affected result's exact degradation code, preserved safe descriptive facts, and zero Findings from that result.

- [ ] **Step 4: Run invariant tests**

Run: `cd services/api && uv run pytest tests/analysis/test_analysis_oracle.py tests/integration/test_analysis_invariants.py -q`

Expected: PASS with every complete bridge difference at or below `0.01`.

## Task 8: Add the acceptance gate and CI job

**Files:**

- Create: `scripts/test_analysis_invariants.sh`
- Create: `scripts/summarize_analysis.py`
- Modify: `Makefile`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the acceptance shell gate**

The script must migrate an empty database, run analysis unit/integration/oracle suites, rerun the Phase 4 snapshot and intake E2E regressions, run Ruff/mypy/migration checks, and print a compact deterministic analysis summary.

- [ ] **Step 2: Register `make test-analysis-invariants`**

Add the target to `.PHONY`. Add an isolated `analysis-invariants` CI job using the same dependency setup pattern as Phase 4.

- [ ] **Step 3: Run the phase gate**

Run: `make test-analysis-invariants`

Expected: PASS and summary shows five results, all complete fixture bridges reconciled, top profit/cash Findings, and degradation coverage.

## Task 9: Verify regressions and document completion

**Files:**

- Create: `docs/implementation/phase-5-verification.md`
- Modify: `docs/knowledge-base/00_start_here/PROJECT_STATE.md`
- Modify: `docs/knowledge-base/00_start_here/AGENT_START_HERE.md` if the next-phase entry point changes
- Modify: `docs/knowledge-base/README.md` only if a new indexed knowledge-base artifact is added
- Regenerate: `docs/knowledge-base/99_manifest/inventory.tsv`
- Regenerate: `docs/knowledge-base/99_manifest/sha256sums.txt`

- [ ] **Step 1: Run complete verification**

Run:

```bash
make test-analysis-invariants
make test-metrics-known-answers
make test-intake-e2e
make contracts-check
make test-api
make lint
make typecheck
git diff --check
```

Expected: all commands PASS.

- [ ] **Step 2: Record evidence honestly**

Document commands, dates, counts, key invariant values, degradation scenarios, and any remaining limitations. Update project state to mark Phase 5 complete only after the evidence exists.

- [ ] **Step 3: Regenerate knowledge-base manifests**

Use the repository's existing manifest procedure. Confirm original conversation, research, and image archives are byte-identical and that only indexes/checksums changed.

- [ ] **Step 4: Commit scoped changes and push `main`**

Review `git status`, stage only Phase 5 files, create descriptive commits at coherent task boundaries, and push `origin main`. Never force-push.

- [ ] **Step 5: Verify GitHub CI**

Inspect the pushed workflow run and wait until all jobs finish. If a job fails, diagnose from logs, fix with TDD, rerun local gates, commit, push, and recheck. Phase 5 is not complete until the latest `main` run is green.
