from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    MappingVersion,
    QualityIssue,
    ReconciliationResult,
    SourceFile,
    SourceRecord,
    StoredObject,
    TransformationEvent,
)


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
def clean_intake_tables() -> None:
    tables = [
        SourceRecord,
        ReconciliationResult,
        QualityIssue,
        TransformationEvent,
        ImportVersion,
        MappingVersion,
        SourceFile,
        StoredObject,
        AnalysisBatch,
    ]
    with Session(get_engine()) as session:
        for model in tables:
            session.execute(delete(model))
        session.commit()


@pytest.fixture
def session() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        yield database_session


def make_batch(session: Session) -> AnalysisBatch:
    batch = AnalysisBatch(name=f"August close {uuid4().hex}")
    session.add(batch)
    session.flush()
    return batch


def make_source_file(session: Session, batch: AnalysisBatch) -> SourceFile:
    digest = uuid4().hex * 2
    stored = StoredObject(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=100,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    source = SourceFile(
        batch=batch,
        stored_object=stored,
        original_filename="actuals.xlsx",
    )
    session.add(source)
    session.flush()
    return source


def test_repeated_uploads_share_bytes_but_keep_distinct_upload_records(
    session: Session,
) -> None:
    batch = make_batch(session)
    digest = uuid4().hex * 2
    blob = StoredObject(
        sha256=digest,
        object_key=f"raw/{digest[:2]}/{digest}",
        size_bytes=100,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    first = SourceFile(batch=batch, stored_object=blob, original_filename="first.xlsx")
    second = SourceFile(batch=batch, stored_object=blob, original_filename="second.xlsx")
    session.add_all([first, second])
    session.commit()

    assert first.id != second.id
    assert first.stored_object_id == second.stored_object_id


def test_batch_versions_are_sequenced_and_only_one_can_be_published(
    session: Session,
) -> None:
    batch = make_batch(session)
    session.add_all(
        [
            ImportVersion(batch=batch, sequence=1, is_published=True),
            ImportVersion(batch=batch, sequence=2, is_published=True),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_quality_severity_and_reconciliation_identity_are_constrained(
    session: Session,
) -> None:
    batch = make_batch(session)
    version = ImportVersion(batch=batch, sequence=1)
    session.add(version)
    session.commit()

    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "insert into quality_issue "
                "(id, import_version_id, severity, code, message) "
                "values (:id, :version, 'informational', 'bad', 'bad')"
            ),
            {"id": uuid4(), "version": version.id},
        )
        session.commit()

    session.rollback()
    session.add_all(
        [
            ReconciliationResult(
                import_version_id=version.id,
                reconciliation_code="trial_balance",
                passed=True,
            ),
            ReconciliationResult(
                import_version_id=version.id,
                reconciliation_code="trial_balance",
                passed=False,
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_source_record_keeps_field_level_lineage(session: Session) -> None:
    batch = make_batch(session)
    source = make_source_file(session, batch)
    version = ImportVersion(batch=batch, sequence=1)
    record = SourceRecord(
        import_version=version,
        source_file=source,
        sheet_name="Revenue",
        source_row=12,
        source_column="G",
        canonical_field="revenue",
        raw_value={"value": "100.25"},
        transformed_value={"value": "100.2500"},
    )
    session.add(record)
    session.commit()

    assert record.source_file_id == source.id
    assert (record.sheet_name, record.source_row, record.source_column) == (
        "Revenue",
        12,
        "G",
    )
