from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.intake import AnalysisBatch, IdentityTimestampMixin


class MetricDefinition(IdentityTimestampMixin, Base):
    __tablename__ = "metric_definition"
    __table_args__ = (
        UniqueConstraint("metric_code", "version", name="uq_metric_definition_code_version"),
        CheckConstraint("version > 0", name="ck_metric_definition_version_positive"),
    )

    metric_code: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_definition: Mapped[str] = mapped_column(Text, nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    aggregation: Mapped[str] = mapped_column(String(64), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    format_pattern: Mapped[str | None] = mapped_column(String(64))
    effective_from_month: Mapped[int | None] = mapped_column(Integer)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    warning_threshold: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    critical_threshold: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    definition_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class MetricSnapshot(IdentityTimestampMixin, Base):
    __tablename__ = "metric_snapshot"
    __table_args__ = (
        UniqueConstraint("batch_id", "version", name="uq_metric_snapshot_batch_version"),
        CheckConstraint("version > 0", name="ck_metric_snapshot_version_positive"),
    )

    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_batch.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(128), nullable=False)

    batch: Mapped[AnalysisBatch] = relationship()


class MetricValue(IdentityTimestampMixin, Base):
    __tablename__ = "metric_value"
    __table_args__ = (
        Index(
            "uq_metric_value_snapshot_grain",
            "metric_snapshot_id",
            "metric_definition_id",
            "comparison_type",
            "period_id",
            "organization_id",
            "customer_id",
            "customer_segment_id",
            "logistics_product_id",
            "region_id",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
    )

    metric_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("metric_snapshot.id", ondelete="CASCADE"), nullable=False
    )
    metric_definition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("metric_definition.id", ondelete="RESTRICT"),
        nullable=False,
    )
    comparison_type: Mapped[str] = mapped_column(String(32), nullable=False)
    period_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim_period.id"))
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim_organization.id"))
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim_customer.id"))
    customer_segment_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim_customer_segment.id"))
    logistics_product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dim_logistics_product.id")
    )
    region_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim_region.id"))
    value: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)

    metric_snapshot: Mapped[MetricSnapshot] = relationship()
    metric_definition: Mapped[MetricDefinition] = relationship()


class Finding(IdentityTimestampMixin, Base):
    __tablename__ = "finding"
    __table_args__ = (
        CheckConstraint(
            "status in ('candidate', 'in_review', 'approved', 'rejected')",
            name="ck_finding_status",
        ),
        CheckConstraint("confidence between 0 and 1", name="ck_finding_confidence_range"),
    )

    metric_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("metric_snapshot.id", ondelete="CASCADE"), nullable=False
    )
    metric_definition_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("metric_definition.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")
    impact_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    business_meaning: Mapped[str | None] = mapped_column(Text)

    metric_snapshot: Mapped[MetricSnapshot] = relationship()
    metric_definition: Mapped[MetricDefinition | None] = relationship()
    drivers: Mapped[list[DriverContribution]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )


class DriverContribution(IdentityTimestampMixin, Base):
    __tablename__ = "driver_contribution"
    __table_args__ = (
        UniqueConstraint("finding_id", "position", name="uq_driver_contribution_order"),
        CheckConstraint("position > 0", name="ck_driver_contribution_position_positive"),
    )

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_code: Mapped[str] = mapped_column(String(128), nullable=False)
    calculation_method: Mapped[str | None] = mapped_column(Text)
    contribution_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    contribution_ratio: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    finding: Mapped[Finding] = relationship(back_populates="drivers")


class Evidence(IdentityTimestampMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'verified', 'rejected')", name="ck_evidence_status"),
        CheckConstraint(
            "object_type in ('metric', 'finding', 'evidence', 'source_record')",
            name="ck_evidence_object_type",
        ),
    )

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[str] = mapped_column(String(128), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    finding: Mapped[Finding] = relationship()


class ReviewEvent(IdentityTimestampMixin, Base):
    __tablename__ = "review_event"
    __table_args__ = (
        UniqueConstraint("finding_id", "sequence", name="uq_review_event_finding_sequence"),
        CheckConstraint("sequence > 0", name="ck_review_event_sequence_positive"),
        CheckConstraint(
            "decision in ('submitted', 'approved', 'rejected', 'returned')",
            name="ck_review_event_decision",
        ),
    )

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    finding: Mapped[Finding] = relationship()


@event.listens_for(ReviewEvent, "before_update")
@event.listens_for(ReviewEvent, "before_delete")
def _protect_review_event_history(*_: object) -> None:
    raise ValueError("review events are append-only")


class Conclusion(IdentityTimestampMixin, Base):
    __tablename__ = "conclusion"

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finding.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    verified_facts: Mapped[str] = mapped_column(Text, nullable=False)
    analysis_judgment: Mapped[str] = mapped_column(Text, nullable=False)
    open_questions: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)

    finding: Mapped[Finding] = relationship()
