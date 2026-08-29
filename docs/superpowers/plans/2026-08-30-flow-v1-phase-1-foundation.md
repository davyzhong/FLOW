# FLOW V1 Phase 1 Foundation & Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a reproducible FLOW development stack, durable object identities, initial PostgreSQL schema, versioned API contract, generated web client, and CI gates on which every later V1 phase can safely build.

**Architecture:** Use a modular-monolith repository with Next.js for the web shell and a FastAPI package shared by the API and Celery worker. Keep domain types independent from frameworks, use SQLAlchemy/Alembic only in infrastructure, and expose all browser integrations through a committed `/api/v1` OpenAPI contract.

**Tech Stack:** Node.js 24 LTS, pnpm 10, Next.js 16.3.3, React 19.2, TypeScript 5, Python 3.13, uv, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, psycopg 3, PostgreSQL 18, Celery, Redis 8, MinIO, pytest, Ruff, mypy, Vitest, Playwright, Docker Compose.

## Global Constraints

- PostgreSQL is the only canonical database; object bytes live in S3-compatible storage.
- Persisted money uses `NUMERIC(20, 4)` and Python `Decimal`.
- Persisted ratios and quantities use `NUMERIC(20, 6)` unless a more restrictive field is specified.
- UUIDv7 application IDs are generated before persistence; stable business/metric IDs are strings.
- Every mutable workflow table carries `created_at`, `created_by`, and a monotonic version or append-only event trail.
- Raw object keys are content-addressed and never overwritten.
- API routes are namespaced under `/api/v1`.
- The initial workspace model is single-workspace/single-Finance-BP; complex authorization is outside V1.
- API domain and application tests must run without the web application.
- The web app imports generated contract types and does not redefine API payloads.
- No user-owned untracked root files are staged or changed.

---

### Task 1: Bootstrap the Reproducible Workspace

**Files:**
- Create: `.tool-versions`
- Create: `.env.example`
- Create: `Makefile`
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `apps/web/package.json`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/app/globals.css`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/tests/home.test.tsx`
- Create: `services/api/pyproject.toml`
- Create: `services/api/src/flow_api/__init__.py`
- Create: `services/api/src/flow_api/main.py`
- Create: `services/api/tests/test_health.py`
- Create: `infra/compose.yaml`
- Create: `infra/api.Dockerfile`
- Create: `infra/web.Dockerfile`
- Create: `scripts/wait_for_services.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: none.
- Produces: `flow_api.main:create_app() -> FastAPI`, `GET /api/v1/health`, root commands `make bootstrap`, `make dev`, and `make test`.

- [ ] **Step 1: Write failing API and web smoke tests**

```python
# services/api/tests/test_health.py
from fastapi.testclient import TestClient
from flow_api.main import create_app


def test_health_contract() -> None:
    response = TestClient(create_app()).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "flow-api"}
```

```tsx
// apps/web/tests/home.test.tsx
import { render, screen } from "@testing-library/react";
import HomePage from "../app/page";

it("identifies the Finance BP workspace", () => {
  render(<HomePage />);
  expect(screen.getByRole("heading", { name: "FLOW" })).toBeVisible();
  expect(screen.getByText("Finance BP 经营分析工作台")).toBeVisible();
});
```

- [ ] **Step 2: Run tests to verify the workspace is absent**

Run: `test ! -f services/api/pyproject.toml && test ! -f apps/web/package.json`

Expected: PASS, proving this task starts before application scaffolding exists.

- [ ] **Step 3: Create the minimal API application**

```python
# services/api/src/flow_api/main.py
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="FLOW API", version="0.1.0")

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "flow-api"}

    return app


app = create_app()
```

- [ ] **Step 4: Create the minimal web shell**

```tsx
// apps/web/app/page.tsx
export default function HomePage() {
  return (
    <main>
      <h1>FLOW</h1>
      <p>Finance BP 经营分析工作台</p>
    </main>
  );
}
```

- [ ] **Step 5: Pin runtimes and dependency families**

Use `.tool-versions` with `nodejs 24` and `python 3.13`. Configure pnpm workspaces and a uv-managed `services/api/pyproject.toml` with dependency families from the plan header plus `uuid6>=2025.0.1,<2027`; commit generated `pnpm-lock.yaml` and `services/api/uv.lock`.

Run: `corepack pnpm install && cd services/api && uv sync --all-groups`

Expected: both lock files are created with no unresolved packages.

- [ ] **Step 6: Add PostgreSQL, Redis, and MinIO development services**

```yaml
# infra/compose.yaml service contract excerpt
services:
  postgres:
    image: postgres:18
    environment:
      POSTGRES_DB: flow
      POSTGRES_USER: flow
      POSTGRES_PASSWORD: flow_dev_only
  redis:
    image: redis:8-alpine
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: flow
      MINIO_ROOT_PASSWORD: flow_dev_only
```

- [ ] **Step 7: Add root developer commands**

`Makefile` must expose `bootstrap`, `infra-up`, `infra-down`, `stack-up`, `stack-down`, `dev-api`, `dev-web`, `test-api`, `test-web`, `test`, `lint`, and `typecheck`; each target delegates to pnpm, uv, or Docker Compose without duplicating package configuration.

- [ ] **Step 8: Run smoke checks**

Run: `make test && make lint && make typecheck`

Expected: API and web smoke tests pass; Ruff, mypy, ESLint, and TypeScript report no errors.

- [ ] **Step 9: Commit**

```bash
git add .tool-versions .env.example .gitignore Makefile package.json pnpm-workspace.yaml pnpm-lock.yaml apps/web services/api infra scripts
git commit -m "build: bootstrap FLOW application workspace"
git push origin main
```

### Task 2: Define Domain IDs, Lifecycle Enums, and Money Types

**Files:**
- Create: `services/api/src/flow_api/domain/__init__.py`
- Create: `services/api/src/flow_api/domain/ids.py`
- Create: `services/api/src/flow_api/domain/enums.py`
- Create: `services/api/src/flow_api/domain/values.py`
- Create: `services/api/tests/domain/test_ids.py`
- Create: `services/api/tests/domain/test_values.py`

**Interfaces:**
- Consumes: Python package from Task 1.
- Produces: `new_uuid7() -> UUID`, lifecycle enums, `Money`, `ObjectRef`, and `JobReceipt` Pydantic models used by all later tasks.

- [ ] **Step 1: Write failing value-object tests**

```python
from decimal import Decimal
import pytest
from flow_api.domain.ids import new_uuid7
from pydantic import ValidationError
from flow_api.domain.values import Money


def test_uuid7_values_are_time_ordered() -> None:
    first = new_uuid7()
    second = new_uuid7()
    assert first.version == 7
    assert second.int > first.int


def test_money_rejects_float_and_quantizes_to_four_places() -> None:
    assert Money(amount=Decimal("12.34567")).amount == Decimal("12.3457")
    with pytest.raises(ValidationError):
        Money(amount=12.34)  # type: ignore[arg-type]
```

- [ ] **Step 2: Verify tests fail**

Run: `cd services/api && uv run pytest tests/domain/test_ids.py tests/domain/test_values.py -q`

Expected: FAIL because `flow_api.domain.ids` and `flow_api.domain.values` do not exist.

- [ ] **Step 3: Implement stable domain primitives**

```python
class BatchStatus(StrEnum):
    DRAFT = "draft"
    VALIDATING = "validating"
    BLOCKED = "blocked"
    READY = "ready"
    PUBLISHED = "published"


class EvidenceStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class FindingStatus(StrEnum):
    CANDIDATE = "candidate"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
```

`Money` must use a Pydantic before-validator to reject Python floats, require a three-letter uppercase currency, and quantize with `ROUND_HALF_UP` to four decimal places.

- [ ] **Step 4: Run domain tests and static checks**

Run: `cd services/api && uv run pytest tests/domain -q && uv run mypy src`

Expected: all domain tests pass and mypy reports success.

- [ ] **Step 5: Commit**

```bash
git add services/api/src/flow_api/domain services/api/tests/domain
git commit -m "feat: define FLOW domain primitives"
git push origin main
```

### Task 3: Add Configuration, Database Session, and Migration Harness

**Files:**
- Create: `services/api/src/flow_api/settings.py`
- Create: `services/api/src/flow_api/infrastructure/db.py`
- Create: `services/api/src/flow_api/infrastructure/models/base.py`
- Create: `services/api/alembic.ini`
- Create: `services/api/migrations/env.py`
- Create: `services/api/migrations/script.py.mako`
- Create: `services/api/tests/integration/test_database.py`
- Create: `scripts/check_migrations.py`

**Interfaces:**
- Consumes: environment variables in `.env.example`.
- Produces: `Settings`, `session_factory`, `transaction()` context manager, SQLAlchemy `Base`, and repeatable Alembic commands.

- [ ] **Step 1: Write the database transaction test**

```python
from sqlalchemy import text
from flow_api.infrastructure.db import transaction


def test_postgres_transaction_is_available() -> None:
    with transaction() as session:
        assert session.scalar(text("select 1")) == 1
```

- [ ] **Step 2: Verify the test fails**

Run: `make infra-up && cd services/api && uv run pytest tests/integration/test_database.py -q`

Expected: FAIL because the database module has not been created.

- [ ] **Step 3: Implement typed configuration and sessions**

`Settings` must require `DATABASE_URL`, `REDIS_URL`, `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY`, and `S3_SECRET_KEY`; secrets must use `SecretStr`. `transaction()` must commit on success, roll back on exception, and always close the session.

- [ ] **Step 4: Configure Alembic and migration validation**

`scripts/check_migrations.py` must create a temporary schema, run `alembic upgrade head`, run `alembic downgrade base`, and run `alembic upgrade head` again.

- [ ] **Step 5: Run integration and migration harness tests**

Run: `cd services/api && uv run pytest tests/integration/test_database.py -q && uv run python ../../scripts/check_migrations.py`

Expected: transaction test passes and both migration upgrade cycles exit 0.

- [ ] **Step 6: Commit**

```bash
git add .env.example services/api/src/flow_api/settings.py services/api/src/flow_api/infrastructure services/api/alembic.ini services/api/migrations services/api/tests/integration scripts/check_migrations.py
git commit -m "build: add database and migration harness"
git push origin main
```

### Task 4: Model Batch, Source File, Import Version, Quality, and Lineage

**Files:**
- Create: `services/api/src/flow_api/infrastructure/models/intake.py`
- Create: `services/api/migrations/versions/0001_intake_foundation.py`
- Create: `services/api/tests/integration/test_intake_schema.py`

**Interfaces:**
- Consumes: `Base`, UUID/domain enums, PostgreSQL session.
- Produces: tables `analysis_batch`, `stored_object`, `source_file`, `import_version`, `mapping_version`, `transformation_event`, `quality_issue`, `reconciliation_result`, and `source_record`.

- [ ] **Step 1: Write failing schema invariants**

```python
def test_repeated_uploads_share_bytes_but_keep_distinct_upload_records(session):
    blob = stored_object(sha256="a" * 64, object_key=f"raw/aa/{'a' * 64}")
    first = source_file(stored_object=blob, original_filename="first.xlsx")
    second = source_file(stored_object=blob, original_filename="second.xlsx")
    session.add_all([first, second])
    session.commit()
    assert first.id != second.id
    assert first.stored_object_id == second.stored_object_id
```

Also assert that one Batch can have multiple Import Versions, only one published version is active, quality issues use `blocking|warning`, and each transformed field can point to Source File + sheet + row + column.

- [ ] **Step 2: Verify schema tests fail**

Run: `cd services/api && uv run pytest tests/integration/test_intake_schema.py -q`

Expected: FAIL because intake tables do not exist.

- [ ] **Step 3: Implement intake models and constraints**

Use database check/unique constraints for one Stored Object per SHA-256/object key, import-version sequence, issue severity, non-negative row numbers, allowed batch states, and one reconciliation result per `(import_version_id, reconciliation_code)`. Each upload creates a distinct Source File referencing the reusable Stored Object.

- [ ] **Step 4: Create and inspect migration**

Run: `cd services/api && uv run alembic upgrade head && uv run python ../../scripts/check_migrations.py`

Expected: migration reaches `0001_intake_foundation` from an empty database and survives downgrade/upgrade.

- [ ] **Step 5: Run tests**

Run: `cd services/api && uv run pytest tests/integration/test_intake_schema.py -q`

Expected: all source immutability, version, quality, and lineage constraints pass.

- [ ] **Step 6: Commit**

```bash
git add services/api/src/flow_api/infrastructure/models/intake.py services/api/migrations/versions/0001_intake_foundation.py services/api/tests/integration/test_intake_schema.py
git commit -m "feat: add intake and lineage schema"
git push origin main
```

### Task 5: Model Canonical Dimensions and Facts

**Files:**
- Create: `services/api/src/flow_api/infrastructure/models/canonical.py`
- Create: `services/api/migrations/versions/0002_canonical_data.py`
- Create: `services/api/tests/integration/test_canonical_schema.py`

**Interfaces:**
- Consumes: published Import Version and Source Record identity.
- Produces: dimension tables from specification §6.4 and fact tables `fact_operating_actual`, `fact_financial_actual`, `fact_budget`, and `fact_ar_collection`.

- [ ] **Step 1: Write failing grain and precision tests**

```python
def test_operating_fact_grain_and_decimal_precision(session, canonical_seed):
    session.add(operating_fact(canonical_seed, revenue=Decimal("100.1234")))
    session.commit()
    session.add(operating_fact(canonical_seed, revenue=Decimal("200.0000")))
    with pytest.raises(IntegrityError):
        session.commit()
```

Test unique business keys, required dimension foreign keys, nullable optional dimensions, month-key validity, and exact Decimal round trip for each fact family.

- [ ] **Step 2: Verify schema tests fail**

Run: `cd services/api && uv run pytest tests/integration/test_canonical_schema.py -q`

Expected: FAIL because canonical tables do not exist.

- [ ] **Step 3: Implement dimensions and facts**

Every fact row must include `import_version_id` and `source_record_id`. Business keys must include the exact grain dimensions from the product specification; AR supports invoice or aging-bucket identity without forcing both.

- [ ] **Step 4: Run migration and schema tests**

Run: `cd services/api && uv run alembic upgrade head && uv run pytest tests/integration/test_canonical_schema.py -q && uv run python ../../scripts/check_migrations.py`

Expected: all precision, relationship, and grain tests pass; migration round trip exits 0.

- [ ] **Step 5: Commit**

```bash
git add services/api/src/flow_api/infrastructure/models/canonical.py services/api/migrations/versions/0002_canonical_data.py services/api/tests/integration/test_canonical_schema.py
git commit -m "feat: add canonical finance data schema"
git push origin main
```

### Task 6: Model Metrics, Findings, Evidence, Reviews, and Publications

**Files:**
- Create: `services/api/src/flow_api/infrastructure/models/analytics.py`
- Create: `services/api/src/flow_api/infrastructure/models/publishing.py`
- Create: `services/api/migrations/versions/0003_analytics_and_publishing.py`
- Create: `services/api/tests/integration/test_analytics_schema.py`

**Interfaces:**
- Consumes: published Batch and canonical dimensions.
- Produces: versioned identities for `metric_definition`, `metric_snapshot`, `metric_value`, `driver_contribution`, `finding`, `evidence`, `review_event`, `conclusion`, `report_snapshot`, `report_snapshot_item`, and `publication_attempt`.

- [ ] **Step 1: Write failing version and reference tests**

```python
def test_report_snapshot_references_one_metric_snapshot(session, analytics_seed):
    report = report_snapshot(metric_snapshot_id=analytics_seed.metric_snapshot_id)
    report.items = [snapshot_item(object_type="finding", object_id=str(analytics_seed.finding_id))]
    session.add(report)
    session.commit()
    assert report.metric_snapshot_id == analytics_seed.metric_snapshot_id
```

Also assert immutable snapshot version keys, Decimal metric values, allowed evidence/finding states, append-only review events, unique driver order, typed object references, and multiple Publication Attempts per Report Snapshot.

- [ ] **Step 2: Verify schema tests fail**

Run: `cd services/api && uv run pytest tests/integration/test_analytics_schema.py -q`

Expected: FAIL because analytics tables do not exist.

- [ ] **Step 3: Implement analytics and publishing schema**

Use JSONB only for renderer-neutral presentation configuration and cited-object lists; financial values, statuses, versions, dimensions, and lifecycle relationships remain typed columns/tables.

- [ ] **Step 4: Run full schema validation**

Run: `cd services/api && uv run alembic upgrade head && uv run pytest tests/integration -q && uv run python ../../scripts/check_migrations.py`

Expected: all integration tests pass and schema upgrades from empty twice.

- [ ] **Step 5: Commit**

```bash
git add services/api/src/flow_api/infrastructure/models/analytics.py services/api/src/flow_api/infrastructure/models/publishing.py services/api/migrations/versions/0003_analytics_and_publishing.py services/api/tests/integration/test_analytics_schema.py
git commit -m "feat: add analytics and publication schema"
git push origin main
```

### Task 7: Add Workspace API and Generated TypeScript Contract

**Files:**
- Create: `services/api/src/flow_api/api/router.py`
- Create: `services/api/src/flow_api/api/routes/health.py`
- Create: `services/api/src/flow_api/api/routes/workspace.py`
- Create: `services/api/src/flow_api/api/schemas/workspace.py`
- Modify: `services/api/src/flow_api/main.py`
- Create: `services/api/tests/api/test_workspace.py`
- Create: `packages/contracts/package.json`
- Create: `packages/contracts/openapi.json`
- Create: `packages/contracts/src/schema.d.ts`
- Create: `scripts/generate_contracts.sh`
- Create: `scripts/check_contracts.sh`
- Create: `apps/web/lib/api/client.ts`
- Create: `apps/web/tests/api-client.test.ts`

**Interfaces:**
- Consumes: domain value objects and application settings.
- Produces: `GET /api/v1/workspace`, committed `openapi.json`, generated `paths` TypeScript type, and `flowApi.getWorkspace()`.

- [ ] **Step 1: Write failing API contract test**

```python
def test_workspace_contract(client):
    response = client.get("/api/v1/workspace")
    assert response.status_code == 200
    assert response.json() == {
        "workspace_id": "flow-v1",
        "name": "FLOW",
        "primary_role": "finance_bp",
        "industry": "logistics_supply_chain",
        "timezone": "Asia/Shanghai",
        "currency": "CNY",
    }
```

- [ ] **Step 2: Verify the route is absent**

Run: `cd services/api && uv run pytest tests/api/test_workspace.py -q`

Expected: FAIL with HTTP 404.

- [ ] **Step 3: Implement the versioned route and schema**

The route returns `WorkspaceResponse`; route modules contain no SQL or business logic. `create_app()` includes one `/api/v1` router.

- [ ] **Step 4: Generate and commit the client contract**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd services/api
uv run python -c 'import json; from flow_api.main import create_app; print(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2))' > ../../packages/contracts/openapi.json
cd ../..
pnpm --filter @flow/contracts generate
```

`openapi-typescript` generates `packages/contracts/src/schema.d.ts`. `check_contracts.sh` regenerates into a temporary directory and fails on diff.

- [ ] **Step 5: Add typed web adapter and test**

```ts
export const flowApi = {
  async getWorkspace(): Promise<WorkspaceResponse> {
    return request<WorkspaceResponse>("/api/v1/workspace");
  },
};
```

Mock `fetch` in Vitest and assert the method calls the versioned route and returns the generated response type.

- [ ] **Step 6: Run contract checks**

Run: `make contracts && make test-api && make test-web && make typecheck`

Expected: contract regeneration is clean and all API/web tests pass.

- [ ] **Step 7: Commit**

```bash
git add services/api/src/flow_api/api services/api/src/flow_api/main.py services/api/tests/api packages/contracts scripts/generate_contracts.sh scripts/check_contracts.sh apps/web/lib/api apps/web/tests/api-client.test.ts package.json pnpm-lock.yaml
git commit -m "feat: publish versioned FLOW API contract"
git push origin main
```

### Task 8: Add Worker, Object Store, and Idempotent Job Contract

**Files:**
- Create: `services/api/src/flow_api/infrastructure/object_store.py`
- Create: `services/api/src/flow_api/infrastructure/jobs.py`
- Create: `services/api/src/flow_api/worker.py`
- Create: `services/api/src/flow_api/application/jobs.py`
- Create: `services/api/tests/integration/test_object_store.py`
- Create: `services/api/tests/integration/test_jobs.py`
- Modify: `infra/compose.yaml`

**Interfaces:**
- Consumes: S3/Redis settings and `JobReceipt`.
- Produces: `ObjectStore.put_immutable(content, filename) -> StoredObject`, `enqueue_once(job_type, resource_id, version) -> JobReceipt`, and Celery app `flow_api.worker:celery_app`.

- [ ] **Step 1: Write failing immutability and idempotency tests**

```python
def test_identical_bytes_reuse_content_addressed_object(object_store):
    first = object_store.put_immutable(b"FLOW", "source.xlsx")
    second = object_store.put_immutable(b"FLOW", "renamed.xlsx")
    assert first.sha256 == second.sha256
    assert first.object_key == second.object_key


def test_same_job_key_is_enqueued_once(job_service):
    first = job_service.enqueue_once("import", "batch-1", 1)
    second = job_service.enqueue_once("import", "batch-1", 1)
    assert first.job_id == second.job_id
```

- [ ] **Step 2: Verify tests fail**

Run: `cd services/api && uv run pytest tests/integration/test_object_store.py tests/integration/test_jobs.py -q`

Expected: FAIL because object-store and job services do not exist.

- [ ] **Step 3: Implement content-addressed storage and job keys**

Store objects under `raw/{sha256[0:2]}/{sha256}` and use Redis key `flow:job:{job_type}:{resource_id}:{version}` with atomic `SET NX`. An existing job returns the existing receipt instead of enqueueing a duplicate.

- [ ] **Step 4: Add worker service to Compose**

The worker runs `celery -A flow_api.worker:celery_app worker --loglevel=INFO --concurrency=2` against the same image and environment as the API.

- [ ] **Step 5: Run infrastructure tests**

Run: `make infra-up && cd services/api && uv run pytest tests/integration/test_object_store.py tests/integration/test_jobs.py -q`

Expected: immutable object and idempotent enqueue tests pass against MinIO and Redis.

- [ ] **Step 6: Commit**

```bash
git add services/api/src/flow_api/infrastructure services/api/src/flow_api/application/jobs.py services/api/src/flow_api/worker.py services/api/tests/integration infra/compose.yaml
git commit -m "feat: add immutable storage and job infrastructure"
git push origin main
```

### Task 9: Add CI and Foundation Acceptance Gate

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `scripts/accept_phase_1.sh`
- Create: `docs/architecture/flow-v1-runtime.md`
- Create: `docs/architecture/flow-v1-domain-objects.md`
- Modify: `README.md`
- Modify: `Makefile`

**Interfaces:**
- Consumes: every Task 1–8 command and contract.
- Produces: `make phase-1-acceptance` and CI jobs `static-python`, `static-web`, `unit`, `integration`, `contracts`, `migrations`, and `smoke`.

- [ ] **Step 1: Write the acceptance script before wiring CI**

```bash
#!/usr/bin/env bash
set -euo pipefail
make stack-up
make lint
make typecheck
make test
make contracts
cd services/api
uv run python ../../scripts/check_migrations.py
uv run pytest tests/integration -q
cd ../..
curl --fail http://localhost:8000/api/v1/health
```

- [ ] **Step 2: Run the acceptance script and capture the first failure**

Run: `bash scripts/accept_phase_1.sh`

Expected: FAIL at the first missing Make target or service wiring; do not weaken a check to make the script pass.

- [ ] **Step 3: Wire Make targets and CI jobs**

CI must use service containers for PostgreSQL, Redis, and MinIO, cache pnpm/uv downloads, regenerate contracts, and fail if generated files differ. It must never require an AI API key.

- [ ] **Step 4: Document architecture and commands**

`README.md` must contain prerequisites, bootstrap, environment, service URLs, test commands, and the rule that raw files cannot be read by downstream modules. Architecture docs must list each runtime process, database aggregate, ID type, and lifecycle owner.

- [ ] **Step 5: Run the complete Phase 1 gate**

Run: `make phase-1-acceptance`

Expected: all static, unit, integration, contract, migration, worker/object-store, and HTTP smoke checks pass.

- [ ] **Step 6: Inspect scope and commit**

```bash
git status --short
git diff --check
git add .github/workflows/ci.yml scripts/accept_phase_1.sh docs/architecture README.md Makefile
git commit -m "ci: enforce FLOW foundation acceptance gate"
git push origin main
```

### Task 10: Phase 1 Review and Handoff

**Files:**
- Create: `docs/implementation/phase-1-verification.md`
- Modify: `docs/knowledge-base/00_start_here/PROJECT_STATE.md`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`

**Interfaces:**
- Consumes: verified Phase 1 repository and migration head `0003_analytics_and_publishing`.
- Produces: auditable verification record and stable inputs for the Phase 2 data-contract plan.

- [ ] **Step 1: Run clean-checkout verification**

Run the following in a temporary Git worktree created from `HEAD`:

```bash
make bootstrap
make phase-1-acceptance
```

Expected: both commands pass without files from the developer's original working tree.

- [ ] **Step 2: Record exact evidence**

Write `docs/implementation/phase-1-verification.md` with commit hash, lock-file hashes, migration heads, command outputs summarized as pass/fail, service image versions, and any accepted non-blocking limitations. Do not include secrets or `.env` values.

- [ ] **Step 3: Update project state and knowledge manifest**

Mark Phase 1 complete and Phase 2 next. Regenerate the knowledge-base inventory and SHA-256 manifest according to `AGENTS.md`.

- [ ] **Step 4: Final verification and commit**

Run: `git diff --check && make phase-1-acceptance`

Expected: no whitespace errors and the complete gate passes.

```bash
git add docs/implementation/phase-1-verification.md docs/knowledge-base/00_start_here/PROJECT_STATE.md docs/knowledge-base/99_manifest
git commit -m "docs: record FLOW foundation verification"
git push origin main
```

## Phase 1 Completion Criteria

- A fresh checkout can provision PostgreSQL, Redis, MinIO, API, worker, and web processes.
- Database migration `0003_analytics_and_publishing` upgrades from empty and round-trips through downgrade/upgrade.
- Domain IDs, status enums, money types, object references, and job receipts are tested and stable.
- Source, canonical, metric, investigation, and publication identities exist with database constraints.
- `/api/v1/health` and `/api/v1/workspace` match the committed OpenAPI contract.
- The generated TypeScript client compiles and is used by the web shell.
- Object storage is content-addressed; duplicate job requests are idempotent.
- Phase 1 acceptance passes in a clean worktree and in GitHub Actions.
- Every task commit is pushed to `origin`; unrelated user files remain untracked and untouched.
