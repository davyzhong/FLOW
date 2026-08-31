from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flow_api.domain.enums import BatchStatus, QualitySeverity
from flow_api.domain.ids import new_uuid7
from flow_api.infrastructure.models.base import Base


class IdentityTimestampMixin:
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AnalysisBatch(IdentityTimestampMixin, Base):
    __tablename__ = "analysis_batch"
    __table_args__ = (
        CheckConstraint(
            "status in ('draft', 'validating', 'blocked', 'ready', 'published')",
            name="ck_analysis_batch_status",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=BatchStatus.DRAFT.value)
    description: Mapped[str | None] = mapped_column(Text)

    source_files: Mapped[list[SourceFile]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )
    import_versions: Mapped[list[ImportVersion]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class StoredObject(IdentityTimestampMixin, Base):
    __tablename__ = "stored_object"
    __table_args__ = (
        CheckConstraint("length(sha256) = 64", name="ck_stored_object_sha256_length"),
        CheckConstraint("size_bytes >= 0", name="ck_stored_object_size_nonnegative"),
    )

    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)

    source_files: Mapped[list[SourceFile]] = relationship(back_populates="stored_object")


class SourceFile(IdentityTimestampMixin, Base):
    __tablename__ = "source_file"

    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_batch.id", ondelete="CASCADE"), nullable=False
    )
    stored_object_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("stored_object.id", ondelete="RESTRICT"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    workbook_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    batch: Mapped[AnalysisBatch] = relationship(back_populates="source_files")
    stored_object: Mapped[StoredObject] = relationship(back_populates="source_files")
    source_records: Mapped[list[SourceRecord]] = relationship(back_populates="source_file")


class MappingVersion(IdentityTimestampMixin, Base):
    __tablename__ = "mapping_version"
    __table_args__ = (
        UniqueConstraint("batch_id", "sequence", name="uq_mapping_version_batch_sequence"),
        UniqueConstraint("batch_id", "mapping_hash", name="uq_mapping_version_batch_hash"),
        CheckConstraint("sequence > 0", name="ck_mapping_version_sequence_positive"),
        CheckConstraint(
            "mapping_hash is null or length(mapping_hash) = 64",
            name="ck_mapping_version_hash_length",
        ),
    )

    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_batch.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    mapping_hash: Mapped[str | None] = mapped_column(String(64))
    mapping_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    rationale_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="system")


class ImportVersion(IdentityTimestampMixin, Base):
    __tablename__ = "import_version"
    __table_args__ = (
        UniqueConstraint("batch_id", "sequence", name="uq_import_version_batch_sequence"),
        UniqueConstraint("id", "batch_id", name="uq_import_version_id_batch"),
        CheckConstraint("sequence > 0", name="ck_import_version_sequence_positive"),
        CheckConstraint(
            "status in ('draft', 'validating', 'blocked', 'ready', 'published')",
            name="ck_import_version_status",
        ),
        Index(
            "uq_import_version_one_published_per_batch",
            "batch_id",
            unique=True,
            postgresql_where=text("is_published"),
        ),
    )

    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_batch.id", ondelete="CASCADE"), nullable=False
    )
    mapping_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("mapping_version.id", ondelete="RESTRICT")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    batch: Mapped[AnalysisBatch] = relationship(back_populates="import_versions")
    mapping_version: Mapped[MappingVersion | None] = relationship()
    source_records: Mapped[list[SourceRecord]] = relationship(back_populates="import_version")


class TransformationEvent(IdentityTimestampMixin, Base):
    __tablename__ = "transformation_event"

    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_version.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    operation: Mapped[str] = mapped_column(String(128), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="system")


class QualityIssue(IdentityTimestampMixin, Base):
    __tablename__ = "quality_issue"
    __table_args__ = (
        CheckConstraint("severity in ('blocking', 'warning')", name="ck_quality_issue_severity"),
        CheckConstraint(
            "source_row is null or source_row >= 1", name="ck_quality_issue_row_positive"
        ),
    )

    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_version.id", ondelete="CASCADE"), nullable=False
    )
    source_file_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("source_file.id", ondelete="CASCADE")
    )
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default=QualitySeverity.WARNING.value
    )
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    repair_suggestion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sheet_name: Mapped[str | None] = mapped_column(String(255))
    source_row: Mapped[int | None] = mapped_column(Integer)
    source_column: Mapped[str | None] = mapped_column(String(32))
    acknowledgement: Mapped[WarningAcknowledgement | None] = relationship(
        back_populates="quality_issue", cascade="all, delete-orphan", uselist=False
    )


class WarningAcknowledgement(IdentityTimestampMixin, Base):
    __tablename__ = "warning_acknowledgement"
    __table_args__ = (
        UniqueConstraint("quality_issue_id", name="uq_warning_ack_issue"),
        CheckConstraint("length(btrim(actor)) > 0", name="ck_warning_ack_actor_nonempty"),
        CheckConstraint("length(btrim(reason)) > 0", name="ck_warning_ack_reason_nonempty"),
    )

    quality_issue_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("quality_issue.id", ondelete="CASCADE"), nullable=False
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    quality_issue: Mapped[QualityIssue] = relationship(back_populates="acknowledgement")


class ReconciliationResult(IdentityTimestampMixin, Base):
    __tablename__ = "reconciliation_result"
    __table_args__ = (
        UniqueConstraint(
            "import_version_id",
            "reconciliation_code",
            name="uq_reconciliation_result_version_code",
        ),
    )

    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_version.id", ondelete="CASCADE"), nullable=False
    )
    reconciliation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expected_value: Mapped[str | None] = mapped_column(String(255))
    actual_value: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class SourceRecord(IdentityTimestampMixin, Base):
    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint(
            "import_version_id",
            "source_file_id",
            "sheet_name",
            "source_row",
            "source_column",
            "canonical_field",
            name="uq_source_record_field_lineage",
        ),
        CheckConstraint("source_row >= 1", name="ck_source_record_row_positive"),
        CheckConstraint(
            "(transform_rule_id is null and transform_rule_version is null) or "
            "(transform_rule_id is not null and transform_rule_version > 0)",
            name="ck_source_record_transform_rule_complete",
        ),
    )

    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_version.id", ondelete="CASCADE"), nullable=False
    )
    source_file_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("source_file.id", ondelete="CASCADE"), nullable=False
    )
    sheet_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    source_column: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_field: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    transformed_value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    transform_rule_id: Mapped[str | None] = mapped_column(String(128))
    transform_rule_version: Mapped[int | None] = mapped_column(Integer)
    transform_reason: Mapped[str | None] = mapped_column(Text)

    import_version: Mapped[ImportVersion] = relationship(back_populates="source_records")
    source_file: Mapped[SourceFile] = relationship(back_populates="source_records")
