# FLOW V1 Phase 2 Canonical Fixture & Excel Contract Implementation Plan

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：Phase 2 功能切片已有实现与[阶段验收](../../implementation/phase-2-verification.md)。正文步骤、示例代码及未勾选项保留当时计划语境，不构成当前待办清单，也不表示已对当前提交重跑全部门禁。
> 当前入口见[文档导航](../../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../../implementation/2026-09-04-review-repairs.md)。

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Every implementation task follows test-driven development and ends with a scoped commit and push.

**Goal:** Freeze `flow.excel.v1` as FLOW's first executable data contract, produce a deterministic logistics-supply-chain reference dataset and standard Excel workbook, and prove that workbook import, PostgreSQL canonical persistence, and workbook export preserve meaning exactly.

**Architecture:** The YAML contract is the single machine-readable definition of workbook sheets and fields. A framework-independent canonical package loads and validates that contract, creates stable fixture records with `Decimal` values and deterministic IDs, and serializes those records through Excel without using worksheet positions as identity. The import path resolves stable business keys into Phase 1 canonical models, while the export path reads canonical records back into the same contract. Dashboard, metric, AI, and publishing code remain outside this phase and must never read the workbook directly.

**Tech Stack:** Python 3.13, Pydantic 2, PyYAML, openpyxl, SQLAlchemy 2, PostgreSQL 18, pytest, Ruff, mypy, Make, JSON, YAML, XLSX.

## Scope Decisions

- Contract version is exactly `flow.excel.v1`; breaking changes require a new version rather than editing field meaning in place.
- The fixture has 12 primary analysis months from `2025-09` through `2026-08` and 12 matched prior-year comparator months from `2024-09` through `2025-08`. The product experience is still a 12-month analysis window; comparator rows exist so Phase 4 can calculate同比 from canonical facts.
- The primary scenario is actual; budget covers the 12 primary months under scenario `BUDGET_FY26_V1`.
- The workbook uses stable business keys such as `customer_code` and `management_account_code`. Database UUIDv7 identities are storage concerns and are never required from a person filling the template.
- Fixture-only database IDs use deterministic UUIDv5 values derived from a fixed FLOW namespace, so tests and expected answers are reproducible.
- Amounts and quantities are serialized as decimal strings in canonical JSON and as numeric cells with explicit number formats in XLSX. Python floats are rejected at package boundaries.
- Empty optional values stay null. Empty strings, missing values, zero, and the text `NULL` are not treated as interchangeable.
- `08_组织与区域` is a typed master sheet with `entity_type` equal to `organization` or `region`; the importer splits it into the two Phase 1 dimensions.
- Scenario metadata in `01_分析批次` creates the matching `ScenarioVersion`; no hidden workbook sheet is required.
- Phase 2 accepts only a valid FLOW standard workbook. Heuristic recognition, aliases, AI mapping, cleaning audit, acknowledgements, and non-standard workbooks belong to Phase 3.
- Original research and conversation archives remain immutable.

## Contract Shape

The ten sheets are fixed and ordered:

1. `00_填写说明`
2. `01_分析批次`
3. `02_经营实际`
4. `03_财务实际`
5. `04_月度预算`
6. `05_应收回款`
7. `06_客户主数据`
8. `07_物流产品`
9. `08_组织与区域`
10. `09_管理科目`

Every contract field has `field_id`, `display_name`, `data_type`, `required`, `nullable`, `description`, and optional `unit`, `enum`, `foreign_key`, `minimum`, and `format`. Every data sheet declares its grain and key fields. Workbook row 1 contains display names, row 2 contains immutable field IDs, row 3 contains type/unit hints, and data begins on row 4. The instruction sheet explains this convention and the batch sheet carries the contract version.

## Planned Package Boundary

```text
templates/excel/flow_v1_contract.yaml
             │
             ▼
flow_api.data_contract.contract
             │
       ┌─────┴─────────┐
       ▼               ▼
 fixture generator     workbook renderer/parser
       │               │
       ▼               ▼
fixtures/canonical   flow_standard_v1.xlsx
       │               │
       └──────┬────────┘
              ▼
       canonical package
              │
              ▼
     temporary PostgreSQL load
              │
              ▼
       exported workbook
              │
              ▼
    semantic snapshot comparison
```

---

### Task 1: Define and Validate `flow.excel.v1`

**Files:**
- Modify: `services/api/pyproject.toml`
- Modify: `services/api/uv.lock`
- Create: `templates/excel/flow_v1_contract.yaml`
- Create: `services/api/src/flow_api/data_contract/__init__.py`
- Create: `services/api/src/flow_api/data_contract/models.py`
- Create: `services/api/src/flow_api/data_contract/contract.py`
- Create: `services/api/tests/data_contract/test_contract.py`

**Interfaces:**
- Consumes: Phase 1 canonical model names and workbook decisions in the approved V1 specification.
- Produces: `WorkbookContract`, `SheetContract`, `FieldContract`, `load_contract(path)`, `get_sheet(sheet_id)`, and a validated `flow.excel.v1` YAML artifact.

- [ ] **Step 1: Write failing contract tests**

Tests must assert:

- contract version is `flow.excel.v1`;
- sheet names and order equal the ten-sheet list above;
- every field ID is snake_case and unique within its sheet;
- sheet IDs and field IDs are stable identifiers independent of display names and positions;
- `required=true` cannot coexist with `nullable=true`;
- foreign keys reference an existing sheet and field;
- all fact sheets declare non-empty grains;
- money and quantity fields declare their units and decimal scale;
- every Phase 1 canonical fact column has a workbook source or an explicit importer-generated source.

Run: `cd services/api && uv run pytest tests/data_contract/test_contract.py -q`

Expected: FAIL because the package and YAML contract do not exist.

- [ ] **Step 2: Add direct YAML dependency**

Add `pyyaml>=6.0,<7` to runtime dependencies, then regenerate the lock file with:

```bash
cd services/api && uv lock && uv sync --all-groups --frozen
```

- [ ] **Step 3: Implement strict Pydantic contract models**

Use `extra="forbid"` for every model and return immutable tuples from public accessors. Reject duplicate sheet IDs, sheet names, field IDs, missing grain fields, invalid foreign keys, and unknown types while loading.

- [ ] **Step 4: Define all ten sheet contracts**

Minimum field coverage:

- `00_填写说明`: `section_code`, `section_name`, `instruction`, `example`;
- `01_分析批次`: `batch_code`, `contract_version`, `analysis_start_month`, `analysis_end_month`, `comparison_start_month`, `comparison_end_month`, `currency`, `actual_scenario_code`, `budget_scenario_code`, `budget_version_label`, `generated_at`;
- `02_经营实际`: `record_id`, `month_key`, `organization_code`, `customer_code`, `logistics_product_code`, `region_code`, `order_count`, `shipment_count`, `revenue`, `warehousing_cost`, `transportation_cost`, `other_direct_cost`;
- `03_财务实际`: `record_id`, `month_key`, `organization_code`, `management_account_code`, `amount`;
- `04_月度预算`: `record_id`, `month_key`, `organization_code`, optional `customer_segment_code`, optional `logistics_product_code`, optional `management_account_code`, `scenario_code`, `metric_code`, `amount`;
- `05_应收回款`: `record_id`, `month_key`, `customer_code`, optional `invoice_number`, optional `aging_bucket`, `receivable_balance`, `due_amount`, `overdue_amount`, `collected_amount`;
- `06_客户主数据`: `customer_code`, `customer_name`, `industry`, `tier`, `credit_term_days`, `customer_segment_code`, `customer_segment_name`;
- `07_物流产品`: `logistics_product_code`, `logistics_product_name`, `level`, optional `parent_code`;
- `08_组织与区域`: `entity_type`, `entity_code`, `entity_name`, `level`, optional `parent_code`, optional `province`, optional `city`;
- `09_管理科目`: `management_account_code`, `management_account_name`, `category`, optional `financial_account_code`, optional `parent_code`.

- [ ] **Step 5: Prove validation and static quality**

Run:

```bash
cd services/api
uv run pytest tests/data_contract/test_contract.py -q
uv run ruff check src tests
uv run mypy src
```

Expected: all pass.

- [ ] **Step 6: Commit and push**

```bash
git add templates/excel/flow_v1_contract.yaml services/api/pyproject.toml services/api/uv.lock services/api/src/flow_api/data_contract services/api/tests/data_contract/test_contract.py
git commit -m "feat: define FLOW Excel data contract"
git push origin feature/flow-v1-implementation
```

### Task 2: Generate Deterministic Canonical Logistics Fixtures

**Files:**
- Create: `services/api/src/flow_api/data_contract/records.py`
- Create: `services/api/src/flow_api/fixtures/__init__.py`
- Create: `services/api/src/flow_api/fixtures/generator.py`
- Create: `services/api/tests/fixtures/test_generator.py`
- Create: `scripts/generate_phase_2_fixtures.py`
- Create: `fixtures/canonical/*.jsonl`

**Interfaces:**
- Consumes: `WorkbookContract` and Phase 1 canonical grains.
- Produces: `CanonicalPackage`, typed record models, `build_reference_package()`, stable JSONL fixtures, and `write_canonical_package(path)`.

- [ ] **Step 1: Write failing fixture shape tests**

Assert the generated package contains:

- 24 periods: 12 primary plus 12 matched comparator months;
- two customer segments;
- eight logistics products;
- at least three organizations, four regions, sixteen customers, and the required management accounts;
- operating actuals at exact period × organization × customer × product × region grain;
- financial actuals for revenue, direct cost, operating expense, operating profit, operating cash flow, and working-capital accounts;
- monthly budget for every primary month;
- AR balances across current, 1–30, 31–60, 61–90, and 90+ aging buckets;
- unique IDs and valid foreign keys;
- no Python float anywhere in a typed record.

Run: `cd services/api && uv run pytest tests/fixtures/test_generator.py -q`

Expected: FAIL because fixture records and generator do not exist.

- [ ] **Step 2: Implement immutable typed canonical records**

Pydantic record models mirror the workbook contract and use strict strings, integers, datetimes, and `Decimal`. Provide `semantic_dict()` that emits decimals as canonical fixed-scale strings and preserves nulls.

- [ ] **Step 3: Build a deterministic business story**

The reference company must exhibit all of these auditable conditions:

- total revenue grows versus the matched prior-year period;
- key-account segment volume weakens while domestic marketing customers grow;
- gross margin deteriorates in the final quarter despite revenue growth;
- transportation cost per order rises in the final quarter;
- operating cash conversion trails operating profit;
- overdue AR and DSO pressure are concentrated in two customers;
- at least one logistics product has strong growth but sub-target margin;
- budget is missed for operating profit in the final quarter.

All variation comes from explicit deterministic factors—period index, segment, product, customer, region, and a small seasonality table—not random numbers.

- [ ] **Step 4: Generate committed canonical fixtures**

Write one UTF-8 JSONL file per canonical entity/fact plus `manifest.json`. Sort by stable key before writing. Regenerating the files must produce byte-identical output.

Run twice and compare:

```bash
uv run scripts/generate_phase_2_fixtures.py
git diff --exit-code fixtures/canonical
uv run scripts/generate_phase_2_fixtures.py
git diff --exit-code fixtures/canonical
```

Expected: second generation creates no diff.

- [ ] **Step 5: Verify and commit**

Run: `cd services/api && uv run pytest tests/fixtures/test_generator.py -q && uv run mypy src`

```bash
git add services/api/src/flow_api/data_contract/records.py services/api/src/flow_api/fixtures services/api/tests/fixtures scripts/generate_phase_2_fixtures.py fixtures/canonical
git commit -m "feat: add deterministic logistics fixtures"
git push origin feature/flow-v1-implementation
```

### Task 3: Freeze the Known Business Answers

**Files:**
- Create: `services/api/src/flow_api/fixtures/known_answers.py`
- Create: `services/api/tests/fixtures/test_known_answers.py`
- Create: `fixtures/expected/known_answers.json`

**Interfaces:**
- Consumes: generated `CanonicalPackage` only.
- Produces: `calculate_known_answers(package)`, exact expected totals, row counts, reconciliation results, and story assertions.

- [ ] **Step 1: Write failing exact-answer tests**

Calculate independently from fixture records and assert exact `Decimal` equality for:

- actual and prior-year revenue, direct cost, gross profit, gross margin, operating profit, operating cash flow;
- orders and shipments;
- current-year budget revenue and operating profit;
- final-quarter actual-versus-budget operating-profit gap;
- AR balance, due, overdue, collected, and aging-bucket totals at the final month;
- totals by segment, product, organization, region, and month;
- operating-to-financial revenue and direct-cost reconciliation;
- row counts for every entity/fact collection.

Run: `cd services/api && uv run pytest tests/fixtures/test_known_answers.py -q`

Expected: FAIL because the calculator and expected file do not exist.

- [ ] **Step 2: Implement a Decimal-only independent calculator**

Do not copy totals from generator constants. Aggregate generated records, quantize ratios explicitly, serialize all decimals as strings, and store the primary/comparator window metadata alongside results.

- [ ] **Step 3: Encode story predicates**

Store machine-checkable predicates such as `revenue_yoy_positive`, `gross_margin_final_quarter_down`, `cash_conversion_below_one`, and `overdue_ar_concentrated`. Tests must recompute each predicate from records.

- [ ] **Step 4: Generate and verify stable answers**

Run the generator twice and require no second diff. Then run fixture and known-answer tests.

- [ ] **Step 5: Commit and push**

```bash
git add services/api/src/flow_api/fixtures/known_answers.py services/api/tests/fixtures/test_known_answers.py fixtures/expected/known_answers.json scripts/generate_phase_2_fixtures.py
git commit -m "test: freeze FLOW reference business answers"
git push origin feature/flow-v1-implementation
```

### Task 4: Generate the Standard Excel Workbook

**Files:**
- Create: `services/api/src/flow_api/data_contract/workbook.py`
- Create: `services/api/tests/data_contract/test_workbook_generation.py`
- Create: `scripts/generate_standard_workbook.py`
- Create: `fixtures/workbooks/flow_standard_v1.xlsx`

**Interfaces:**
- Consumes: YAML contract and canonical fixtures.
- Produces: `render_workbook(contract, package, destination)`, the committed `flow_standard_v1.xlsx`, and a workbook semantic fingerprint.

- [ ] **Step 1: Write failing workbook tests**

Assert:

- exact sheet names and order;
- frozen panes, autofilter, widths, row styling, and protection of field-ID rows;
- display names in row 1, stable field IDs in row 2, hints in row 3, data from row 4;
- contract version in `01_分析批次` and workbook properties;
- valid date/month, integer, decimal, code, enum, and nullable cell encodings;
- Excel data validation for `entity_type`, category/enums, and constrained fields;
- instruction sheet explains direct-fill and system-conversion paths;
- no formulas, macros, external links, or hidden data sheets;
- all ten sheets can be understood without reading source code.

Run: `cd services/api && uv run pytest tests/data_contract/test_workbook_generation.py -q`

Expected: FAIL because the renderer does not exist.

- [ ] **Step 2: Implement contract-driven rendering**

Use openpyxl write APIs only. Read headers, descriptions, formats, required flags, and validations from YAML; do not hard-code a second field list in the renderer. Use fixed workbook metadata timestamps and deterministic row order. Semantic tests, not raw ZIP hashes, define workbook reproducibility.

- [ ] **Step 3: Add human-safe presentation**

Use a restrained FLOW theme, visible required-field markers, Chinese explanations, examples, top-row filters, frozen headers, sensible widths, and cell comments for business definitions. Presentation must not alter the contract or create merged cells in tabular data sheets.

- [ ] **Step 4: Generate, inspect, and test artifact**

Run:

```bash
uv run scripts/generate_standard_workbook.py
cd services/api && uv run pytest tests/data_contract/test_workbook_generation.py -q
```

Open the artifact with LibreOffice headless conversion or openpyxl reload as an integrity check. Expected: no repair warning and all assertions pass.

- [ ] **Step 5: Commit and push**

```bash
git add services/api/src/flow_api/data_contract/workbook.py services/api/tests/data_contract/test_workbook_generation.py scripts/generate_standard_workbook.py fixtures/workbooks/flow_standard_v1.xlsx
git commit -m "feat: generate FLOW standard Excel workbook"
git push origin feature/flow-v1-implementation
```

### Task 5: Parse the Standard Workbook Without Semantic Loss

**Files:**
- Create: `services/api/src/flow_api/data_contract/parser.py`
- Create: `services/api/src/flow_api/data_contract/semantic.py`
- Create: `services/api/tests/data_contract/test_workbook_parser.py`
- Create: `services/api/tests/data_contract/test_semantic_round_trip.py`

**Interfaces:**
- Consumes: a `flow.excel.v1` workbook.
- Produces: `parse_workbook(path, contract) -> CanonicalPackage`, typed parse issues, `semantic_snapshot(package)`, and `compare_semantics(expected, actual)`.

- [ ] **Step 1: Write failing parser and semantic tests**

Tests cover:

- columns reordered while field-ID row remains valid;
- display names edited while field IDs remain valid;
- missing/duplicate/unknown field IDs;
- missing or incompatible contract version;
- exact decimal scale, zero values, optional nulls, Unicode, month keys, and timestamps;
- duplicate grain and broken relationship diagnostics;
- original package → workbook → parsed package equality for row counts, stable keys, values, nulls, totals, and relationships.

Run: `cd services/api && uv run pytest tests/data_contract/test_workbook_parser.py tests/data_contract/test_semantic_round_trip.py -q`

Expected: FAIL because parser and semantic comparator do not exist.

- [ ] **Step 2: Implement field-ID-driven parsing**

Resolve columns from row 2 only. Treat row 1 as presentation. Convert cell values through contract data types, reject float inputs for financial cells unless their exact decimal representation is safe, and return issues with sheet, row, field ID, code, severity, and message.

- [ ] **Step 3: Implement semantic snapshots**

Canonicalize each collection by stable keys; encode `Decimal`, datetime, and null explicitly; calculate relationship sets and aggregate checksums. Comparisons report precise paths instead of a single boolean.

- [ ] **Step 4: Prove semantic round trip**

Run tests plus `ruff` and `mypy`. Expected: package → XLSX → package has zero differences.

- [ ] **Step 5: Commit and push**

```bash
git add services/api/src/flow_api/data_contract/parser.py services/api/src/flow_api/data_contract/semantic.py services/api/tests/data_contract/test_workbook_parser.py services/api/tests/data_contract/test_semantic_round_trip.py
git commit -m "feat: parse FLOW workbooks by stable field IDs"
git push origin feature/flow-v1-implementation
```

### Task 6: Load Temporary Canonical Tables and Export Again

**Files:**
- Create: `services/api/src/flow_api/data_contract/persistence.py`
- Create: `services/api/tests/integration/test_data_contract_persistence.py`
- Create: `services/api/tests/integration/test_excel_database_round_trip.py`

**Interfaces:**
- Consumes: parsed `CanonicalPackage`, Phase 1 SQLAlchemy models, `ImportVersion`, and `SourceRecord` lineage objects.
- Produces: `load_canonical_package(session, package, source_file)`, `read_canonical_package(session, batch_code)`, and a database-backed export package.

- [ ] **Step 1: Write failing PostgreSQL integration tests**

The tests must:

1. create a source file/import version and one source-record lineage entry for every workbook data row;
2. load dimensions in dependency order and facts atomically;
3. resolve stable business keys to deterministic database IDs;
4. reject duplicate grains and broken required relationships;
5. read the package back from PostgreSQL;
6. render a second workbook and parse it;
7. compare source fixture, first parsed package, database package, and second parsed package semantically.

Run: `make infra-up && cd services/api && uv run pytest tests/integration/test_data_contract_persistence.py tests/integration/test_excel_database_round_trip.py -q`

Expected: FAIL because persistence adapters do not exist.

- [ ] **Step 2: Implement transactional persistence**

Use one database transaction. Build explicit code-to-ID maps. Persist one `SourceRecord` per imported data row and reference it from each fact. Roll back everything on any issue. Do not bypass SQLAlchemy constraints.

- [ ] **Step 3: Implement database-to-package projection**

Read canonical models and reconstruct workbook business keys through dimension joins. Do not read original workbook bytes during export.

- [ ] **Step 4: Prove database round trip**

Assert exact row counts, IDs/business keys, decimals, nulls, totals, reconciliations, and relationships at every boundary. Run migration head/rollback/head once to prove compatibility.

- [ ] **Step 5: Commit and push**

```bash
git add services/api/src/flow_api/data_contract/persistence.py services/api/tests/integration/test_data_contract_persistence.py services/api/tests/integration/test_excel_database_round_trip.py
git commit -m "feat: persist and export canonical workbook data"
git push origin feature/flow-v1-implementation
```

### Task 7: Add the Data-Contract Acceptance Gate and Documentation

**Files:**
- Modify: `Makefile`
- Modify: `.github/workflows/ci.yml`
- Create: `scripts/test_data_contract.sh`
- Create: `docs/data-contract/flow-v1.md`
- Create: `services/api/tests/data_contract/test_committed_artifacts.py`

**Interfaces:**
- Consumes: all Phase 2 artifacts and tests.
- Produces: `make test-data-contract`, CI enforcement, and a human-readable contract reference.

- [ ] **Step 1: Write a failing committed-artifact test**

Regenerate canonical JSONL, known answers, and the standard workbook into a temporary directory. Compare JSON bytes and workbook semantics against committed artifacts. Assert contract documentation names every sheet, grain, key, null rule, unit, relationship, and reconciliation rule.

- [ ] **Step 2: Add one-command acceptance**

`scripts/test_data_contract.sh` must:

1. ensure PostgreSQL is reachable;
2. validate contract YAML;
3. regenerate deterministic canonical fixtures and known answers in a temporary directory;
4. verify committed artifacts;
5. run all unit and integration tests tagged for the data contract;
6. run Ruff and mypy;
7. print a concise row-count and known-answer summary.

Expose it as:

```make
test-data-contract:
	$(MAKE) infra-up
	bash scripts/test_data_contract.sh
```

- [ ] **Step 3: Document the contract**

`docs/data-contract/flow-v1.md` must explain:

- the intermediate-layer purpose and prohibition on downstream raw Excel reads;
- ten sheet roles, field IDs, grains, required/nullable semantics, units, and keys;
- primary and comparison windows;
- direct-fill versus non-standard conversion path;
- blockers versus warnings and the Phase 2/Phase 3 boundary;
- operating/financial reconciliation;
- versioning and compatibility policy;
- how to regenerate, validate, import, and export the standard workbook.

- [ ] **Step 4: Add CI gate**

Add a `data-contract` job or a clearly isolated step that runs `make test-data-contract` against PostgreSQL. Keep Phase 1 jobs intact.

- [ ] **Step 5: Run complete Phase 2 acceptance**

Run: `make test-data-contract`

Expected: all workbook contract, known-answer, persistence, and semantic round-trip tests pass.

- [ ] **Step 6: Commit and push**

```bash
git add Makefile .github/workflows/ci.yml scripts/test_data_contract.sh docs/data-contract/flow-v1.md services/api/tests/data_contract/test_committed_artifacts.py
git commit -m "ci: enforce FLOW data contract acceptance"
git push origin feature/flow-v1-implementation
```

### Task 8: Verify Phase 2 From a Clean Checkout and Update the Knowledge Base

**Files:**
- Create: `docs/implementation/phase-2-verification.md`
- Modify: `docs/knowledge-base/00_start_here/PROJECT_STATE.md`
- Modify: `docs/knowledge-base/00_start_here/AGENT_START_HERE.md`
- Regenerate: `docs/knowledge-base/99_manifest/inventory.tsv`
- Regenerate: `docs/knowledge-base/99_manifest/sha256sums.txt`

**Interfaces:**
- Consumes: pushed Phase 2 branch and CI run.
- Produces: an auditable clean-checkout verification record and stable inputs for the Phase 3 intake plan.

- [ ] **Step 1: Create a temporary clean worktree at the pushed commit**

Do not reuse dependency caches or generated untracked artifacts as proof. In the clean worktree run:

```bash
make bootstrap
make test-data-contract
make phase-1-acceptance
```

Expected: both acceptance commands pass from repository state alone.

- [ ] **Step 2: Confirm committed artifact semantics**

Record contract version, sheet count, fixture row counts, exact known-answer headline totals, migration head, workbook size, and semantic round-trip result.

- [ ] **Step 3: Confirm GitHub Actions**

Wait for the pushed branch workflow. Record the run URL and every job result. Do not mark Phase 2 complete until CI is green.

- [ ] **Step 4: Update state and immutable manifests**

Mark Phase 2 complete and Phase 3 next. Regenerate the knowledge-base inventory and SHA-256 manifest according to `AGENTS.md`. Do not edit original conversation, research, or image archives.

- [ ] **Step 5: Write verification evidence**

`phase-2-verification.md` includes commands, environment, commit, test counts, row counts, known answers, round-trip proof, CI URL, limitations, and the exact Phase 3 handoff contract.

- [ ] **Step 6: Commit and push**

```bash
git add docs/implementation/phase-2-verification.md docs/knowledge-base/00_start_here/PROJECT_STATE.md docs/knowledge-base/00_start_here/AGENT_START_HERE.md docs/knowledge-base/99_manifest/inventory.tsv docs/knowledge-base/99_manifest/sha256sums.txt
git commit -m "docs: record FLOW data contract verification"
git push origin feature/flow-v1-implementation
```

## Phase 2 Exit Criteria

- `flow.excel.v1` is complete, machine-validated, documented, and committed.
- The standard workbook contains all ten sheets and can be directly filled or used as a conversion target.
- Canonical fixtures and known answers regenerate deterministically.
- The 12-month analysis window and matched prior-year comparator produce an auditable Finance BP business story.
- Workbook → typed package → PostgreSQL → typed package → workbook has zero semantic differences.
- Row counts, stable keys, decimals, nulls, totals, relationships, and operating/financial reconciliation are exact.
- `make test-data-contract` and `make phase-1-acceptance` pass from a clean checkout.
- GitHub Actions is green on the pushed feature branch.
- Phase 3 can freeze `flow.excel.v1` and implement non-standard mapping, cleaning, validation, lineage, retry, and immutable batch publication without changing the contract silently.
