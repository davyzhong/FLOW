from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from flow_api.analysis.policy import AnalysisPolicy, load_analysis_policy

POLICY_PATH = Path("config/analysis/flow-logistics-v1.yaml")


def test_committed_policy_has_stable_identity_and_complete_weights() -> None:
    loaded = load_analysis_policy(POLICY_PATH)

    assert loaded.policy.policy_id == "flow.analysis.logistics.v1"
    assert loaded.policy.engine_version == "flow-analysis/1"
    assert loaded.policy.reconciliation_tolerance == Decimal("0.01")
    assert sum(loaded.policy.ranking_weights.values(), start=Decimal("0")) == Decimal("1")
    assert loaded.policy.required_evidence == (
        "metric_value",
        "calculation",
        "source_record_set",
        "lineage",
        "invariant",
    )
    assert len(loaded.policy_hash) == 64


def test_policy_rejects_float_and_invalid_weight_total() -> None:
    payload = {
        "policy_id": "test",
        "engine_version": "test/1",
        "reconciliation_tolerance": "0.01",
        "qualification_materiality": {"profit": "10"},
        "high_materiality_amount": {"profit": "100"},
        "persistence_periods": 3,
        "ranking_weights": {
            "materiality": "0.5",
            "persistence": "0.2",
            "evidence_completeness": "0.2",
            "management_relevance": "0.2",
        },
        "management_relevance": {"profit": "100"},
        "required_evidence": ["metric_value"],
    }
    with pytest.raises(ValidationError, match="sum to 1"):
        AnalysisPolicy.model_validate(payload)

    payload["ranking_weights"]["materiality"] = 0.4
    with pytest.raises(ValidationError, match="float values are forbidden"):
        AnalysisPolicy.model_validate(payload)
