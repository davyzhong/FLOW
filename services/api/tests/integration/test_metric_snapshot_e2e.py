from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import MetricSnapshot, MetricValue
from flow_api.infrastructure.models.intake import ImportVersion, QualityIssue
from flow_api.intake.service import IntakeService
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotService

from .intake_service_support import NONSTANDARD, STANDARD, intake_inputs
from .metric_snapshot_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from .metric_snapshot_support import metric_session_fixture as _metric_session_fixture  # noqa: F401

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_metric_catalog(REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml")
ORACLE = json.loads(
    (REPOSITORY_ROOT / "fixtures/expected/metric_snapshots_v1.json").read_text(
        encoding="utf-8"
    )
)


def _publish_workbook(
    session: Session, path: Path, label: str
) -> tuple[IntakeService, UUID, ImportVersion]:
    intake = IntakeService(session)
    batch = intake.create_batch(label)
    stored, proposal, candidate, report = intake_inputs(path)
    source = intake.attach_source(batch.id, stored)
    mapping = intake.propose_mapping(
        source.id, proposal, actor="phase-4-metric-acceptance"
    )
    intake.confirm_mapping(mapping.id, actor="phase-4-metric-acceptance")
    version = intake.validate_import(source.id, mapping.id, candidate, report)
    for issue in session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == version.id,
            QualityIssue.severity == "warning",
        )
    ):
        intake.acknowledge_warning(
            issue.id,
            actor="phase-4-metric-acceptance",
            reason="verified against frozen metric oracle",
        )
    intake.publish_import(version.id)
    session.flush()
    return intake, batch.id, version


def _value_key(value: MetricValue) -> tuple[object, ...]:
    return (
        value.metric_definition.metric_code,
        value.comparison_type,
        value.period_id,
        value.organization_id,
        value.customer_id,
        value.customer_segment_id,
        value.logistics_product_id,
        value.region_id,
    )


def _total_values(
    values: tuple[MetricValue, ...], comparison_type: str
) -> dict[str, Decimal]:
    return {
        value.metric_definition.metric_code: Decimal(value.exact_value)
        for value in values
        if value.comparison_type == comparison_type
        and all(
            identifier is None
            for identifier in (
                value.organization_id,
                value.customer_id,
                value.customer_segment_id,
                value.logistics_product_id,
                value.region_id,
            )
        )
    }


def test_workbook_intake_produces_equivalent_governed_metric_snapshots(
    metric_session: Session,
) -> None:
    _, external_batch_id, external_import = _publish_workbook(
        metric_session, NONSTANDARD, "Phase 4 external workbook"
    )
    standard_intake, standard_batch_id, standard_import = _publish_workbook(
        metric_session, STANDARD, "Phase 4 standard workbook"
    )
    service = MetricSnapshotService()
    external_snapshot = service.create_snapshot(
        metric_session,
        batch_id=external_batch_id,
        as_of_month=202608,
        catalog=CATALOG,
    )
    standard_snapshot = service.create_snapshot(
        metric_session,
        batch_id=standard_batch_id,
        as_of_month=202608,
        catalog=CATALOG,
    )
    external_values = service.get_snapshot_values(metric_session, external_snapshot.id)
    standard_values = service.get_snapshot_values(metric_session, standard_snapshot.id)

    assert external_import.id != standard_import.id
    assert external_snapshot.import_version_id != standard_snapshot.import_version_id
    assert external_snapshot.definition_set_hash == standard_snapshot.definition_set_hash
    assert external_snapshot.fingerprint == standard_snapshot.fingerprint
    assert {
        _value_key(value): (value.exact_value, value.calculation_trace)
        for value in external_values
    } == {
        _value_key(value): (value.exact_value, value.calculation_trace)
        for value in standard_values
    }
    for comparison_type in (
        "actual_month",
        "actual_ytd",
        "prior_year_ytd",
        "trailing_12",
        "budget_ytd",
        "budget_variance_ytd",
    ):
        assert _total_values(standard_values, comparison_type) == {
            code: Decimal(exact_value)
            for code, exact_value in ORACLE[comparison_type].items()
        }

    actual_ytd_revenue = [
        value
        for value in standard_values
        if value.metric_definition.metric_code == "revenue"
        and value.comparison_type == "actual_ytd"
    ]
    revenue_total = _total_values(standard_values, "actual_ytd")["revenue"]
    organization_revenue = [
        Decimal(value.exact_value)
        for value in actual_ytd_revenue
        if value.organization_id is not None
        and value.customer_id is None
        and value.customer_segment_id is None
        and value.logistics_product_id is None
        and value.region_id is None
    ]
    assert organization_revenue
    assert sum(organization_revenue, Decimal("0")) == revenue_total

    actual_month = _total_values(standard_values, "actual_month")
    actual_ytd = _total_values(standard_values, "actual_ytd")
    assert actual_ytd["ar_balance"] == actual_month["ar_balance"]
    assert actual_ytd["dso"] == actual_month["dso"]

    totals_by_code = {
        value.metric_definition.metric_code: value
        for value in standard_values
        if value.comparison_type == "actual_ytd"
        and _value_key(value)[3:] == (None, None, None, None, None)
    }
    gross_margin = totals_by_code["gross_margin"]
    assert gross_margin.calculation_trace["dependencies"] == [
        {
            "metric_code": "gross_profit",
            "exact_value": totals_by_code["gross_profit"].exact_value,
        },
        {
            "metric_code": "revenue",
            "exact_value": totals_by_code["revenue"].exact_value,
        },
    ]
    assert Decimal(gross_margin.exact_value) == (
        Decimal(totals_by_code["gross_profit"].exact_value)
        / Decimal(totals_by_code["revenue"].exact_value)
    ).quantize(Decimal("0.000001"))

    budget_values = [
        value for value in standard_values if value.comparison_type.startswith("budget")
    ]
    assert budget_values
    assert all(value.customer_id is None for value in budget_values)
    assert all(value.region_id is None for value in budget_values)

    old_values = tuple(
        (value.id, value.exact_value, value.calculation_trace)
        for value in standard_values
    )
    stored, proposal, candidate, report = intake_inputs(NONSTANDARD)
    source = standard_intake.attach_source(standard_batch_id, stored)
    mapping = standard_intake.propose_mapping(
        source.id, proposal, actor="phase-4-metric-acceptance"
    )
    correction = standard_intake.create_correction(
        source.id, mapping.id, candidate, report
    )
    assert correction.id != standard_import.id
    for issue in metric_session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == correction.id,
            QualityIssue.severity == "warning",
        )
    ):
        standard_intake.acknowledge_warning(
            issue.id,
            actor="phase-4-metric-acceptance",
            reason="verified correction",
        )
    standard_intake.publish_import(correction.id)
    corrected_snapshot = service.create_snapshot(
        metric_session,
        batch_id=standard_batch_id,
        as_of_month=202608,
        catalog=CATALOG,
    )

    assert corrected_snapshot.version == 2
    assert corrected_snapshot.id != standard_snapshot.id
    assert corrected_snapshot.fingerprint == standard_snapshot.fingerprint
    assert tuple(
        (value.id, value.exact_value, value.calculation_trace)
        for value in service.get_snapshot_values(metric_session, standard_snapshot.id)
    ) == old_values
    assert (
        metric_session.scalar(select(func.count()).select_from(MetricSnapshot)) == 3
    )
