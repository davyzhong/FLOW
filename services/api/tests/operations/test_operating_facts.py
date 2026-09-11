"""O2 经营事实中间层：期间、口径与来源边界测试。"""

from __future__ import annotations

from pathlib import Path

from flow_api.operations.engine import (
    build_public_operating_overview,
    list_public_operating_periods,
    operating_fact_metrics_for_period,
)
from flow_api.operations.facts import (
    facts_for_period,
    load_cainiao_operating_facts,
    previous_comparable_period,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CAINIAO_METRICS = REPO_ROOT / "docs/implementation/p5/cainiao_operating_metrics.yaml"


def test_loader_normalizes_source_and_period_contract() -> None:
    facts = load_cainiao_operating_facts(CAINIAO_METRICS, repo_root=REPO_ROOT)

    international = next(
        fact
        for fact in facts
        if fact.metric_code == "international_parcels"
        and fact.period_label == "Q1FY2024"
    )
    assert international.numeric_value == 439
    assert international.unit == "百万件"
    assert international.period_type == "fiscal_quarter"
    assert international.assurance == "unaudited"
    assert international.is_stub is True
    assert international.source_page == "22"
    assert international.source_sha256 == (
        "3e2c367958eacf3bb50c165204a1093383381f5cdb9d8af506636b880b54b13c"
    )


def test_period_filter_never_spreads_annual_facts_into_quarter() -> None:
    facts = load_cainiao_operating_facts(CAINIAO_METRICS, repo_root=REPO_ROOT)

    quarter = facts_for_period(facts, "Q1FY2024")
    assert quarter
    assert {fact.period_label for fact in quarter} == {"Q1FY2024"}
    assert all(fact.period_type == "fiscal_quarter" for fact in quarter)
    assert not any(fact.period_label == "FY2023" for fact in quarter)


def test_comparable_period_preserves_frequency() -> None:
    assert previous_comparable_period("FY2023") == "FY2022"
    assert previous_comparable_period("Q1FY2024") == "Q1FY2023"
    assert previous_comparable_period("2023-06-30") is None


def test_annual_fact_cards_use_only_previous_annual_basis() -> None:
    facts = load_cainiao_operating_facts(CAINIAO_METRICS, repo_root=REPO_ROOT)

    grouped = operating_fact_metrics_for_period(facts, selected_period="FY2023")
    volume = next(
        metric
        for metric in grouped["growth_quality"]
        if metric.entry_id == "international_parcels"
    )

    assert volume.value == "1519"
    assert "FY2022" in volume.basis and "1679" in volume.basis
    assert "Q1" not in volume.basis
    assert volume.source == "operating_fact"
    assert volume.source_ref.endswith("Cainiao_application_proof_20230926.pdf")
    assert len(volume.source_sha256) == 64
    assert volume.source_page == "22"


def test_quarter_fact_cards_use_same_quarter_and_show_assurance() -> None:
    facts = load_cainiao_operating_facts(CAINIAO_METRICS, repo_root=REPO_ROOT)

    grouped = operating_fact_metrics_for_period(facts, selected_period="Q1FY2024")
    volume = next(
        metric
        for metric in grouped["growth_quality"]
        if metric.entry_id == "international_parcels"
    )

    assert volume.value == "439"
    assert "Q1FY2023" in volume.basis and "347" in volume.basis
    assert volume.basis.startswith("Q1FY2023 ")
    assert volume.period_type == "fiscal_quarter"
    assert volume.assurance == "unaudited"


def test_public_quarter_overview_is_reachable_without_statement_report() -> None:
    overview = build_public_operating_overview(
        stock_code="CAINIAO", selected_period="Q1FY2024"
    )
    by_id = {theme.theme_id: theme for theme in overview.themes}

    assert len(by_id) == 6
    growth = {metric.entry_id: metric for metric in by_id["growth_quality"].metrics}
    assert growth["international_parcels"].value == "439"
    assert growth["international_parcels"].basis.startswith("Q1FY2023 347")
    assert by_id["revenue_structure"].status == "not_applicable"
    assert not any(
        metric.entry_id.startswith("business_line_share")
        for metric in by_id["revenue_structure"].metrics
    )


def test_public_period_catalog_exposes_real_periods_only() -> None:
    periods = list_public_operating_periods()
    cainiao = [item for item in periods if item.stock_code == "CAINIAO"]

    assert {item.period_label for item in cainiao} == {
        "FY2021",
        "FY2022",
        "FY2023",
        "Q1FY2023",
        "Q1FY2024",
    }
    assert all("month" not in item.period_label.lower() for item in cainiao)
