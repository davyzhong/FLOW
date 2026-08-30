# FLOW V1 Phase 3 Intake, Mapping & Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Apply `superpowers:test-driven-development` to every behavior change and `superpowers:verification-before-completion` before the phase is declared complete.

**Goal:** Accept both a valid `flow.excel.v1` workbook and a deliberately non-standard external workbook, preserve the original bytes, identify and map their data into the frozen canonical contract, produce auditable transformations and quality results, and atomically publish an immutable import version only when every blocking gate passes.

**Architecture:** Phase 3 is an orchestration layer around the Phase 2 contract. Immutable source bytes enter through content-addressed object storage. A detector describes workbook structure without changing it; a deterministic matcher proposes sheet and field mappings before an optional AI adapter is consulted. Versioned pure transformations produce typed candidate rows and field-level lineage. A quality engine returns typed issues and reconciliation results. PostgreSQL stores every mapping, import attempt, acknowledgement and source-to-canonical relationship. Publication changes the batch pointer and canonical rows in one transaction; corrections always create a new version.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, openpyxl, SQLAlchemy 2, PostgreSQL 18, MinIO/S3, pytest, Ruff, mypy, Make, JSON, XLSX.

## Frozen Inputs and Non-negotiable Boundaries

- Contract version remains exactly `flow.excel.v1`; Phase 3 does not silently widen or reinterpret Phase 2 fields.
- `fixtures/workbooks/flow_standard_v1.xlsx` and `fixtures/expected/known_answers.json` are the positive reference oracle.
- A committed non-standard workbook contains the same business records with renamed/reordered sheets, shifted headers, aliases, alternate date/number formatting and ignorable notes; it must map to the same canonical semantics.
- Original file bytes and observed source values are immutable. Cleaning creates derived values and events.
- Workbook recognition, mapping, AI suggestions and user confirmations never write canonical facts directly.
- Deterministic exact/alias/type rules run before the AI adapter. The AI adapter returns proposals and rationale only; it cannot publish.
- Blocking issues cannot be acknowledged. Warnings require actor and reason.
- Exactly one import version per batch may be published. A corrected import creates a new version and leaves the former version queryable.
- All financial and quantity values remain `Decimal`; float is rejected at boundaries.
- Dashboard, metrics, Investigation and report generation remain outside this phase.

## Phase Exit Command

```bash
make test-intake-e2e
```

The command must prove that the standard and non-standard workbooks produce the same semantic snapshot and known totals; blocking errors prevent publication; acknowledged warnings retain actor/reason; corrected imports create new versions; source bytes, raw values and earlier versions remain unchanged.

---

### Task 1: Freeze the Non-standard Workbook Acceptance Fixture

**Files:**
- Create: `scripts/generate_phase_3_fixtures.py`
- Create: `fixtures/workbooks/external_logistics_nonstandard_v1.xlsx`
- Create: `fixtures/intake/nonstandard_manifest.json`
- Create: `services/api/tests/intake/test_nonstandard_fixture.py`
- Modify: `services/api/tests/data_contract/test_committed_artifacts.py`

**Interfaces:**
- Consumes: Phase 2 standard workbook and canonical package.
- Produces: a deterministic external-workbook fixture plus a manifest of expected sheet roles, header rows, data regions and intentional aliases.

- [ ] Write failing tests that require the committed fixture and verify it has no FLOW field-ID row.
- [ ] Generate a workbook with renamed/reordered sheets, two pre-header note rows, Chinese aliases, dates represented in two safe formats, comma-formatted numbers and irrelevant note columns.
- [ ] Preserve the same logical records and null meanings as the standard workbook; do not introduce lossy transformations.
- [ ] Generate twice and require byte-identical artifacts and manifest.
- [ ] Run fixture and artifact tests, then commit and push.

### Task 2: Make Immutable Source Storage Collision-safe

**Files:**
- Modify: `services/api/src/flow_api/infrastructure/object_store.py`
- Create: `services/api/src/flow_api/intake/source_storage.py`
- Create: `services/api/tests/intake/test_source_storage.py`
- Modify: `services/api/tests/integration/test_object_store.py`

**Interfaces:**
- Produces: `StoredSource`, `SourceStorage.store(content, filename)`, `SourceStorage.read(sha256)`.

- [ ] Write failing tests for identical-byte reuse, stored-byte re-read, metadata validation and a simulated existing-key hash/size mismatch.
- [ ] Require SHA-256 content addressing under `raw/<prefix>/<sha256>` and validate an existing object's length and checksum before reuse.
- [ ] Ensure a filename changes source-file metadata only, never object identity.
- [ ] Reject empty files, unsupported workbook types and accidental overwrite with typed errors.
- [ ] Run unit and MinIO integration tests, then commit and push.

### Task 3: Detect Workbook Structure Without Mutating It

**Files:**
- Create: `services/api/src/flow_api/intake/__init__.py`
- Create: `services/api/src/flow_api/intake/models.py`
- Create: `services/api/src/flow_api/intake/detector.py`
- Create: `services/api/tests/intake/test_detector.py`

**Interfaces:**
- Produces: `WorkbookProfile`, `SheetProfile`, `ColumnProfile`, `CellRegion`, `profile_workbook(path_or_bytes)`.

- [ ] Write failing tests for both reference workbooks and malformed/empty sheets.
- [ ] Detect sheet names, visibility, used region, likely header rows, first/last data rows, raw headers, inferred primitive types and representative values.
- [ ] Detect stable FLOW field IDs when present, but do not require them.
- [ ] Infer row grain candidates from uniqueness and contract keys; return evidence, never a bare guess.
- [ ] Cap sampled rows/cells and reject zip bombs, encrypted workbooks, formulas in required input cells and unsupported file types.
- [ ] Prove profiling does not change bytes, then run static checks and commit.

### Task 4: Version Deterministic Mapping Proposals and AI Fallback

**Files:**
- Create: `config/intake/flow_v1_aliases.yaml`
- Create: `services/api/src/flow_api/intake/mapping.py`
- Create: `services/api/src/flow_api/intake/ai_mapping.py`
- Create: `services/api/tests/intake/test_mapping.py`
- Create: `services/api/tests/intake/test_ai_mapping_adapter.py`

**Interfaces:**
- Produces: `MappingProposal`, `SheetMapping`, `FieldMapping`, `MappingConfidence`, `MappingRationale`, `propose_mapping(profile, contract)`, and `AIMappingAdapter` protocol.

- [ ] Write failing tests for exact field ID, exact display name, normalized alias, compatible-type and ambiguous matches.
- [ ] Score deterministic evidence in a documented order and reject one-to-many or many-to-one required-field mappings unless explicitly resolved.
- [ ] Return confidence, matched evidence, unresolved requirements and confirmations for every proposal.
- [ ] Invoke the AI adapter only for unresolved/ambiguous candidates; validate its response against contract IDs and allowed source columns.
- [ ] Ensure AI output cannot change types, formulas, grains, quality gates or publication state.
- [ ] Persist a canonical JSON mapping specification whose hash is stable; run tests and commit.

### Task 5: Build Pure, Versioned Transformations and Field Lineage

**Files:**
- Create: `config/intake/flow_v1_transforms.yaml`
- Create: `services/api/src/flow_api/intake/transforms.py`
- Create: `services/api/src/flow_api/intake/extractor.py`
- Create: `services/api/tests/intake/test_transforms.py`
- Create: `services/api/tests/intake/test_extractor.py`

**Interfaces:**
- Produces: `TransformRule`, `TransformResult`, `LineageValue`, `apply_transform(rule, raw_value)`, `extract_candidate_package(source, profile, mapping, contract)`.

- [ ] Write failing table-driven tests for trimming, null normalization, Unicode normalization, dates, decimal separators, percentages, codes and safe enum aliases.
- [ ] Require every rule to have stable ID and version; return raw value, transformed value, rule, reason and status.
- [ ] Never coerce ambiguous values silently. Failed or lossy conversions become quality candidates.
- [ ] Extract a typed `CanonicalPackage` candidate and exact source sheet/row/column lineage for each mapped value.
- [ ] Prove standard and non-standard workbooks reach equal candidate semantic snapshots before persistence.
- [ ] Run tests, Ruff and mypy, then commit.

### Task 6: Implement Layered Quality and Reconciliation Gates

**Files:**
- Create: `services/api/src/flow_api/intake/quality.py`
- Create: `services/api/src/flow_api/intake/reconciliation.py`
- Create: `services/api/tests/intake/test_quality.py`
- Create: `services/api/tests/intake/test_reconciliation.py`

**Interfaces:**
- Produces: `QualityReport`, `Issue`, `IssueLocation`, `ReconciliationCheck`, `evaluate_quality(candidate, contract)`, `reconcile(candidate, tolerance)`.

- [ ] Write failing tests for missing required roles/fields, duplicate grains, broken required relations and invalid types as blocking issues.
- [ ] Add warning rules for unexpected negative/zero values, revenue with zero orders, suspected unit scale, optional-dimension misses and low-confidence mappings.
- [ ] Run operating-to-financial revenue and direct-cost reconciliations with explicit CNY tolerance and exact Decimal calculations.
- [ ] Include issue code, severity, source location, canonical target, evidence and repair suggestion.
- [ ] Make report ordering deterministic and prove all expected bad-fixture issues are located accurately.
- [ ] Run tests and static checks, then commit.

### Task 7: Complete the Audit and Acknowledgement Schema

**Files:**
- Create: `services/api/migrations/versions/0004_intake_audit_and_publication.py`
- Modify: `services/api/src/flow_api/infrastructure/models/intake.py`
- Modify: `services/api/src/flow_api/infrastructure/models/__init__.py`
- Create: `services/api/tests/integration/test_intake_audit_schema.py`

**Interfaces:**
- Adds: mapping confidence/rationale/hash, import lifecycle status, per-value transformation rule identity, warning acknowledgement actor/reason/time, and published-version identity needed for an immutable history.

- [ ] Write failing migration/model tests before changing the schema.
- [ ] Add the smallest schema extension required for complete auditability; do not duplicate `SourceRecord.raw_value` and `transformed_value` unnecessarily.
- [ ] Enforce that only warning issues can be acknowledged and actor/reason are non-empty.
- [ ] Enforce import status transitions and one published import per batch at the database/service boundary.
- [ ] Verify `upgrade head → downgrade 0003 → upgrade head` and full migration round trip.
- [ ] Run integration/static tests, then commit and push.

### Task 8: Orchestrate Versioned Intake and Atomic Publication

**Files:**
- Create: `services/api/src/flow_api/intake/service.py`
- Create: `services/api/src/flow_api/intake/repositories.py`
- Modify: `services/api/src/flow_api/data_contract/persistence.py`
- Create: `services/api/tests/integration/test_intake_service.py`
- Create: `services/api/tests/integration/test_intake_atomicity.py`

**Interfaces:**
- Produces: `IntakeService.create_batch`, `attach_source`, `propose_mapping`, `confirm_mapping`, `validate_import`, `acknowledge_warning`, `publish_import`, `create_correction`.

- [ ] Write failing lifecycle tests for draft → validating → blocked/ready → published.
- [ ] Persist every source, mapping and import sequence; retrying an idempotent step must not duplicate records.
- [ ] Store candidate canonical rows under their import version without exposing them as published state.
- [ ] Refuse publication for any blocking issue, failed reconciliation or unacknowledged warning.
- [ ] Publish canonical rows, lineage and batch state in one transaction; inject a mid-publication failure and prove rollback leaves no partial state.
- [ ] Correct a failed or published import by creating a new version; prove source bytes and previous versions remain byte/row identical.
- [ ] Run integration tests and commit.

### Task 9: Expose a Typed Intake API

**Files:**
- Create: `services/api/src/flow_api/api/routes/intake.py`
- Create: `services/api/src/flow_api/api/schemas/intake.py`
- Modify: `services/api/src/flow_api/api/router.py`
- Modify: `services/api/openapi.json`
- Modify: `packages/contracts/src/generated/api.ts`
- Create: `services/api/tests/api/test_intake.py`

**Interfaces:**
- Adds endpoints for batch creation, workbook upload, profile/mapping retrieval, mapping confirmation, validation, warning acknowledgement, publication and version history.

- [ ] Write failing API contract tests for happy path, typed validation errors, invalid transitions and publication blockers.
- [ ] Stream uploads with a configured size limit; never log workbook bytes or cell contents.
- [ ] Return stable IDs, lifecycle state, mapping confidence/rationale, issue summaries and next allowed actions.
- [ ] Make actor identity explicit in acknowledgement and mapping confirmation requests until authentication is introduced.
- [ ] Regenerate OpenAPI and TypeScript contracts and require no generation drift.
- [ ] Run API, contract and static tests, then commit.

### Task 10: Build the End-to-end Acceptance Gate

**Files:**
- Create: `scripts/test_intake_e2e.sh`
- Create: `scripts/summarize_intake.py`
- Modify: `Makefile`
- Modify: `.github/workflows/ci.yml`
- Create: `services/api/tests/integration/test_intake_e2e.py`
- Create: `docs/intake/flow-v1-intake.md`

**Interfaces:**
- Adds: `make test-intake-e2e` and CI job `intake-e2e`.

- [ ] Write the failing acceptance test first.
- [ ] Ingest the standard and non-standard workbook through the same public service boundary and compare both with Phase 2 semantic snapshots and known answers.
- [ ] Exercise blocking error, warning acknowledgement, reconciliation failure, atomic rollback and corrected-version paths.
- [ ] Assert object hashes, raw values, mapping versions, transform rules, issue locations, canonical facts and field lineage.
- [ ] Run Ruff, mypy, API contract drift, migrations and Phase 1/2 regression gates from the script.
- [ ] Document operator behavior, error codes, audit trail and recovery rules.
- [ ] Add the CI job, run the gate in a clean worktree, record evidence in `docs/implementation/phase-3-verification.md`, update project state and knowledge-base manifests.
- [ ] Commit, push and require all GitHub Actions jobs to pass before marking Phase 3 complete.

## Expected Phase 3 Deliverable

At completion, FLOW will have a trustworthy ingestion boundary rather than a workbook parser alone. A Finance BP can upload either the FLOW template or a realistic external workbook, inspect why each source field maps to the standard contract, correct uncertain decisions, see precise quality/reconciliation blockers, acknowledge only permissible warnings, and publish an immutable canonical batch whose numbers and lineage are provably identical to the Phase 2 oracle.
