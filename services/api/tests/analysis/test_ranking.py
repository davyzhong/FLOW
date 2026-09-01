from decimal import Decimal

from flow_api.analysis.findings import calculate_score_components, rank_findings
from flow_api.analysis.models import FindingDraft

from .test_finding_qualification import _evidence, _policy


def test_score_components_are_exact_and_retain_policy_inputs() -> None:
    components = calculate_score_components(
        finding_type="gross_profit_deterioration",
        impact_amount=Decimal("-40"),
        persistence_flags=(True, True, False),
        verified_evidence_count=5,
        required_evidence_count=5,
        policy=_policy(),
    )
    by_code = {component.component_code: component for component in components}

    assert by_code["materiality"].normalized_score == Decimal("40.000000")
    assert by_code["materiality"].weighted_score == Decimal("16.000000")
    assert by_code["persistence"].normalized_score == Decimal("66.666667")
    assert by_code["evidence_completeness"].normalized_score == Decimal("100.000000")
    assert by_code["management_relevance"].normalized_score == Decimal("90.000000")
    assert by_code["materiality"].calculation_trace["high_materiality_amount"] == "100"


def test_point_in_time_persistence_is_neutral() -> None:
    components = calculate_score_components(
        finding_type="gross_profit_deterioration",
        impact_amount=Decimal("-40"),
        persistence_flags=(),
        verified_evidence_count=5,
        required_evidence_count=5,
        policy=_policy(),
    )
    persistence = next(
        item for item in components if item.component_code == "persistence"
    )
    assert persistence.normalized_score == Decimal("50.000000")
    assert persistence.calculation_trace["policy"] == "point_in_time_neutral"


def _finding(*, score: str, impact: str, fingerprint: str) -> FindingDraft:
    return FindingDraft(
        finding_type="gross_profit_deterioration",
        playbook_code="gross_profit_bridge",
        title="毛利下降",
        fact_statement="毛利同比下降",
        business_meaning="盈利空间收窄",
        comparison_basis="prior_year",
        impact_amount=Decimal(impact),
        confidence=Decimal("1"),
        total_score=Decimal(score),
        policy_version="test",
        fingerprint=fingerprint * 64,
        score_components=(),
        evidence=_evidence(),
        qualification_trace={},
    )


def test_ranking_uses_score_then_absolute_impact_then_fingerprint() -> None:
    ranked = rank_findings(
        (
            _finding(score="80", impact="-20", fingerprint="c"),
            _finding(score="90", impact="-10", fingerprint="b"),
            _finding(score="80", impact="-30", fingerprint="d"),
            _finding(score="80", impact="-30", fingerprint="a"),
        )
    )
    assert [item.fingerprint[0] for item in ranked] == ["b", "a", "d", "c"]
