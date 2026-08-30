from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flow_api.infrastructure.models.analytics import MetricSnapshot
from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.intake import IdentityTimestampMixin, StoredObject


class ReportSnapshot(IdentityTimestampMixin, Base):
    __tablename__ = "report_snapshot"
    __table_args__ = (
        UniqueConstraint("metric_snapshot_id", "version", name="uq_report_snapshot_metric_version"),
        CheckConstraint("version > 0", name="ck_report_snapshot_version_positive"),
    )

    metric_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("metric_snapshot.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    template_code: Mapped[str] = mapped_column(String(128), nullable=False)
    presentation_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    metric_snapshot: Mapped[MetricSnapshot] = relationship()
    items: Mapped[list[ReportSnapshotItem]] = relationship(
        back_populates="report_snapshot",
        cascade="all, delete-orphan",
        order_by="ReportSnapshotItem.position",
    )
    publication_attempts: Mapped[list[PublicationAttempt]] = relationship(
        back_populates="report_snapshot", cascade="all, delete-orphan"
    )


class ReportSnapshotItem(IdentityTimestampMixin, Base):
    __tablename__ = "report_snapshot_item"
    __table_args__ = (
        UniqueConstraint("report_snapshot_id", "position", name="uq_report_snapshot_item_order"),
        CheckConstraint("position > 0", name="ck_report_snapshot_item_position_positive"),
        CheckConstraint(
            "object_type in ('metric', 'finding', 'evidence', 'conclusion')",
            name="ck_report_snapshot_item_object_type",
        ),
    )

    report_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("report_snapshot.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[str] = mapped_column(String(128), nullable=False)
    presentation_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    report_snapshot: Mapped[ReportSnapshot] = relationship(back_populates="items")


class PublicationAttempt(IdentityTimestampMixin, Base):
    __tablename__ = "publication_attempt"
    __table_args__ = (
        UniqueConstraint(
            "report_snapshot_id", "sequence", name="uq_publication_attempt_report_sequence"
        ),
        CheckConstraint("sequence > 0", name="ck_publication_attempt_sequence_positive"),
        CheckConstraint(
            "format in ('pptx', 'xlsx', 'html', 'pdf')", name="ck_publication_attempt_format"
        ),
        CheckConstraint(
            "status in ('queued', 'running', 'succeeded', 'failed')",
            name="ck_publication_attempt_status",
        ),
    )

    report_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("report_snapshot.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stored_object_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("stored_object.id", ondelete="RESTRICT")
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    report_snapshot: Mapped[ReportSnapshot] = relationship(back_populates="publication_attempts")
    stored_object: Mapped[StoredObject | None] = relationship()
