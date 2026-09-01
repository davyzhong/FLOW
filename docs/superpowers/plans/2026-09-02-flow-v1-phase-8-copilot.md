# FLOW V1 Phase 8 AI Copilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` task-by-task. Apply `superpowers:test-driven-development` to every behavior change and `superpowers:verification-before-completion` before declaring the phase complete. Keep the seven root-level user files untracked and out of every commit.

**Goal:** Ship a bounded, evidence-first AI Copilot that can explain mappings, answer investigation questions, and draft report outlines — using only allow-listed context packets, always separating facts/judgments/hypotheses/questions, always citing referenced object IDs, and never inventing numbers or touching unapproved findings.

**Architecture:** A provider-neutral `CopilotProvider` protocol with a deterministic offline `ScriptedProvider` (and an opt-in live adapter stub) powers three use-case services. Each request builds a `ContextPacket` by serializing only identity-bound domain objects (batch, snapshot, finding, evidence, metric definition/formula, driver contributions) through the same Investigation repository used by Phase 7. Responses are validated against a strict schema: every number must match a context packet number, every citation must resolve to a known object ID, unapproved findings cannot be referenced by report-outline drafts, and insufficient data degrades explicitly. Every call persists a `CopilotInteraction` audit row (prompt template version, provider/model, request references, response, validation outcome, actor).

**Tech Stack:** Python 3.13, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 18, FastAPI, pytest, Ruff, strict mypy, Next.js 16, React 19, TypeScript 5.

**Approved design:** `docs/superpowers/specs/2026-08-29-flow-v1-design.md` §12 (AI 能力与边界).

## Global constraints

- AI never computes or invents financial numbers; output numbers must byte-match context packet values.
- AI never modifies data: the copilot layer has no write access to domain tables.
- Facts, judgments, hypotheses, and questions are separate typed output sections; a statement may not be presented as fact unless it cites verified evidence or a metric/analysis object.
- Uncited numbers or unknown object IDs fail validation; the interaction is stored with `rejected` outcome and a typed reason.
- Report outlines may only reference findings with `status == approved`.
- Context packets are allow-listed: no raw files, no canonical row dumps beyond aggregates already exposed by Phase 7, no other batches.
- Live providers are opt-in via explicit settings; tests and CI run the deterministic fake offline.

## Task 1: Provider protocol, scripted provider, interaction audit model

**Files:**

- Create: `services/api/src/flow_api/copilot/__init__.py`
- Create: `services/api/src/flow_api/copilot/providers.py`
- Create: `services/api/src/flow_api/copilot/models.py`
- Create: `services/api/migrations/versions/0009_copilot_interactions.py`
- Test: `services/api/tests/copilot/test_providers.py`

- [ ] **Step 1: Failing tests** — protocol surface (`complete(request) -> response`), scripted provider returns queued deterministic responses, frozen request/response models, prompt template version stamping.
- [ ] **Step 2: Run, observe missing module.**
- [ ] **Step 3: Implement protocol + ScriptedProvider + typed models;** migration `0009_copilot_interactions` (audit table: template version, provider, model, request reference ids, response payload, validation outcome, actor, created_at).
- [ ] **Step 4: Focused tests pass.**

## Task 2: Context packets and output validator

**Files:**

- Create: `services/api/src/flow_api/copilot/context.py`
- Create: `services/api/src/flow_api/copilot/validator.py`
- Test: `services/api/tests/copilot/test_context.py`
- Test: `services/api/tests/copilot/test_validator.py`

- [ ] **Step 1: Failing context tests** — packet contains exactly identity-bound objects (batch provenance, snapshot identity/definition/formula, finding, drivers, evidence, engine/policy versions); rejects cross-batch ids; stable canonical serialization.
- [ ] **Step 2: Failing validator tests** — accept clean structured output; reject uncited numbers; reject unknown citations; reject facts citing unverified evidence; reject report outlines referencing unapproved findings; require degradation marker when data missing.
- [ ] **Step 3: Implement packet builder + validator** with `ValidationOutcome` (`accepted` | `rejected` + reasons).
- [ ] **Step 4: Focused tests pass.**

## Task 3: Three use-case services + audit persistence

**Files:**

- Create: `services/api/src/flow_api/copilot/service.py`
- Test: `services/api/tests/copilot/test_service.py`

- [ ] **Step 1: Failing service tests** — `explain_mapping`, `answer_investigation_question`, `draft_report_outline`: scripted responses flow through validation; interactions persist with template version + references + outcome; rejected outputs raise typed `CopilotValidationError` while still persisting.
- [ ] **Step 2: Implement services** wiring providers, packets, validator, audit repository.
- [ ] **Step 3: Focused tests pass.**

## Task 4: Typed Copilot API + contract regeneration

**Files:**

- Create: `services/api/src/flow_api/api/routes/copilot.py`
- Create: `services/api/src/flow_api/api/schemas/copilot.py`
- Modify: `services/api/src/flow_api/api/router.py`
- Modify: `packages/contracts/openapi.json`, `packages/contracts/src/schema.d.ts`
- Test: `services/api/tests/api/test_copilot.py`

- [ ] **Step 1: Failing API tests** — `POST /api/v1/investigations/{finding_id}/copilot/ask` (identity-bound), `POST /api/v1/imports/{import_version_id}/copilot/explain-mapping`, `POST /api/v1/copilot/report-outline` (batch-bound); typed validation-failure envelope (`copilot_validation_failed` + reasons); audit id returned.
- [ ] **Step 2: Implement routes;** regenerate contracts; `make contracts-check` passes.
- [ ] **Step 3: Full unit scope passes.**

## Task 5: Fixed evaluations gate

**Files:**

- Create: `services/api/config/copilot/flow-v1-evals.yaml`
- Create: `services/api/src/flow_api/copilot/evals.py`
- Create: `scripts/test_copilot_evals.sh`
- Modify: `Makefile` (`test-copilot-e2e` → `test-copilot-evals`), `.github/workflows/ci.yml` (`copilot-evals` job)
- Test: `services/api/tests/copilot/test_evals.py`

- [ ] **Step 1: Freeze eval cases** — citation completeness, numeric consistency vs packet, insufficient-data degradation, unapproved-findings prohibition, mapping-explanation sanity; each case pairs a context fixture with a required verdict.
- [ ] **Step 2: Evals runner** executes all cases against ScriptedProvider offline and reports pass/fail summaries.
- [ ] **Step 3: `make test-copilot-evals` green locally and in CI.**

## Task 6: Investigation workbench AI panel (frontend)

**Files:**

- Create: `apps/web/components/investigation/copilot-panel.tsx`
- Modify: `apps/web/components/investigation/investigation-app.tsx` (inspector tab)
- Modify: `apps/web/lib/api/client.ts`
- Test: `apps/web/tests/investigation-copilot.test.tsx`

- [ ] **Step 1: Component tests** — question box, structured answer sections render with citation badges, rejected-output notice, disabled state when no context.
- [ ] **Step 2: Implement panel;** lint/typecheck/vitest pass.

Exit command: `make test-copilot-evals`

Expected: deterministic fake tests pass offline; live-provider tests are opt-in and never gate normal CI; every interaction is auditable end-to-end.
