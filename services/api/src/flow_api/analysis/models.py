from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _reject_float(value: object) -> object:
    if isinstance(value, float):
        raise ValueError("float values are forbidden; use Decimal or decimal strings")
    return value


StrictDecimal = Annotated[Decimal, BeforeValidator(_reject_float)]
AnalysisStatus = Literal["complete", "degraded", "not_applicable"]
ComparisonBasis = Literal["prior_year", "budget"]
DegradationCode = Literal[
    "missing_required_field",
    "missing_comparison_window",
    "zero_denominator",
    "unmatched_mix_cell",
    "unsupported_grain",
    "insufficient_periods_for_persistence",
    "source_total_mismatch",
    "upstream_result_degraded",
]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DriverContributionDraft(FrozenModel):
    driver_code: str = Field(min_length=1, max_length=128)
    calculation_method: str = Field(min_length=1)
    contribution_amount: StrictDecimal
    contribution_ratio: StrictDecimal | None
    calculation_trace: dict[str, Any]


class EvidenceReference(FrozenModel):
    evidence_type: Literal[
        "metric_value", "calculation", "source_record_set", "lineage", "invariant"
    ]
    object_type: Literal[
        "metric",
        "analysis_run",
        "analysis_result",
        "canonical_record_set",
        "lineage",
        "invariant",
    ]
    object_id: str = Field(min_length=1, max_length=256)
    digest: str | None = None
    verification_trace: dict[str, Any]

    @model_validator(mode="after")
    def validate_digest(self) -> EvidenceReference:
        if self.digest is not None and len(self.digest) != 64:
            raise ValueError("evidence digest must be a 64-character sha256")
        return self


class AnalysisResultDraft(FrozenModel):
    playbook_code: str = Field(min_length=1, max_length=128)
    playbook_version: int = Field(gt=0)
    status: AnalysisStatus
    comparison_basis: ComparisonBasis
    impact_amount: StrictDecimal
    unit: Literal["CNY", "ratio", "day", "order", "unit"]
    drivers: tuple[DriverContributionDraft, ...]
    reconciliation_difference: StrictDecimal
    reconciliation_tolerance: StrictDecimal = Field(ge=0)
    required_fields: tuple[str, ...]
    available_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]
    source_record_count: int = Field(ge=0)
    calculation_trace: dict[str, Any]
    degradation_code: DegradationCode | None = None
    degradation_message: str | None = None

    @model_validator(mode="after")
    def validate_result_state(self) -> AnalysisResultDraft:
        driver_codes = [driver.driver_code for driver in self.drivers]
        if len(driver_codes) != len(set(driver_codes)):
            raise ValueError("result has a duplicate driver code")
        if self.status == "complete":
            if self.missing_fields:
                raise ValueError("complete result cannot have missing fields")
            if self.degradation_code is not None or self.degradation_message is not None:
                raise ValueError("complete result cannot have degradation details")
        elif self.status == "degraded":
            if self.degradation_code is None or not self.degradation_message:
                raise ValueError("degraded result requires a code and message")
            if self.drivers:
                raise ValueError("degraded result cannot expose a complete driver bridge")
        return self


class ScoreComponentDraft(FrozenModel):
    component_code: Literal[
        "materiality", "persistence", "evidence_completeness", "management_relevance"
    ]
    raw_value: StrictDecimal
    normalized_score: StrictDecimal = Field(ge=0, le=100)
    weight: StrictDecimal = Field(ge=0, le=1)
    weighted_score: StrictDecimal = Field(ge=0, le=100)
    calculation_trace: dict[str, Any]


class FindingDraft(FrozenModel):
    finding_type: str = Field(min_length=1, max_length=128)
    playbook_code: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    fact_statement: str = Field(min_length=1)
    business_meaning: str = Field(min_length=1)
    comparison_basis: ComparisonBasis
    impact_amount: StrictDecimal
    confidence: StrictDecimal = Field(ge=0, le=1)
    total_score: StrictDecimal = Field(ge=0, le=100)
    policy_version: str = Field(min_length=1, max_length=128)
    fingerprint: str = Field(min_length=64, max_length=64)
    score_components: tuple[ScoreComponentDraft, ...]
    evidence: tuple[EvidenceReference, ...]
    qualification_trace: dict[str, Any]


__all__ = [
    "AnalysisResultDraft",
    "AnalysisStatus",
    "ComparisonBasis",
    "DegradationCode",
    "DriverContributionDraft",
    "EvidenceReference",
    "FindingDraft",
    "ScoreComponentDraft",
    "StrictDecimal",
]
