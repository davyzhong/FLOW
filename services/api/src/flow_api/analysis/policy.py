from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import Field, model_validator

from flow_api.analysis.models import FrozenModel, StrictDecimal


class AnalysisPolicy(FrozenModel):
    policy_id: str = Field(min_length=1, max_length=128)
    engine_version: str = Field(min_length=1, max_length=128)
    reconciliation_tolerance: StrictDecimal = Field(gt=0)
    qualification_materiality: dict[str, StrictDecimal]
    high_materiality_amount: dict[str, StrictDecimal]
    persistence_periods: int = Field(gt=0)
    ranking_weights: dict[str, StrictDecimal]
    management_relevance: dict[str, StrictDecimal]
    required_evidence: tuple[str, ...]

    @model_validator(mode="after")
    def validate_policy(self) -> AnalysisPolicy:
        expected_weights = {
            "materiality",
            "persistence",
            "evidence_completeness",
            "management_relevance",
        }
        if set(self.ranking_weights) != expected_weights:
            raise ValueError("ranking weights must define all four components")
        if sum(self.ranking_weights.values(), start=Decimal("0")) != Decimal("1"):
            raise ValueError("ranking weights must sum to 1")
        if not self.required_evidence or len(self.required_evidence) != len(
            set(self.required_evidence)
        ):
            raise ValueError("required evidence must be non-empty and unique")
        if any(value <= 0 for value in self.qualification_materiality.values()):
            raise ValueError("qualification materiality must be positive")
        if any(value <= 0 for value in self.high_materiality_amount.values()):
            raise ValueError("high materiality amounts must be positive")
        if any(value < 0 or value > 100 for value in self.management_relevance.values()):
            raise ValueError("management relevance must be between 0 and 100")
        return self


class LoadedAnalysisPolicy(FrozenModel):
    policy: AnalysisPolicy
    policy_hash: str = Field(min_length=64, max_length=64)


def load_analysis_policy(path: Path) -> LoadedAnalysisPolicy:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("analysis policy root must be a mapping")
    policy = AnalysisPolicy.model_validate(payload)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    policy_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return LoadedAnalysisPolicy(policy=policy, policy_hash=policy_hash)


__all__ = ["AnalysisPolicy", "LoadedAnalysisPolicy", "load_analysis_policy"]
