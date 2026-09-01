from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.service import DashboardFilterError, DashboardService
from flow_api.infrastructure.models.analytics import MetricSnapshot

from .analysis_run_support import (
    REPOSITORY_ROOT,
    publish_analysis_run,
)
from .analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from .analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)

ORACLE = Path(REPOSITORY_ROOT) / "fixtures/expected/dashboard_overview_v1.json"


def test_core_projection_matches_governed_context_status_filters_and_cards(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)
    expected = json.loads(ORACLE.read_text(encoding="utf-8"))

    core = DashboardService().get_core(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
        now=datetime(2026, 9, 1, tzinfo=UTC),
    )

    context = core.context.model_dump(mode="json")
    snapshot = analysis_session.get(MetricSnapshot, run.metric_snapshot_id)
    assert snapshot is not None
    assert core.context.analysis_run_id == run.id
    assert core.context.metric_snapshot_id == snapshot.id
    assert core.context.import_version_id == run.import_version_id
    assert core.context.batch_id == snapshot.batch_id
    context.pop("generated_at")
    expected_context = dict(expected["context"])
    expected_context.pop("generated_at")
    for identity in (
        "analysis_run_id",
        "metric_snapshot_id",
        "import_version_id",
        "batch_id",
    ):
        context.pop(identity)
        expected_context.pop(identity)
    assert context == expected_context
    assert core.data_status.model_dump(mode="json") == expected["data_status"]
    assert core.filter_options.model_dump(mode="json") == expected["filter_options"]
    assert [card.model_dump(mode="json") for card in core.metric_cards] == expected[
        "metric_cards"
    ]


def test_ytd_and_supported_dimension_filters_use_only_published_grains(
    analysis_session: Session,
) -> None:
    publish_analysis_run(analysis_session)
    service = DashboardService()
    total_ytd = service.get_core(
        analysis_session,
        filters=ActiveFilters(period_view="ytd", is_total_scope=True),
        now=datetime(2026, 9, 1, tzinfo=UTC),
    )
    revenue = next(card for card in total_ytd.metric_cards if card.metric_code == "revenue")
    assert str(revenue.primary.exact_value) == "17320164.2962"
    assert str(revenue.yoy.exact_value) == "0.098421"

    initial = service.get_core(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
        now=datetime(2026, 9, 1, tzinfo=UTC),
    )
    product_id = initial.filter_options.dimensions[2].options[0].id
    product = service.get_core(
        analysis_session,
        filters=ActiveFilters(
            period_view="month",
            logistics_product_id=product_id,
            is_total_scope=False,
        ),
        now=datetime(2026, 9, 1, tzinfo=UTC),
    )
    assert next(
        card for card in product.metric_cards if card.metric_code == "revenue"
    ).primary.status == "available"
    assert next(
        card for card in product.metric_cards if card.metric_code == "operating_profit"
    ).primary.status == "unavailable"


def test_unsupported_filter_combinations_are_rejected(analysis_session: Session) -> None:
    publish_analysis_run(analysis_session)
    service = DashboardService()
    total = service.get_core(
        analysis_session,
        filters=ActiveFilters(period_view="month", is_total_scope=True),
        now=datetime(2026, 9, 1, tzinfo=UTC),
    )
    organization_id = total.filter_options.dimensions[0].options[0].id
    product_id = total.filter_options.dimensions[2].options[0].id

    with pytest.raises(DashboardFilterError) as unsupported:
        service.get_core(
            analysis_session,
            filters=ActiveFilters(
                period_view="month",
                organization_id=organization_id,
                logistics_product_id=product_id,
                is_total_scope=False,
            ),
            now=datetime(2026, 9, 1, tzinfo=UTC),
        )

    assert unsupported.value.code == "unsupported_filter_combination"
