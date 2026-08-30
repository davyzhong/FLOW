from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion, QualityIssue
from flow_api.intake.service import IntakeService

from .intake_service_support import (
    intake_inputs,
)
from .intake_service_support import (
    intake_session_fixture as _intake_session_fixture,  # noqa: F401
)


def setup_module() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def test_mid_publication_failure_rolls_back_every_publication_state_change(
    intake_session: Session,
) -> None:
    stored, proposal, candidate, report = intake_inputs()
    service = IntakeService(intake_session)
    batch = service.create_batch("Atomic publication")
    source = service.attach_source(batch.id, stored)
    mapping = service.propose_mapping(source.id, proposal)
    version = service.validate_import(source.id, mapping.id, candidate, report)
    for issue in intake_session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == version.id,
            QualityIssue.severity == "warning",
        )
    ):
        service.acknowledge_warning(issue.id, actor="finance.bp", reason="confirmed")
    intake_session.flush()

    def fail() -> None:
        raise RuntimeError("injected publication failure")

    try:
        service.publish_import(version.id, failure_hook=fail)
    except RuntimeError as error:
        assert str(error) == "injected publication failure"
    else:
        raise AssertionError("failure injection did not run")
    intake_session.expire_all()

    persisted_version = intake_session.get(ImportVersion, version.id)
    persisted_batch = intake_session.get(AnalysisBatch, batch.id)
    assert persisted_version is not None and persisted_batch is not None
    assert persisted_version.status == "ready"
    assert not persisted_version.is_published
    assert persisted_version.published_at is None
    assert persisted_batch.status == "ready"
