# FLOW V1 Phase 5 Analysis & Findings Design

**Status:** Approved for autonomous implementation

**Date:** 2026-09-01

**Decision owner:** Project owner

**Scope:** Deterministic analysis, typed Finding candidates, transparent ranking, evidence, persistence, and degradation

## 1. Purpose

Phase 5 turns one published Metric Snapshot and its bound canonical detail into a reusable, deterministic operating-analysis layer. It must explain the fixture's central Finance BP story—scale grows while profit quality and cash conversion deteriorate—without allowing AI, dashboards, or report renderers to recalculate or invent financial facts.

The phase produces immutable Analysis Runs that later phases consume unchanged:

```text
Published Metric Snapshot + bound Canonical Detail + versioned Analysis Policy
                                  ↓
                       Typed Analysis Playbooks
                                  ↓
                    Reconciled Analysis Results
                                  ↓
             Deterministic Finding Candidates + Evidence
                                  ↓
            Dashboard / Investigation / AI / Reports
```

## 2. Approved product decisions

1. Phase 5 generates only Findings that deterministic calculations and existing evidence fully support.
2. Missing inputs cause an explicit degraded Analysis Result; they do not create a hypothesis or speculative Finding.
3. The architecture uses typed analysis playbooks behind one shared protocol. It does not hard-code one monolithic service and does not introduce a general-purpose formula DSL.
4. All calculations use `Decimal`; persisted money reconciles within `0.01 CNY` and retains exact calculation traces.
5. Analysis Runs bind immutable input and policy identities. The same identities are idempotent and cannot produce numerical drift.
6. Phase 6 and later consumers read published Analysis Runs; they do not re-run analysis formulas.

## 3. Boundaries

### 3.1 Allowed inputs

- one published `MetricSnapshot`;
- only the published `ImportVersion` already bound to that snapshot;
- version-scoped canonical operating, financial, AR, budget, dimension, and lineage repositories;
- a versioned analysis-policy document with materiality and ranking parameters;
- data-quality, reconciliation, warning-acknowledgement, and source-coverage state already approved by earlier phases.

### 3.2 Forbidden inputs and behaviors

- no direct workbook, worksheet, or ad-hoc file reads;
- no unpublished import version or metric snapshot;
- no float at a public calculation boundary;
- no AI-generated amounts, drivers, causal claims, confidence, or rank;
- no implicit allocation of unavailable budget detail;
- no Finding when its bridge fails, required evidence is incomplete, or required fields are unavailable;
- no mutation of a published Analysis Run or its results, drivers, scores, and evidence.

### 3.3 Deferred scope

- human review and approval workflow beyond the existing schema contract;
- hypothesis generation and AI-assisted investigative questions;
- forecasting, scenarios, recommendations, actions, owners, and deadlines;
- dashboard and Investigation UI;
- report composition and PPT, Excel, or HTML/PDF rendering;
- user-authored formula DSL or arbitrary third-party analysis plug-ins.

## 4. Architecture

### 4.1 Shared playbook protocol

Every playbook implements the same lifecycle:

1. declare its stable code, version, required sources, required fields, output unit, comparison window, and supported dimensions;
2. check applicability against the snapshot and canonical-field manifest;
3. load only repositories explicitly declared by the playbook;
4. calculate typed driver contributions;
5. prove the sum of drivers equals the stated impact within tolerance;
6. build calculation, metric, and source-record evidence references;
7. return either `complete`, `degraded`, or `not_applicable`—never a partial success disguised as complete;
8. qualify a Finding only from a complete, reconciled, evidence-complete result.

The registry uses stable playbook codes:

- `revenue_vpm`;
- `gross_profit_bridge`;
- `operating_profit_bridge`;
- `fulfillment_cost_rve`;
- `ar_cash_impact`.

Gross-profit and operating-profit bridges are separate registered analyses even though they share bridge utilities.

### 4.2 Analysis Run identity and lifecycle

An Analysis Run is uniquely identified by:

```text
metric_snapshot_id
+ policy_set_hash
+ engine_version
```

Lifecycle:

```text
building → published
         ↘ failed
```

- `building` children are written in one database transaction.
- Publication occurs only when all registered playbooks have a terminal result and every complete bridge passes its invariant.
- A degraded result does not fail the run; it records exactly which capability is unavailable and why.
- An unexpected calculation, persistence, or invariant error rolls back all children and records no published run.
- A retry with the same identity returns the existing published run or safely resumes after a failed attempt according to the service contract.

### 4.3 Typed output contract

Each `AnalysisResult` contains:

- result ID, run ID, playbook code and version;
- status: `complete`, `degraded`, or `not_applicable`;
- analysis period and comparison period/window;
- comparison basis: prior year or budget;
- impact amount and unit;
- exact driver contributions in display order;
- reconciliation difference and tolerance;
- required, available, and missing fields;
- source-record count and deterministic calculation trace;
- degradation code and human-readable explanation when incomplete.

Driver contributions contain stable driver code, calculation method, amount, contribution ratio, and exact trace. Contribution ratio is `driver amount / total impact` only when the total impact is non-zero; otherwise it is absent rather than fabricated.

## 5. Playbook calculation models

### 5.1 Revenue Volume / Price / Mix

Comparison is current trailing-12 analysis window versus the aligned prior-year trailing-12 window. Quantity is order count. Mix cells are logistics products; the calculation may additionally project results by supported dimensions after the total bridge passes.

For product cell `i`:

```text
q0_i = comparison orders
q1_i = analysis orders
p0_i = comparison revenue / comparison orders
p1_i = analysis revenue / analysis orders
P0   = total comparison revenue / total comparison orders

Volume = (Σq1_i - Σq0_i) × P0
Mix    = Σ[q1_i × (p0_i - P0)]
Price  = Σ[q1_i × (p1_i - p0_i)]
```

Invariant:

```text
Volume + Mix + Price = analysis revenue - comparison revenue
```

Requirements and degradation:

- both windows must contain revenue and order count;
- every product participating in either window must have non-zero comparison and analysis orders;
- product keys must reconcile to total revenue and orders;
- a new, lost, or zero-volume product makes V/P/M `degraded` in V1 because assigning a reference price would introduce policy judgment;
- the degraded result may still report the already-published descriptive revenue variance, but it does not create a V/P/M Finding.

### 5.2 Fulfillment-cost Rate / Volume / Efficiency

Fulfillment cost is direct operating cost. The model separates scale, shipments-per-order efficiency, and cost-per-shipment rate:

```text
o0 = comparison orders
o1 = analysis orders
s0 = comparison shipments / comparison orders
s1 = analysis shipments / analysis orders
c0 = comparison direct cost / comparison shipments
c1 = analysis direct cost / analysis shipments

Volume     = (o1 - o0) × s0 × c0
Efficiency = o1 × (s1 - s0) × c0
Rate       = o1 × s1 × (c1 - c0)
```

Invariant:

```text
Volume + Efficiency + Rate = analysis direct cost - comparison direct cost
```

All required denominators must be positive. The playbook also calculates warehousing, transportation, and other-direct-cost sub-bridges using the same quantity framework where the canonical fields are present. It never labels a rate increase as supplier pricing or operational inefficiency without separate business evidence; the labels describe mathematical drivers only.

### 5.3 Gross-profit bridge

Gross profit is bridged from the comparison period to the analysis period by reusing the reconciled revenue V/P/M output and separating direct-cost categories:

```text
Revenue Volume contribution
+ Revenue Mix contribution
+ Revenue Price contribution
- Warehousing cost change
- Transportation cost change
- Other direct cost change
= Gross-profit change
```

Cost increases have negative profit contribution; cost decreases have positive contribution. The result must equal the published gross-profit metric variance and the canonical financial-account variance.

If V/P/M is degraded, the gross-profit bridge is also degraded rather than silently replacing it with one undifferentiated revenue driver.

### 5.4 Operating-profit bridge

The operating-profit bridge extends the reconciled gross-profit bridge:

```text
Gross-profit driver contributions
- Operating-expense change
= Operating-profit change
```

It must reconcile both to the published operating-profit variance and to canonical financial actuals. Budget variance may be stored as a second Analysis Result only at the total or organization grains supported by budget data; the engine must not allocate budget to customer, product, segment, or region.

### 5.5 AR, DSO, collection, and operating-cash impact

The playbook is descriptive and financial, not a causal cash-flow model.

It calculates:

- closing AR change versus aligned prior-year closing AR;
- DSO change using the Phase 4 metric definition;
- current aging-bucket distribution and overdue concentration;
- collection rate and collection shortfall from canonical due and collected amounts;
- working-capital cash impact as the negative of the closing AR increase:

```text
AR cash impact = -(analysis closing AR - comparison closing AR)
```

This amount is explicitly labelled `estimated_working_capital_cash_impact`, not operating cash flow. It is compared with—but never asserted to fully explain—the published operating-cash-flow variance.

The driver bridge for AR cash impact uses aging buckets:

```text
bucket impact = -(analysis bucket balance - comparison bucket balance)
Σ bucket impact = AR cash impact
```

Customer concentration is evidence and prioritization context. It is not added to the bucket bridge because doing so would double-count the same AR balance.

## 6. Finding qualification

### 6.1 Candidate contract

A Finding candidate contains:

- stable finding type and source Analysis Result;
- factual title generated from deterministic templates;
- abnormal fact with explicit comparison basis;
- signed financial impact and unit;
- business meaning limited to what the calculation proves;
- materiality, persistence, evidence-completeness, and management-relevance component scores;
- total rank score and scoring-policy version;
- status `candidate`;
- links to its driver contributions and evidence.

Examples of allowed wording:

- “经营利润同比减少 77.5 万元，运输成本率上升为最大负向数学驱动。”
- “期末应收同比增加 42.0 万元，对营运资金现金形成约 42.0 万元负向占用。”

Disallowed wording without separate evidence:

- “承运商涨价导致利润下降。”
- “客户经营恶化导致无法回款。”
- “应收增加导致全部经营现金流下降。”

### 6.2 Hard qualification gates

No Finding is created unless all gates pass:

1. the source result is `complete`;
2. its bridge reconciles within `0.01 CNY`;
3. all required evidence types are present and system-verified;
4. the absolute financial impact meets the configured materiality threshold;
5. the abnormal direction is defined by the typed Finding policy;
6. the result references the current Analysis Run's bound snapshot and import version;
7. the Finding fingerprint is unique within the run.

Failure of a gate remains visible in the result's qualification trace; it does not create a low-confidence Finding.

## 7. Transparent ranking

V1 uses a versioned deterministic score from 0 to 100:

```text
total score =
    materiality × 40%
  + persistence × 20%
  + evidence completeness × 20%
  + management relevance × 20%
```

Components:

- **Materiality:** `min(abs(impact) / high_materiality_amount, 1) × 100`; the lower qualification threshold remains a separate hard gate.
- **Persistence:** percentage of the configured recent periods in which the abnormal direction exceeded its period threshold. Three periods are used by the V1 policy when monthly evidence exists. A point-in-time-only analysis uses a declared neutral persistence score of 50 and records that policy choice.
- **Evidence completeness:** verified required evidence count divided by required evidence count. Under the approved deterministic-only policy, a qualified Finding must score 100 here.
- **Management relevance:** a policy value by Finding type, not an AI opinion. Operating profit, gross profit, and cash/AR impacts receive higher values than descriptive volume changes.

Every persisted score retains raw values, normalization parameters, weight, weighted value, and policy version. Ranking is descending total score, then descending absolute impact, then stable Finding fingerprint to make ties deterministic.

## 8. Evidence model

Every qualified Finding requires:

1. `metric_value` evidence for the headline current and comparison values;
2. `calculation` evidence for the Analysis Result and exact formula trace;
3. `source_record_set` evidence containing a deterministic digest, row count, and repository query boundary;
4. `lineage` evidence linking the canonical record set to its import version and source artifact;
5. `invariant` evidence showing contribution sum, target impact, tolerance, and difference.

System-verifiable evidence is created with status `verified` only after its referential and digest checks pass. Human-confirmed causal documents are outside Phase 5 and remain `pending` until a later Investigation workflow verifies them.

The evidence model distinguishes supporting objects from claims. A source row proves a recorded value, not a business cause.

## 9. Persistence changes

Phase 5 extends, rather than replaces, the existing analytics schema.

### 9.1 New tables

`analysis_run`

- snapshot, import version, policy identity/hash, engine version, fingerprint, status;
- unique immutable identity and append-only protection after publication.

`analysis_result`

- run, playbook code/version, status, comparison basis, periods, impact, unit;
- reconciliation difference/tolerance;
- field coverage, calculation trace, and degradation fields;
- unique playbook/result identity within a run.

`analysis_driver`

- result, position, driver code, method, amount, optional ratio, and trace;
- unique position and stable driver code per result.

`finding_score_component`

- finding, component code, raw value, normalized score, weight, weighted score, and policy trace.

### 9.2 Existing-table extensions

`finding`

- add `analysis_result_id`, finding type, fact statement, comparison basis, total score, policy version, fingerprint, and qualification trace;
- retain `metric_snapshot_id` as a direct integrity boundary for existing publishing consumers;
- enforce one deterministic fingerprint per Analysis Run.

`driver_contribution`

- remains the Finding-facing copy of the qualifying Analysis Result drivers;
- add exact trace where necessary;
- amounts must equal the Analysis Result drivers used by the Finding.

`evidence`

- extend allowed object types for Analysis Run, Analysis Result, canonical record set, lineage, and invariant references;
- add evidence digest and structured verification trace;
- preserve the existing pending/verified/rejected lifecycle.

### 9.3 Atomic publication

The service writes the run, results, drivers, qualified Findings, score components, and evidence in one transaction. It verifies persisted rows before changing the run from `building` to `published`. A failure rolls back the transaction. Published rows are append-only.

## 10. Degradation contract

Degradation is structured data, not a log message.

Required codes include:

- `missing_required_field`;
- `missing_comparison_window`;
- `zero_denominator`;
- `unmatched_mix_cell`;
- `unsupported_grain`;
- `insufficient_periods_for_persistence`;
- `source_total_mismatch`;
- `upstream_result_degraded`.

A degraded result records:

- unavailable capability;
- missing fields or failed prerequisite result;
- calculations that remain safe to display;
- calculations and Finding types that are suppressed;
- recommended data remediation.

The run may publish with degraded results so later UI can accurately explain reduced analysis depth. A degraded result never has drivers presented as a complete bridge and never emits a Finding.

## 11. Determinism, precision, and security

- Inputs, intermediate calculations, outputs, thresholds, weights, and tolerances are `Decimal`.
- Money is retained at scale 4 and bridge acceptance is `abs(difference) <= 0.01`.
- Ratios retain scale 6 in calculation traces and follow existing persistence policy at database boundaries.
- Source queries are version-scoped and use stable ordering before hashing.
- Fingerprints use canonical JSON with sorted keys and explicit decimal strings.
- Registry codes, policy documents, and formulas are application-owned—not user-executable code.
- Evidence never stores unrestricted file paths or arbitrary SQL.

## 12. Verification strategy

### 12.1 Pure calculation tests

- exact known-answer V/P/M bridge;
- exact fulfillment Rate/Volume/Efficiency bridge;
- gross-profit and operating-profit bridges, including cost sign convention;
- AR bucket bridge and DSO/collection calculations;
- zero denominators, absent windows, missing cells, and input-float rejection;
- score normalization, weights, persistence, deterministic ties, and qualification gates.

### 12.2 Repository and persistence tests

- only the snapshot-bound published import version is read;
- unpublished or mismatched snapshots are rejected;
- run identity is idempotent;
- all children publish atomically;
- a bridge or persistence error leaves no published partial result;
- published run, result, driver, Finding score, and evidence rows are append-only;
- evidence digests resolve to the expected version-scoped records.

### 12.3 End-to-end invariant gate

`make test-analysis-invariants` must:

1. initialize an empty database and migrate to head;
2. import and publish the standard reference fixture;
3. build the Phase 4 Metric Snapshot;
4. publish one Analysis Run;
5. prove every complete bridge reconciles within `0.01 CNY`;
6. prove the intended profit/cash deterioration Findings rank at the top;
7. remove selected fields in controlled variants and assert explicit degradation with no speculative Finding;
8. repeat the same run identity and prove idempotence and numerical stability.

### 12.4 Regression gates

- full API test suite;
- Ruff and strict mypy;
- Phase 3 intake acceptance;
- Phase 4 known-answer acceptance;
- contract drift check.

## 13. Acceptance criteria

Phase 5 is complete only when:

1. all five registered analysis results are produced from the reference fixture;
2. every complete bridge reconciles within `0.01 CNY`;
3. the “growth with profit and cash deterioration” story is represented by deterministic, evidence-complete Findings;
4. profit/cash deterioration ranks above less material descriptive changes under the documented score;
5. every Finding can be recalculated from its result, drivers, snapshot values, and canonical evidence;
6. removed optional diagnostic fields cause explicit degradation and suppress affected Findings;
7. repeated execution with identical input/policy identity is idempotent;
8. no consumer needs to read raw Excel or recalculate analysis;
9. all phase and regression verification commands pass;
10. implementation and verification evidence are committed and pushed to `main`.

## 14. Consequences for later phases

- Phase 6 dashboard reads Analysis Results and ranked Finding candidates through an API/client boundary.
- Investigation can display exact bridges, formulas, source coverage, evidence, and degradation without recomputation.
- AI receives IDs and verified facts, not raw financial rows as an unrestricted calculation substrate.
- Phase 7 publishing selects approved Findings later, while preserving the same Analysis Run and numerical traces.
- New industries add typed playbooks or policy variants behind the shared protocol without changing the canonical-layer contract.
