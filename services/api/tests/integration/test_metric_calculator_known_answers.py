from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from flow_api.metrics.calculator import MetricCalculator
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.grain import MetricGrain
from flow_api.metrics.repositories import MetricSourceRepository

from .intake_service_support import (
    intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .test_metric_source_repository import _publish_reference

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml"
ORACLE_PATH = REPOSITORY_ROOT / "fixtures/expected/metric_snapshots_v1.json"


def _total_values(result, comparison_type: str) -> dict[str, Decimal]:
    return {
        value.metric_code: value.exact_value
        for value in result.values
        if value.comparison_type == comparison_type and value.grain == MetricGrain()
    }


def test_calculator_matches_independent_total_grain_oracle(
    intake_session: Session,
) -> None:
    _, batch, _ = _publish_reference(intake_session)
    repository = MetricSourceRepository()
    source = repository.get_published_source(intake_session, batch.id)
    catalog = load_metric_catalog(CATALOG_PATH)
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))

    result = MetricCalculator(intake_session, repository).calculate(
        source, catalog, as_of_month=202608
    )

    for comparison_type in (
        "actual_month",
        "actual_ytd",
        "prior_year_ytd",
        "trailing_12",
        "budget_ytd",
        "budget_variance_ytd",
    ):
        assert _total_values(result, comparison_type) == {
            code: Decimal(value) for code, value in oracle[comparison_type].items()
        }
    assert result.definition_set_hash
    assert len(result.fingerprint) == 64
    assert result == MetricCalculator(intake_session, repository).calculate(
        source, catalog, as_of_month=202608
    )


def test_calculator_preserves_slice_and_dependency_invariants(
    intake_session: Session,
) -> None:
    _, batch, _ = _publish_reference(intake_session)
    repository = MetricSourceRepository()
    source = repository.get_published_source(intake_session, batch.id)
    result = MetricCalculator(intake_session, repository).calculate(
        source, load_metric_catalog(CATALOG_PATH), as_of_month=202608
    )

    revenue_values = [
        value
        for value in result.values
        if value.metric_code == "revenue" and value.comparison_type == "actual_ytd"
    ]
    total = next(value for value in revenue_values if value.grain == MetricGrain())
    organizations = [
        value for value in revenue_values if value.grain.dimensions == ("organization",)
    ]
    assert organizations
    assert sum((value.exact_value for value in organizations), Decimal("0")) == total.exact_value

    gross_profit = next(
        value
        for value in result.values
        if value.metric_code == "gross_profit"
        and value.comparison_type == "actual_ytd"
        and value.grain == MetricGrain()
    )
    assert gross_profit.dependency_values == (
        ("revenue", Decimal("17320164.2962")),
        ("direct_cost", Decimal("11629044.9986")),
    )
    assert gross_profit.source_fact_count > 0

    budget_values = [
        value
        for value in result.values
        if value.comparison_type == "budget_ytd"
    ]
    assert budget_values
    assert all("customer" not in value.grain.dimensions for value in budget_values)
    assert all("region" not in value.grain.dimensions for value in budget_values)


def test_calculator_materializes_every_allowed_actual_dimension(
    intake_session: Session,
) -> None:
    _, batch, _ = _publish_reference(intake_session)
    repository = MetricSourceRepository()
    source = repository.get_published_source(intake_session, batch.id)
    catalog = load_metric_catalog(CATALOG_PATH)
    result = MetricCalculator(intake_session, repository).calculate(
        source, catalog, as_of_month=202608
    )

    for metric in catalog.metrics:
        actual_ytd = [
            value
            for value in result.values
            if value.metric_code == metric.metric_code
            and value.comparison_type == "actual_ytd"
        ]
        assert {value.grain.dimensions for value in actual_ytd} == set(
            metric.allowed_dimension_sets
        )

    gross_margins = {
        value.grain: value.exact_value
        for value in result.values
        if value.metric_code == "gross_margin"
        and value.comparison_type == "actual_ytd"
    }
    revenues = {
        value.grain: value.exact_value
        for value in result.values
        if value.metric_code == "revenue" and value.comparison_type == "actual_ytd"
    }
    gross_profits = {
        value.grain: value.exact_value
        for value in result.values
        if value.metric_code == "gross_profit"
        and value.comparison_type == "actual_ytd"
    }
    for grain, margin in gross_margins.items():
        assert margin == (gross_profits[grain] / revenues[grain]).quantize(
            Decimal("0.000001")
        )
