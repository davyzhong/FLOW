# FLOW V1 Phase 4 Metric Snapshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Apply `superpowers:test-driven-development` to every behavior change and `superpowers:verification-before-completion` before the phase is declared complete. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn one published canonical import into an immutable, versioned Metric Snapshot whose month, YTD, budget, prior-year and trailing-12 values exactly match frozen Decimal oracles and can be reused unchanged by dashboards, Investigation and reports.

**Architecture:** Phase 4 reads only the published `ImportVersion` and its version-scoped canonical facts. A versioned YAML catalog defines metric identity, source, formula, dependencies, allowed dimensions, aggregation and time behavior. Pure Decimal calculations produce typed values before a transactional snapshot service persists definitions, dependency edges, values and calculation traces. Flow metrics sum over time; balance metrics select the closing period; ratios are recalculated from same-grain dependencies and are never summed or averaged from child ratios.

**Tech Stack:** Python 3.13, Pydantic 2, PyYAML, SQLAlchemy 2, PostgreSQL 18, Alembic, pytest, Ruff, mypy, Make, JSON, YAML.

## Global Constraints

- Phase 4 consumes only canonical facts belonging to the batch's currently published `ImportVersion`; no workbook, source record or unpublished candidate may be read by the metric engine.
- All numeric inputs, intermediate values and persisted outputs are `Decimal`. Floats are rejected at every public boundary.
- Definition set ID is `flow.metrics.logistics.v1`; every definition has a stable code and positive integer version.
- Money and quantity values persist at scale 4; ratios and days calculate at scale 6 and persist in the existing `Numeric(24, 4)` column only after the documented output rounding policy is applied. Exact scale-6 oracle comparisons occur before persistence and in calculation traces.
- A Metric Snapshot is identified by `batch_id + import_version_id + as_of_period_id + definition_set_hash + engine_version`; a retry with the same identity is idempotent.
- Snapshot creation is refused unless the import version is published, is the batch's active published version, has no blocking quality issues, has no unacknowledged warnings and all required reconciliations passed.
- Flow metrics are additive across periods; balance metrics are semi-additive and use the last available period; ratio metrics are recalculated from numerator and denominator at the same grain.
- Budget variance is emitted only at grains supported by both actual and budget source data. The engine must not invent budget allocation for customer or region.
- Required Phase 4 metrics are: `orders`, `fulfilled_units`, `revenue`, `revenue_per_order`, `direct_cost`, `cost_per_order`, `gross_profit`, `gross_margin`, `fulfillment_cost_rate`, `operating_profit`, `ar_balance`, `collection_rate`, `dso`, `operating_cash_flow`, and `cash_conversion`.
- DSO V1 formula is `closing_ar_balance / trailing_12_revenue * 365`; a zero trailing-12 revenue denominator is a typed calculation blocker.
- Snapshot definitions, values and dependency records are append-only. A corrected import creates a new snapshot version and never mutates a prior snapshot.
- Dashboard rendering, Finding generation, driver decomposition, AI prose and report export remain outside Phase 4.

## Phase Exit Command

```bash
make test-metrics-known-answers
```

Expected: all metric definition, formula, dimension, time-window, persistence, immutability and known-answer tests pass; the standard and external workbooks' published canonical versions produce equal snapshot fingerprints; exact Decimal comparisons match the committed metric oracle.

---

### Task 1: Freeze the Versioned Metric Catalog and Independent Oracle

**Files:**
- Create: `config/metrics/flow_v1_metrics.yaml`
- Create: `fixtures/expected/metric_snapshots_v1.json`
- Create: `services/api/src/flow_api/metrics/__init__.py`
- Create: `services/api/src/flow_api/metrics/models.py`
- Create: `services/api/src/flow_api/metrics/catalog.py`
- Create: `services/api/tests/metrics/test_catalog.py`
- Create: `services/api/tests/metrics/test_metric_oracle.py`
- Modify: `services/api/tests/data_contract/test_committed_artifacts.py`

**Interfaces:**

```python
MetricAggregation = Literal["sum", "closing_balance", "ratio"]
MetricTimeBehavior = Literal["flow", "balance"]
MetricUnit = Literal["order", "unit", "CNY", "CNY/order", "ratio", "day"]

class MetricSpec(BaseModel):
    metric_code: str
    version: int
    name: str
    business_definition: str
    formula: str
    dependencies: tuple[str, ...]
    aggregation: MetricAggregation
    time_behavior: MetricTimeBehavior
    unit: MetricUnit
    output_scale: int
    allowed_dimension_sets: tuple[tuple[str, ...], ...]

class MetricCatalog(BaseModel):
    definition_set_id: str
    engine_version: str
    metrics: tuple[MetricSpec, ...]

def load_metric_catalog(path: str | Path) -> MetricCatalog: ...
```

- [x] Write a failing test requiring exactly the 15 metric codes, unique `(metric_code, version)`, dependency references to existing codes, an acyclic graph and `definition_set_id == "flow.metrics.logistics.v1"`.
- [x] Run `cd services/api && uv run pytest tests/metrics/test_catalog.py -q`; expect failure because the catalog loader does not exist.
- [x] Implement strict YAML loading with `extra="forbid"`, explicit units, output scales, allowed dimension sets and stable topological ordering.
- [x] Freeze the exact source formulas: operating facts for volume/revenue/direct cost; financial accounts for operating profit/cash; AR facts for balance/collections; derived formulas only through declared metric dependencies.
- [x] Commit an independently reviewed JSON oracle containing exact month, YTD, budget, prior-year, variance, trailing-12 and final-month balance values needed by later tests. The oracle must contain strings, never JSON floats.
- [x] Add deterministic serialization and SHA-256 tests for both YAML and oracle, run the task tests, Ruff and mypy, then commit and push.

### Task 2: Implement Decimal Formula and Dependency Evaluation

**Files:**
- Create: `services/api/src/flow_api/metrics/decimal_math.py`
- Create: `services/api/src/flow_api/metrics/formulas.py`
- Create: `services/api/tests/metrics/test_decimal_math.py`
- Create: `services/api/tests/metrics/test_formulas.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class CalculatedDecimal:
    exact_value: Decimal
    persisted_value: Decimal
    output_scale: int
    rounding: str

class MetricCalculationError(ValueError):
    metric_code: str
    code: Literal["zero_denominator", "missing_dependency", "float_rejected"]

def decimal_sum(values: Iterable[Decimal], *, scale: int = 4) -> Decimal: ...
def calculate_ratio(
    metric_code: str,
    numerator: Decimal,
    denominator: Decimal,
    *,
    multiplier: Decimal = Decimal("1"),
    output_scale: int = 6,
) -> CalculatedDecimal: ...
def topological_metric_order(catalog: MetricCatalog) -> tuple[str, ...]: ...
```

- [x] Write table-driven failing tests for exact sums, negative values, repeating ratios, scale-6 ratios, scale-4 persistence rounding, zero denominators, missing dependencies and float rejection.
- [x] Run the two test files and confirm failures are caused by missing production functions.
- [x] Implement `ROUND_HALF_UP` calculations using explicit quantums; never call `Decimal` with a float.
- [x] Implement formulas for subtraction and ratios by stable formula IDs rather than evaluating arbitrary YAML expressions.
- [x] Prove `gross_profit = revenue - direct_cost`, `gross_margin = gross_profit / revenue`, `cash_conversion = operating_cash_flow / operating_profit`, and DSO uses multiplier `365`.
- [x] Run task tests plus existing known-answer tests, then commit.

### Task 3: Read Only Published, Version-scoped Canonical Facts

**Files:**
- Create: `services/api/src/flow_api/metrics/repositories.py`
- Create: `services/api/src/flow_api/metrics/source_rows.py`
- Create: `services/api/tests/integration/test_metric_source_repository.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class PublishedMetricSource:
    batch_id: UUID
    import_version_id: UUID
    analysis_start_month: int
    analysis_end_month: int
    comparison_start_month: int
    comparison_end_month: int
    actual_scenario_code: str
    budget_scenario_code: str

class MetricSourceRepository:
    def get_published_source(self, session: Session, batch_id: UUID) -> PublishedMetricSource: ...
    def operating_rows(self, session: Session, source: PublishedMetricSource) -> tuple[OperatingSourceRow, ...]: ...
    def financial_rows(self, session: Session, source: PublishedMetricSource) -> tuple[FinancialSourceRow, ...]: ...
    def budget_rows(self, session: Session, source: PublishedMetricSource) -> tuple[BudgetSourceRow, ...]: ...
    def ar_rows(self, session: Session, source: PublishedMetricSource) -> tuple[ArSourceRow, ...]: ...
```

- [x] Write failing integration tests with two import versions in one batch; assert every returned fact belongs to the active published version and the unpublished version is absent.
- [x] Test typed rejection for draft, blocked, ready-without-publication, failed reconciliation and unacknowledged warning states.
- [x] Implement immutable source-row dataclasses containing dimension IDs/codes and Decimals, not ORM objects, so calculation code cannot mutate database state.
- [x] Parse analysis/comparison windows from `ImportVersion.summary["batch"]` and validate the referenced periods exist.
- [x] Query every fact table with an explicit `import_version_id` predicate and deterministic ordering.
- [x] Run integration tests and static checks, then commit.

### Task 4: Enforce Dimension-safe and Semi-additive Aggregation

**Files:**
- Create: `services/api/src/flow_api/metrics/grain.py`
- Create: `services/api/src/flow_api/metrics/aggregation.py`
- Create: `services/api/tests/metrics/test_grain.py`
- Create: `services/api/tests/metrics/test_aggregation.py`

**Interfaces:**

```python
DimensionName = Literal[
    "organization", "customer", "customer_segment", "logistics_product", "region"
]

@dataclass(frozen=True, slots=True)
class MetricGrain:
    organization_id: UUID | None = None
    customer_id: UUID | None = None
    customer_segment_id: UUID | None = None
    logistics_product_id: UUID | None = None
    region_id: UUID | None = None

@dataclass(frozen=True, slots=True)
class PeriodValue:
    period_id: UUID
    month_key: int
    grain: MetricGrain
    value: Decimal

def aggregate_flow(values: Iterable[PeriodValue], months: frozenset[int]) -> dict[MetricGrain, Decimal]: ...
def aggregate_closing_balance(values: Iterable[PeriodValue], months: frozenset[int]) -> dict[MetricGrain, Decimal]: ...
def validate_grain(metric: MetricSpec, grain: MetricGrain) -> None: ...
```

- [ ] Write failing tests proving additive totals equal allowed child slices for organization, segment, product and region, including segment × product.
- [ ] Prove customer and customer-segment cannot both be populated in one value and unsupported dimensions raise `UnsupportedMetricGrainError`.
- [ ] Prove 12 monthly AR balances produce the final month balance for YTD/trailing windows rather than the sum of 12 balances.
- [ ] Prove gross margin at total grain is `total gross profit / total revenue`, not the average or sum of child gross margins.
- [ ] Implement deterministic grain keys and source-specific dimension projection. Do not allocate financial or AR values into dimensions absent from their sources.
- [ ] Run task tests and commit.

### Task 5: Build Month, YTD, Budget, YoY and Trailing-12 Windows

**Files:**
- Create: `services/api/src/flow_api/metrics/windows.py`
- Create: `services/api/src/flow_api/metrics/comparisons.py`
- Create: `services/api/tests/metrics/test_windows.py`
- Create: `services/api/tests/metrics/test_comparisons.py`

**Interfaces:**

```python
ComparisonType = Literal[
    "actual_month", "actual_ytd", "budget_month", "budget_ytd",
    "budget_variance", "budget_variance_pct", "prior_year_month",
    "prior_year_ytd", "yoy_variance", "yoy_variance_pct", "trailing_12"
]

@dataclass(frozen=True, slots=True)
class MetricWindow:
    comparison_type: ComparisonType
    as_of_month: int
    included_months: frozenset[int]

def metric_windows(periods: tuple[int, ...], as_of_month: int) -> tuple[MetricWindow, ...]: ...
def variance(actual: Decimal, comparison: Decimal) -> Decimal: ...
def variance_pct(metric_code: str, actual: Decimal, comparison: Decimal) -> CalculatedDecimal: ...
```

- [ ] Write failing tests at January, fiscal-year end and the fixture as-of month `202608` for month, calendar YTD, same-prior-year window and trailing 12 months.
- [ ] Require missing prior-year periods to omit the comparison with a typed availability reason; never substitute zero for missing data.
- [ ] Prove variance sign is `actual - comparison` for amount/volume metrics and ratio-point variance uses direct ratio subtraction.
- [ ] Prove budget comparisons are emitted only for catalog-declared compatible grains.
- [ ] Implement pure window and comparison functions with sorted deterministic output, run tests and commit.

### Task 6: Calculate the Complete Metric Graph

**Files:**
- Create: `services/api/src/flow_api/metrics/calculator.py`
- Create: `services/api/src/flow_api/metrics/results.py`
- Create: `services/api/tests/metrics/test_calculator.py`
- Create: `services/api/tests/integration/test_metric_calculator_known_answers.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class CalculatedMetricValue:
    metric_code: str
    metric_version: int
    comparison_type: ComparisonType
    period_id: UUID
    grain: MetricGrain
    exact_value: Decimal
    persisted_value: Decimal
    dependency_values: tuple[tuple[str, Decimal], ...]
    source_fact_count: int

@dataclass(frozen=True, slots=True)
class MetricCalculationResult:
    source: PublishedMetricSource
    as_of_period_id: UUID
    definition_set_hash: str
    values: tuple[CalculatedMetricValue, ...]
    fingerprint: str

class MetricCalculator:
    def calculate(
        self,
        source: PublishedMetricSource,
        catalog: MetricCatalog,
        as_of_month: int,
    ) -> MetricCalculationResult: ...
```

- [ ] Write failing tests for all 15 metrics at total grain and every allowed dimensional slice.
- [ ] Assert orders, fulfilled units, revenue, direct cost, gross profit, operating profit and operating cash flow against direct fixture sums.
- [ ] Assert revenue/order, cost/order, gross margin, fulfillment cost rate, collection rate, DSO and cash conversion against independently calculated Decimal oracle strings.
- [ ] Assert budget, YoY and final-month/YTD windows, plus `sum(organization slices) == total` and equivalent allowed-slice invariants.
- [ ] Implement source metric collection first, then derived metrics in catalog topological order; each derived value records exact same-grain dependency values.
- [ ] Sort all results by metric code, comparison type, period and grain before fingerprinting. Prove repeated calculations are byte-identical.
- [ ] Run unit/integration tests, Ruff and mypy, then commit.

### Task 7: Complete Metric Snapshot Identity, Dependency and Trace Schema

**Files:**
- Create: `services/api/migrations/versions/0006_metric_snapshot_identity.py`
- Modify: `services/api/src/flow_api/infrastructure/models/analytics.py`
- Modify: `services/api/src/flow_api/infrastructure/models/__init__.py`
- Create: `services/api/tests/integration/test_metric_snapshot_schema.py`

**Interfaces:**

```python
class MetricDefinitionDependency(Base):
    metric_definition_id: UUID
    dependency_definition_id: UUID
    position: int

class MetricSnapshot(Base):
    batch_id: UUID
    import_version_id: UUID
    as_of_period_id: UUID
    version: int
    engine_version: str
    definition_set_id: str
    definition_set_hash: str
    fingerprint: str
    status: Literal["building", "published", "failed"]

class MetricValue(Base):
    # existing identity and dimension columns remain
    exact_value: str
    calculation_trace: dict[str, object]
```

- [ ] Write failing model/migration tests for foreign keys, unique snapshot identity, definition dependency order, hash length, allowed status and append-only event listeners.
- [ ] Add `import_version_id`, `as_of_period_id`, `definition_set_id`, `definition_set_hash`, `fingerprint` and `status` to `metric_snapshot`.
- [ ] Add `metric_definition_dependency` with unique parent/dependency and parent/position constraints.
- [ ] Add `exact_value` and `calculation_trace` to `metric_value`; keep existing `value Numeric(24,4)` for indexed display/query output.
- [ ] Add model-level guards rejecting update/delete of published snapshots, their values, and definition dependency records.
- [ ] Verify `upgrade 0005 → 0006 → downgrade 0005 → upgrade 0006` and the full isolated migration round trip.
- [ ] Run integration/static tests, then commit and push.

### Task 8: Persist and Publish Snapshots Atomically

**Files:**
- Create: `services/api/src/flow_api/metrics/persistence.py`
- Create: `services/api/src/flow_api/metrics/service.py`
- Create: `services/api/tests/integration/test_metric_snapshot_service.py`
- Create: `services/api/tests/integration/test_metric_snapshot_atomicity.py`

**Interfaces:**

```python
class MetricSnapshotBlockedError(RuntimeError):
    reasons: tuple[str, ...]

class MetricSnapshotService:
    def create_snapshot(
        self,
        session: Session,
        *,
        batch_id: UUID,
        as_of_month: int,
        catalog: MetricCatalog,
    ) -> MetricSnapshot: ...
    def get_snapshot_values(
        self,
        session: Session,
        snapshot_id: UUID,
    ) -> tuple[MetricValue, ...]: ...
```

- [ ] Write failing lifecycle tests for eligible publication, ineligible import states, idempotent retry, new snapshot after corrected import and an injected mid-write failure.
- [ ] Upsert metric definitions by stable `(metric_code, version)` and reject conflicting content under an existing identity.
- [ ] Persist definition dependency edges in topological position and values with exact-value/calculation traces.
- [ ] Write values and switch snapshot `building → published` in one transaction; injected failure must leave no visible snapshot or partial values.
- [ ] Return an existing published snapshot for the same full identity and fingerprint. A changed import version, catalog hash or engine version creates a new version.
- [ ] Prove old snapshots and values remain unchanged after corrected import publication, then commit.

### Task 9: Build the End-to-end Metric Acceptance Gate

**Files:**
- Create: `scripts/summarize_metrics.py`
- Create: `scripts/test_metrics_known_answers.sh`
- Create: `services/api/tests/integration/test_metric_snapshot_e2e.py`
- Create: `docs/metrics/flow-v1-metrics.md`
- Modify: `Makefile`
- Modify: `.github/workflows/ci.yml`
- Create: `docs/implementation/phase-4-verification.md`
- Modify: `docs/knowledge-base/00_start_here/PROJECT_STATE.md`
- Modify: `docs/knowledge-base/00_start_here/AGENT_START_HERE.md`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`

**Interfaces:**
- Adds `make test-metrics-known-answers` and GitHub Actions job `metrics-known-answers`.

- [ ] Write a failing E2E test that publishes standard and external workbook batches through the Phase 3 service, creates Metric Snapshots through the Phase 4 service and compares their fingerprints and every oracle value.
- [ ] Assert both snapshots use different `import_version_id` values but equal definition set hashes, value fingerprints and exact business values.
- [ ] Assert additive slice invariants, semi-additive AR behavior, same-grain ratio dependencies, no invented budget grains and append-only history.
- [ ] Make the shell gate run Phase 4 tests, Phase 3 intake acceptance, Ruff, mypy, migration round trip, deterministic catalog/oracle checks and a concise machine-readable metric summary.
- [ ] Document every metric formula, source, unit, allowed dimensions, time behavior, comparison availability, rounding policy and blocker code.
- [ ] Add the CI job, run the gate from a clean worktree and record exact local/CI evidence in `phase-4-verification.md`.
- [ ] Update project state and Agent start documents, regenerate knowledge-base inventory and SHA-256 manifests, then verify every manifest entry.
- [ ] Commit, push and require every GitHub Actions job to pass before marking Phase 4 complete.

## Expected Phase 4 Deliverable

At completion, FLOW will have a governed semantic layer rather than page-specific KPI queries. A published canonical batch produces one immutable Metric Snapshot with exact month/YTD/budget/YoY/trailing-12 values, explicit formula dependencies, dimension-safe slices, correct closing-balance behavior and a reproducible fingerprint. Dashboard, Investigation and publishing phases can consume this snapshot without recalculating financial numbers or reading Excel/canonical facts directly.
