from decimal import Decimal

from flow_api.analysis.bridges import RevenueMixCell, calculate_revenue_vpm
from flow_api.analysis.findings import qualify_finding
from flow_api.analysis.models import EvidenceReference
from flow_api.analysis.playbooks import ProfitBridgeInput, calculate_gross_profit_bridge
from flow_api.analysis.policy import AnalysisPolicy


def _policy() -> AnalysisPolicy:
    return AnalysisPolicy(
        policy_id="flow.analysis.test.v1",
        engine_version="flow-analysis/1",
        reconciliation_tolerance=Decimal("0.01"),
        qualification_materiality={"gross_profit_deterioration": Decimal("10")},
        high_materiality_amount={"gross_profit_deterioration": Decimal("100")},
        persistence_periods=3,
        ranking_weights={
            "materiality": Decimal("0.4"),
            "persistence": Decimal("0.2"),
            "evidence_completeness": Decimal("0.2"),
            "management_relevance": Decimal("0.2"),
        },
        management_relevance={"gross_profit_deterioration": Decimal("90")},
        required_evidence=(
            "metric_value",
            "calculation",
            "source_record_set",
            "lineage",
            "invariant",
        ),
    )


def _result():
    revenue = calculate_revenue_vpm(
        (
            RevenueMixCell(
                cell_code="A",
                comparison_orders=Decimal("10"),
                comparison_revenue=Decimal("100"),
                analysis_orders=Decimal("12"),
                analysis_revenue=Decimal("132"),
                source_record_count=2,
            ),
            RevenueMixCell(
                cell_code="B",
                comparison_orders=Decimal("10"),
                comparison_revenue=Decimal("200"),
                analysis_orders=Decimal("8"),
                analysis_revenue=Decimal("144"),
                source_record_count=2,
            ),
        ),
        tolerance=Decimal("0.01"),
    )
    return calculate_gross_profit_bridge(
        ProfitBridgeInput(
            revenue_result=revenue,
            comparison_warehousing_cost=Decimal("50"),
            analysis_warehousing_cost=Decimal("55"),
            comparison_transportation_cost=Decimal("60"),
            analysis_transportation_cost=Decimal("70"),
            comparison_other_direct_cost=Decimal("10"),
            analysis_other_direct_cost=Decimal("11"),
            comparison_gross_profit=Decimal("180"),
            analysis_gross_profit=Decimal("140"),
            comparison_operating_expense=Decimal("30"),
            analysis_operating_expense=Decimal("35"),
            comparison_operating_profit=Decimal("150"),
            analysis_operating_profit=Decimal("105"),
            source_record_count=12,
        ),
        tolerance=Decimal("0.01"),
    )


def _evidence() -> tuple[EvidenceReference, ...]:
    return tuple(
        EvidenceReference(
            evidence_type=evidence_type,
            object_type=(
                "metric"
                if evidence_type == "metric_value"
                else "canonical_record_set"
                if evidence_type == "source_record_set"
                else "lineage"
                if evidence_type == "lineage"
                else "invariant"
                if evidence_type == "invariant"
                else "analysis_result"
            ),
            object_id=f"test:{evidence_type}",
            digest="a" * 64 if evidence_type == "source_record_set" else None,
            verification_trace={"verified": True},
        )
        for evidence_type in _policy().required_evidence
    )


def test_complete_supported_result_qualifies_with_noncausal_wording() -> None:
    outcome = qualify_finding(
        result=_result(),
        finding_type="gross_profit_deterioration",
        policy=_policy(),
        evidence=_evidence(),
        persistence_flags=(True, True, False),
        run_identity="run-1",
        expected_run_identity="run-1",
        existing_fingerprints=frozenset(),
    )

    assert outcome.suppression_reasons == ()
    assert outcome.finding is not None
    assert outcome.finding.impact_amount == Decimal("-40.0000")
    assert "毛利" in outcome.finding.title
    assert "运输成本" in outcome.finding.fact_statement
    assert all(
        forbidden not in outcome.finding.fact_statement
        for forbidden in ("导致", "承运商涨价", "客户经营恶化")
    )
    assert {component.component_code for component in outcome.finding.score_components} == {
        "materiality",
        "persistence",
        "evidence_completeness",
        "management_relevance",
    }
    assert len(outcome.finding.fingerprint) == 64


def test_hard_gates_suppress_degraded_missing_evidence_and_wrong_identity() -> None:
    degraded = _result().model_copy(
        update={
            "status": "degraded",
            "drivers": (),
            "missing_fields": ("revenue_vpm",),
            "degradation_code": "upstream_result_degraded",
            "degradation_message": "missing",
        }
    )
    outcome = qualify_finding(
        result=degraded,
        finding_type="gross_profit_deterioration",
        policy=_policy(),
        evidence=_evidence()[:-1],
        persistence_flags=(True,),
        run_identity="run-1",
        expected_run_identity="run-2",
        existing_fingerprints=frozenset(),
    )

    assert outcome.finding is None
    assert set(outcome.suppression_reasons) == {
        "result_not_complete",
        "evidence_incomplete",
        "run_identity_mismatch",
    }


def test_materiality_direction_and_duplicate_fingerprint_are_hard_gates() -> None:
    policy = _policy().model_copy(
        update={"qualification_materiality": {"gross_profit_deterioration": Decimal("50")}}
    )
    below = qualify_finding(
        result=_result(),
        finding_type="gross_profit_deterioration",
        policy=policy,
        evidence=_evidence(),
        persistence_flags=(),
        run_identity="run-1",
        expected_run_identity="run-1",
        existing_fingerprints=frozenset(),
    )
    assert below.finding is None
    assert below.suppression_reasons == ("below_materiality",)

    first = qualify_finding(
        result=_result(),
        finding_type="gross_profit_deterioration",
        policy=_policy(),
        evidence=_evidence(),
        persistence_flags=(),
        run_identity="run-1",
        expected_run_identity="run-1",
        existing_fingerprints=frozenset(),
    )
    assert first.finding is not None
    duplicate = qualify_finding(
        result=_result(),
        finding_type="gross_profit_deterioration",
        policy=_policy(),
        evidence=_evidence(),
        persistence_flags=(),
        run_identity="run-1",
        expected_run_identity="run-1",
        existing_fingerprints=frozenset({first.finding.fingerprint}),
    )
    assert duplicate.finding is None
    assert duplicate.suppression_reasons == ("duplicate_fingerprint",)
