from __future__ import annotations

from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    MappingVersion,
    QualityIssue,
    SourceFile,
    SourceRecord,
    StoredObject,
    WarningAcknowledgement,
)


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def clean_tables() -> None:
    with Session(get_engine()) as session:
        for model in (
            WarningAcknowledgement,
            SourceRecord,
            QualityIssue,
            ImportVersion,
            MappingVersion,
            SourceFile,
            StoredObject,
            AnalysisBatch,
        ):
            session.execute(delete(model))
        session.commit()


@pytest.fixture
def session() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        yield database_session


def _version(session: Session) -> tuple[AnalysisBatch, ImportVersion]:
    batch = AnalysisBatch(name=f"audit-{uuid4().hex}")
    version = ImportVersion(batch=batch, sequence=1, status="validating")
    session.add_all([batch, version])
    session.flush()
    return batch, version


def test_mapping_hash_confidence_and_rationale_are_versioned(session: Session) -> None:
    batch, _ = _version(session)
    mapping = MappingVersion(
        batch_id=batch.id,
        sequence=1,
        mapping_hash="a" * 64,
        mapping_spec={"contract_version": "flow.excel.v1"},
        confidence_summary={"high": 42, "low": 1},
        rationale_summary={"unresolved": []},
        created_by="finance.bp@example.com",
    )
    session.add(mapping)
    session.commit()

    assert mapping.mapping_hash == "a" * 64
    assert mapping.confidence_summary["high"] == 42


def test_source_record_retains_transform_rule_identity(session: Session) -> None:
    batch, version = _version(session)
    digest = uuid4().hex * 2
    stored = StoredObject(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=100,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    source = SourceFile(batch=batch, stored_object=stored, original_filename="source.xlsx")
    lineage = SourceRecord(
        import_version=version,
        source_file=source,
        sheet_name="业务明细",
        source_row=4,
        source_column="L",
        canonical_field="month_key",
        raw_value={"value": "2026年08月"},
        transformed_value={"value": "2026-08"},
        transform_rule_id="normalize_month",
        transform_rule_version=1,
        transform_reason="规范化月份格式",
    )
    session.add(lineage)
    session.commit()

    assert lineage.transform_rule_id == "normalize_month"
    assert lineage.transform_rule_version == 1


def test_only_warning_issue_can_be_acknowledged_with_actor_and_reason(session: Session) -> None:
    _, version = _version(session)
    warning = QualityIssue(
        import_version_id=version.id,
        severity="warning",
        code="low_confidence_mapping",
        message="confirm mapping",
    )
    session.add(warning)
    session.flush()
    acknowledgement = WarningAcknowledgement(
        quality_issue_id=warning.id,
        actor="finance.bp@example.com",
        reason="已与业务负责人核对口径",
    )
    session.add(acknowledgement)
    session.commit()

    assert acknowledgement.quality_issue_id == warning.id
    assert acknowledgement.acknowledged_at is not None

    blocking = QualityIssue(
        import_version_id=version.id,
        severity="blocking",
        code="duplicate_grain",
        message="duplicate",
    )
    session.add(blocking)
    session.flush()
    session.add(
        WarningAcknowledgement(
            quality_issue_id=blocking.id,
            actor="finance.bp@example.com",
            reason="cannot override blocking issue",
        )
    )
    with pytest.raises(DBAPIError):
        session.commit()


def test_import_status_and_acknowledgement_text_are_constrained(session: Session) -> None:
    batch = AnalysisBatch(name=f"constraints-{uuid4().hex}")
    session.add(batch)
    session.flush()

    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "insert into import_version "
                "(id, batch_id, sequence, is_published, status, summary) "
                "values (:id, :batch, 1, false, 'unknown', '{}'::jsonb)"
            ),
            {"id": uuid4(), "batch": batch.id},
        )
        session.commit()
