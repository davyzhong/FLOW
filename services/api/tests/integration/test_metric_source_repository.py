from __future__ import annotations

import importlib
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.intake import QualityIssue, ReconciliationResult
from flow_api.intake.service import IntakeService

from .intake_service_support import STANDARD, intake_inputs
from .intake_service_support import (
    intake_session_fixture as _intake_session_fixture,  # noqa: F401
)


def setup_module() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def _repository_module():
    try:
        return importlib.import_module("flow_api.metrics.repositories")
    except ModuleNotFoundError:
        pytest.fail("flow_api.metrics.repositories does not exist")


def _publish_reference(session: Session):
    stored, proposal, candidate, report = intake_inputs()
    service = IntakeService(session)
    batch = service.create_batch("Metric source repository")
    source = service.attach_source(batch.id, stored)
    mapping = service.propose_mapping(source.id, proposal)
    version = service.validate_import(source.id, mapping.id, candidate, report)
    for issue in session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == version.id,
            QualityIssue.severity == "warning",
        )
    ):
        service.acknowledge_warning(issue.id, actor="finance.bp", reason="verified")
    service.publish_import(version.id)
    session.flush()
    return service, batch, version


def test_repository_reads_only_the_active_published_import(
    intake_session: Session,
) -> None:
    module = _repository_module()
    service, batch, published = _publish_reference(intake_session)

    stored, proposal, candidate, report = intake_inputs(STANDARD)
    source = service.attach_source(batch.id, stored)
    mapping = service.propose_mapping(source.id, proposal)
    unpublished = service.create_correction(source.id, mapping.id, candidate, report)
    intake_session.flush()

    repository = module.MetricSourceRepository()
    metric_source = repository.get_published_source(intake_session, batch.id)
    operating = repository.operating_rows(intake_session, metric_source)
    financial = repository.financial_rows(intake_session, metric_source)
    budgets = repository.budget_rows(intake_session, metric_source)
    ar_rows = repository.ar_rows(intake_session, metric_source)

    assert metric_source.import_version_id == published.id
    assert metric_source.import_version_id != unpublished.id
    assert metric_source.analysis_start_month == 202509
    assert metric_source.analysis_end_month == 202608
    assert metric_source.comparison_start_month == 202409
    assert metric_source.comparison_end_month == 202508
    assert metric_source.actual_scenario_code == "ACTUAL"
    assert metric_source.budget_scenario_code == "BUDGET_FY26_V1"
    assert len(operating) == 3072
    assert len(financial) == 432
    assert len(budgets) == 120
    assert len(ar_rows) == 1920
    assert all(row.import_version_id == published.id for row in operating)
    assert all(row.import_version_id == published.id for row in financial)
    assert all(row.import_version_id == published.id for row in budgets)
    assert all(row.import_version_id == published.id for row in ar_rows)
    assert isinstance(operating[0].revenue, Decimal)
    assert operating == tuple(sorted(operating, key=lambda row: (row.month_key, row.fact_id)))


def test_repository_rejects_missing_or_no_longer_eligible_publication(
    intake_session: Session,
) -> None:
    module = _repository_module()
    repository = module.MetricSourceRepository()
    service = IntakeService(intake_session)
    draft = service.create_batch("No publication")

    with pytest.raises(module.MetricSourceUnavailableError) as missing:
        repository.get_published_source(intake_session, draft.id)
    assert missing.value.code == "no_published_import"

    _, batch, published = _publish_reference(intake_session)
    reconciliation = intake_session.scalar(
        select(ReconciliationResult).where(
            ReconciliationResult.import_version_id == published.id
        )
    )
    assert reconciliation is not None
    reconciliation.passed = False
    intake_session.flush()

    with pytest.raises(module.MetricSourceUnavailableError) as failed_reconciliation:
        repository.get_published_source(intake_session, batch.id)
    assert failed_reconciliation.value.code == "failed_reconciliation"

    reconciliation.passed = True
    issue = QualityIssue(
        import_version_id=published.id,
        severity="blocking",
        code="post_publication_blocker",
        message="test blocker",
        evidence="test evidence",
        repair_suggestion="publish a correction",
    )
    intake_session.add(issue)
    intake_session.flush()

    with pytest.raises(module.MetricSourceUnavailableError) as blocker:
        repository.get_published_source(intake_session, batch.id)
    assert blocker.value.code == "blocking_quality_issue"

    issue.severity = "warning"
    intake_session.flush()
    with pytest.raises(module.MetricSourceUnavailableError) as warning:
        repository.get_published_source(intake_session, batch.id)
    assert warning.value.code == "unacknowledged_warning"
