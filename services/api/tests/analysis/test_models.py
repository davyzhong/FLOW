from decimal import Decimal

import pytest
from pydantic import ValidationError

from flow_api.analysis.models import (
    AnalysisResultDraft,
    DriverContributionDraft,
    EvidenceReference,
)


def _driver(code: str, amount: str) -> DriverContributionDraft:
    return DriverContributionDraft(
        driver_code=code,
        calculation_method=f"calculate_{code}",
        contribution_amount=Decimal(amount),
        contribution_ratio=None,
        calculation_trace={"amount": amount},
    )


def test_complete_result_is_frozen_and_reconciled() -> None:
    result = AnalysisResultDraft(
        playbook_code="revenue_vpm",
        playbook_version=1,
        status="complete",
        comparison_basis="prior_year",
        impact_amount=Decimal("25.0000"),
        unit="CNY",
        drivers=(_driver("volume", "10.0000"), _driver("price", "15.0000")),
        reconciliation_difference=Decimal("0.0000"),
        reconciliation_tolerance=Decimal("0.01"),
        required_fields=("order_count", "revenue"),
        available_fields=("order_count", "revenue"),
        missing_fields=(),
        source_record_count=4,
        calculation_trace={"formula": "volume + price"},
    )

    assert sum(
        (driver.contribution_amount for driver in result.drivers), start=Decimal("0")
    ) == result.impact_amount
    with pytest.raises(ValidationError):
        result.impact_amount = Decimal("1")


def test_complete_result_rejects_duplicate_drivers_and_missing_fields() -> None:
    base = {
        "playbook_code": "revenue_vpm",
        "playbook_version": 1,
        "status": "complete",
        "comparison_basis": "prior_year",
        "impact_amount": Decimal("20"),
        "unit": "CNY",
        "drivers": (_driver("volume", "10"), _driver("volume", "10")),
        "reconciliation_difference": Decimal("0"),
        "reconciliation_tolerance": Decimal("0.01"),
        "required_fields": ("revenue",),
        "available_fields": (),
        "missing_fields": ("revenue",),
        "source_record_count": 1,
        "calculation_trace": {},
    }

    with pytest.raises(ValidationError, match="duplicate driver"):
        AnalysisResultDraft.model_validate(base)

    base["drivers"] = (_driver("volume", "20"),)
    with pytest.raises(ValidationError, match="complete result cannot have missing fields"):
        AnalysisResultDraft.model_validate(base)


def test_degraded_result_requires_reason_and_has_no_complete_bridge() -> None:
    with pytest.raises(ValidationError, match="degraded result requires"):
        AnalysisResultDraft(
            playbook_code="ar_cash_impact",
            playbook_version=1,
            status="degraded",
            comparison_basis="prior_year",
            impact_amount=Decimal("0"),
            unit="CNY",
            drivers=(),
            reconciliation_difference=Decimal("0"),
            reconciliation_tolerance=Decimal("0.01"),
            required_fields=("aging_bucket",),
            available_fields=(),
            missing_fields=("aging_bucket",),
            source_record_count=0,
            calculation_trace={},
        )


def test_public_models_reject_float_numbers() -> None:
    with pytest.raises(ValidationError, match="float values are forbidden"):
        DriverContributionDraft(
            driver_code="volume",
            calculation_method="test",
            contribution_amount=1.5,
            contribution_ratio=None,
            calculation_trace={},
        )


def test_evidence_reference_requires_a_sha256_digest_when_present() -> None:
    evidence = EvidenceReference(
        evidence_type="source_record_set",
        object_type="canonical_record_set",
        object_id="operating:analysis",
        digest="a" * 64,
        verification_trace={"row_count": 12},
    )
    assert evidence.digest == "a" * 64

    with pytest.raises(ValidationError, match="64-character"):
        EvidenceReference(
            evidence_type="source_record_set",
            object_type="canonical_record_set",
            object_id="operating:analysis",
            digest="bad",
            verification_trace={},
        )
