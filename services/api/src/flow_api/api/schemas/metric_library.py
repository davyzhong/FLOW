from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MetricFormula(BaseModel):
    op: str
    args: list[str | int | float | MetricFormula]


class MetricDecomposition(BaseModel):
    name: str
    formula_text: str
    factors: list[str]


class MetricEntry(BaseModel):
    metric_code: str
    name: str
    domain: str
    definition: str
    formula_text: str
    formula: MetricFormula
    unit: str | None = None
    time_behavior: str | None = None
    caliber: str | None = None
    default_caliber: str | None = None
    default_basis: str | None = None
    alternative_calibers: list[str] = []
    source_cas: list[str] = []
    source_ifrs: str | None = None
    depends_on: list[str] = []
    decompositions: list[MetricDecomposition] = []
    benchmark: str | None = None
    mpm: bool = False
    mpm_review: dict[str, Any] | None = None
    reconciliation: str | None = None
    migrates_from: str | None = None
    aliases: list[str] = []
    provenance: str | None = None
    collection: Literal["general", "logistics"]
    execution_kind: Literal["engine", "facts", "narrative"] | None = None
    execution_detail: str | None = None
    entry_id: str | None = None
    status: str | None = None


class ReportItem(BaseModel):
    item_id: str
    cas: str
    ifrs: str


class MetricRelation(BaseModel):
    relation: str
    name: str
    expression: str
    note: str
    provenance: str | None = None


class AccountingAccount(BaseModel):
    code: str
    name: str
    category: str
    balance_side: str
    status: str
    standard_ref: str | None = None
    code_note: str | None = None
    source_note: str | None = None


class SupersededNote(BaseModel):
    code: str
    note: str


class AccountingStandard(BaseModel):
    id: str
    name: str
    issuer: str | None = None
    note: str | None = None


class EntryLine(BaseModel):
    direction: str
    account: str
    amount_rule: str


class EntryTemplate(BaseModel):
    template_id: str
    scenario: str
    business_context: str | None = None
    lines: list[EntryLine]
    standard_ref: str | None = None
    related_metrics: list[str] = []
    note: str | None = None


class AccountingFoundation(BaseModel):
    dataset_id: str
    status: str
    known_gaps: list[str] = []
    categories: list[str] = []
    accounts: list[AccountingAccount]
    superseded_notes: list[SupersededNote] = []
    standards: list[AccountingStandard] = []
    entry_templates: list[EntryTemplate] = []


class MetricLibraryResponse(BaseModel):
    dictionary_id: str
    status: str
    decision_ref: str
    created: str
    standards_scope: list[str]
    domains: dict[str, str]
    report_items: list[ReportItem]
    metrics: list[MetricEntry]
    relations: list[MetricRelation]
    accounting: AccountingFoundation


class MetricDraftRequest(BaseModel):
    changes: dict[str, Any]
    operator: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=512)


class MetricActionRequest(BaseModel):
    operator: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=512)


class MetricEntryActionResponse(BaseModel):
    id: str
    metric_code: str
    version: int
    status: str


class MetricGovernanceEventLine(BaseModel):
    id: str
    metric_code: str
    version: int
    action: str
    operator: str
    reason: str
    diff: dict[str, Any]
    created_at: str | None = None


class MetricGovernanceEventListResponse(BaseModel):
    events: list[MetricGovernanceEventLine]


class SandboxDiffLine(BaseModel):
    company: str
    period: str
    current_value: str | None = None
    draft_value: str | None = None
    delta: str | None = None
    error: str | None = None


class MetricImpactResponse(BaseModel):
    metric_code: str
    draft_version: int
    downstream_metrics: list[str]
    referenced_items: list[str]
    frozen_snapshots_untouched: int
    sandbox: list[SandboxDiffLine]
