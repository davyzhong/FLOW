from __future__ import annotations

from dataclasses import replace

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.persistence import read_canonical_package_by_version
from flow_api.data_contract.semantic import compare_semantics
from flow_api.infrastructure.models.intake import QualityIssue, SourceRecord
from flow_api.intake.quality import Issue, IssueLocation
from flow_api.intake.service import (
    IntakeService,
    InvalidIntakeTransitionError,
    PublicationBlockedError,
)

from .intake_service_support import (
    STANDARD,
    intake_inputs,
)
from .intake_service_support import (
    intake_session_fixture as _intake_session_fixture,  # noqa: F401
)


def setup_module() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def test_intake_lifecycle_is_auditable_idempotent_and_publishable(
    intake_session: Session,
) -> None:
    stored, proposal, candidate, report = intake_inputs()
    service = IntakeService(intake_session)
    batch = service.create_batch("August logistics review")
    source = service.attach_source(batch.id, stored)
    assert service.attach_source(batch.id, stored).id == source.id
    mapping = service.propose_mapping(source.id, proposal)
    assert service.propose_mapping(source.id, proposal).id == mapping.id
    service.confirm_mapping(mapping.id, actor="finance.bp@example.com")

    version = service.validate_import(source.id, mapping.id, candidate, report)
    assert service.validate_import(source.id, mapping.id, candidate, report).id == version.id
    assert version.status == "ready"
    assert batch.status == "ready"
    assert intake_session.scalar(
        select(func.count())
        .select_from(SourceRecord)
        .where(SourceRecord.import_version_id == version.id)
    ) == len(candidate.lineage)
    warnings = list(
        intake_session.scalars(
            select(QualityIssue).where(
                QualityIssue.import_version_id == version.id,
                QualityIssue.severity == "warning",
            )
        )
    )
    if warnings:
        try:
            service.publish_import(version.id)
        except PublicationBlockedError:
            pass
        else:
            raise AssertionError("unacknowledged warnings must block publication")
    for warning in warnings:
        first = service.acknowledge_warning(
            warning.id,
            actor="finance.bp@example.com",
            reason="已与业务负责人核对口径",
        )
        assert (
            service.acknowledge_warning(
                warning.id,
                actor="finance.bp@example.com",
                reason="idempotent retry",
            ).id
            == first.id
        )

    published = service.publish_import(version.id)
    assert published.status == "published"
    assert published.is_published
    assert published.published_at is not None
    assert batch.status == "published"
    assert service.publish_import(version.id).id == version.id


def test_blocking_quality_issue_cannot_be_overridden_or_published(
    intake_session: Session,
) -> None:
    stored, proposal, candidate, report = intake_inputs()
    report = replace(
        report,
        issues=report.issues
        + (
            Issue(
                code="test_blocker",
                severity="blocking",
                message="blocking test issue",
                location=IssueLocation(target_sheet_id="operating_actual"),
                evidence="deterministic test evidence",
                repair_suggestion="create a corrected import",
            ),
        ),
    )
    service = IntakeService(intake_session)
    batch = service.create_batch("Blocked intake")
    source = service.attach_source(batch.id, stored)
    mapping = service.propose_mapping(source.id, proposal)
    version = service.validate_import(source.id, mapping.id, candidate, report)

    assert version.status == "blocked"
    try:
        service.publish_import(version.id)
    except InvalidIntakeTransitionError:
        pass
    else:
        raise AssertionError("blocked import must not publish")
    blocker = intake_session.scalar(select(QualityIssue).where(QualityIssue.code == "test_blocker"))
    assert blocker is not None
    try:
        service.acknowledge_warning(
            blocker.id, actor="finance.bp@example.com", reason="cannot override"
        )
    except PublicationBlockedError:
        pass
    else:
        raise AssertionError("blocking issue must not be acknowledged")


def test_correction_creates_new_published_version_and_preserves_old_rows(
    intake_session: Session,
) -> None:
    service = IntakeService(intake_session)
    batch = service.create_batch("Correction history")
    first_stored, first_proposal, first_candidate, first_report = intake_inputs()
    first_source = service.attach_source(batch.id, first_stored)
    first_mapping = service.propose_mapping(first_source.id, first_proposal)
    first = service.validate_import(
        first_source.id, first_mapping.id, first_candidate, first_report
    )
    for issue in intake_session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == first.id,
            QualityIssue.severity == "warning",
        )
    ):
        service.acknowledge_warning(issue.id, actor="finance.bp", reason="confirmed")
    service.publish_import(first.id)

    second_stored, second_proposal, second_candidate, second_report = intake_inputs(STANDARD)
    second_source = service.attach_source(batch.id, second_stored)
    second_mapping = service.propose_mapping(second_source.id, second_proposal)
    second = service.create_correction(
        second_source.id, second_mapping.id, second_candidate, second_report
    )
    for issue in intake_session.scalars(
        select(QualityIssue).where(
            QualityIssue.import_version_id == second.id,
            QualityIssue.severity == "warning",
        )
    ):
        service.acknowledge_warning(issue.id, actor="finance.bp", reason="confirmed")
    service.publish_import(second.id)
    intake_session.commit()

    assert first.sequence == 1 and second.sequence == 2
    assert not first.is_published and second.is_published
    assert (
        compare_semantics(
            first_candidate.package,
            read_canonical_package_by_version(intake_session, first.id),
        )
        == ()
    )
    assert (
        compare_semantics(
            second_candidate.package,
            read_canonical_package_by_version(intake_session, second.id),
        )
        == ()
    )
