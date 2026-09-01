"""Typed read and write models for the Investigation workbench."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class InvestigationIdentity(StrictModel):
    finding_id: str
    batch_id: str
    metric_snapshot_id: str
    analysis_run_id: str


class FindingContext(StrictModel):
    finding_id: str
    finding_type: str | None
    title: str
    status: str
    impact_amount: str
    unit: str
    confidence: str
    business_meaning: str | None
    fact_statement: str | None
    comparison_basis: str | None
    total_score: str | None
    policy_version: str | None
    created_at: str


class AnalysisResultContext(StrictModel):
    analysis_result_id: str
    playbook_code: str
    playbook_version: int
    status: str
    comparison_basis: str
    impact_amount: str
    unit: str
    reconciliation_difference: str
    reconciliation_tolerance: str
    source_record_count: int
    degradation_code: str | None
    degradation_message: str | None


class MetricContext(StrictModel):
    metric_code: str | None
    metric_name: str | None
    business_definition: str | None
    formula: str | None
    unit: str | None
    definition_version: int | None
    engine_version: str
    policy_id: str
    policy_set_hash: str


class DriverLine(StrictModel):
    position: int
    driver_code: str
    calculation_method: str | None
    contribution_amount: str
    contribution_ratio: str | None


class EvidenceLine(StrictModel):
    evidence_id: str
    status: str
    evidence_type: str
    object_type: str
    object_id: str
    note: str | None
    evidence_digest: str | None


class ReviewLine(StrictModel):
    sequence: int
    reviewer: str
    decision: str
    comment: str | None
    created_at: str


class QualityIssueLine(StrictModel):
    severity: str
    code: str
    message: str
    acknowledged: bool


class ReconciliationLine(StrictModel):
    reconciliation_code: str
    passed: bool
    expected_value: str | None
    actual_value: str | None


class ConclusionState(StrictModel):
    exists: bool
    verified_facts: str = ""
    analysis_judgment: str = ""
    open_questions: str = ""
    recommendation: str = ""


class SourceRecordLine(StrictModel):
    fact_id: str
    month_key: int
    labels: dict[str, str]
    values: dict[str, str]
    source_file_name: str
    sheet_name: str
    source_row: int
    source_column: str


class InvestigationContext(StrictModel):
    identity: InvestigationIdentity
    finding: FindingContext
    result: AnalysisResultContext | None
    metric: MetricContext
    drivers: tuple[DriverLine, ...]
    evidence: tuple[EvidenceLine, ...]
    reviews: tuple[ReviewLine, ...]
    quality_issues: tuple[QualityIssueLine, ...]
    reconciliations: tuple[ReconciliationLine, ...]
    conclusion: ConclusionState
    source_records: tuple[SourceRecordLine, ...]
    eligibility_blockers: tuple[str, ...]


class EvidenceDecisionRequest(StrictModel):
    decision: str
    reviewer: str = Field(min_length=1)
    comment: str | None = None


class ConclusionUpsertRequest(StrictModel):
    verified_facts: str = Field(min_length=1)
    analysis_judgment: str = Field(min_length=1)
    open_questions: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    editor: str = Field(min_length=1)


class FindingTransitionRequest(StrictModel):
    decision: str
    reviewer: str = Field(min_length=1)
    comment: str | None = None


class MutationAcknowledgement(StrictModel):
    finding_id: str
    status: str
    review_sequence: int
    decision: str


__all__ = [
    "AnalysisResultContext",
    "ConclusionState",
    "ConclusionUpsertRequest",
    "DriverLine",
    "EvidenceDecisionRequest",
    "EvidenceLine",
    "FindingContext",
    "FindingTransitionRequest",
    "InvestigationContext",
    "InvestigationIdentity",
    "MetricContext",
    "MutationAcknowledgement",
    "QualityIssueLine",
    "ReconciliationLine",
    "ReviewLine",
    "SourceRecordLine",
    "StrictModel",
]
