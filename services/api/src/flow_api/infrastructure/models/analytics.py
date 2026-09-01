from __future__ import annotations

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.canonical import Period
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    IdentityTimestampMixin,
    ImportVersion,
)


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


class MetricDefinitionDependency(IdentityTimestampMixin, Base):
    __tablename__ = "metric_definition_dependency"
    __table_args__ = (
        UniqueConstraint(
            "metric_definition_id",
            "dependency_definition_id",
            name="uq_metric_definition_dependency_edge",
        ),
        UniqueConstraint(
            "metric_definition_id",
            "position",
            name="uq_metric_definition_dependency_position",
        ),
        CheckConstraint(
            "position > 0", name="ck_metric_definition_dependency_position_positive"
        ),
        CheckConstraint(
            "metric_definition_id <> dependency_definition_id",
            name="ck_metric_definition_dependency_not_self",
        ),
    )

    metric_definition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("metric_definition.id", ondelete="RESTRICT"),
        nullable=False,
    )
    dependency_definition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("metric_definition.id", ondelete="RESTRICT"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    metric_definition: Mapped[MetricDefinition] = relationship(
        foreign_keys=[metric_definition_id]
    )
    dependency_definition: Mapped[MetricDefinition] = relationship(
        foreign_keys=[dependency_definition_id]
    )


@event.listens_for(MetricDefinitionDependency, "before_update")
@event.listens_for(MetricDefinitionDependency, "before_delete")
def _protect_metric_definition_dependency(*_: object) -> None:
    raise ValueError("metric definition dependencies are append-only")


class MetricSnapshot(IdentityTimestampMixin, Base):
    __tablename__ = "metric_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "import_version_id",
            "as_of_period_id",
            "version",
            name="uq_metric_snapshot_identity_version",
        ),
        CheckConstraint("version > 0", name="ck_metric_snapshot_version_positive"),
        CheckConstraint(
            "status in ('building', 'published', 'failed')",
            name="ck_metric_snapshot_status",
        ),
        CheckConstraint(
            "length(definition_set_hash) = 64",
            name="ck_metric_snapshot_definition_hash_length",
        ),
        CheckConstraint(
            "length(fingerprint) = 64", name="ck_metric_snapshot_fingerprint_length"
        ),
        ForeignKeyConstraint(
            ["import_version_id", "batch_id"],
            ["import_version.id", "import_version.batch_id"],
            name="fk_metric_snapshot_import_batch",
            ondelete="RESTRICT",
        ),
    )

    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_batch.id", ondelete="RESTRICT"), nullable=False
    )
    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )
    as_of_period_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dim_period.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(128), nullable=False)
    definition_set_id: Mapped[str] = mapped_column(String(128), nullable=False)
    definition_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="building", server_default="building"
    )

    batch: Mapped[AnalysisBatch] = relationship(overlaps="import_version")
    import_version: Mapped[ImportVersion] = relationship(overlaps="batch")
    as_of_period: Mapped[Period] = relationship()


@event.listens_for(MetricSnapshot, "before_update")
def _protect_published_metric_snapshot_update(
    _mapper: object, _connection: object, target: MetricSnapshot
) -> None:
    prior_statuses = inspect(target).attrs.status.history.deleted
    if (
        target.status == "published" or "published" in prior_statuses
    ) and list(prior_statuses) != ["building"]:
        raise ValueError("published metric snapshots are append-only")


@event.listens_for(MetricSnapshot, "before_delete")
def _protect_published_metric_snapshot_delete(
    _mapper: object, _connection: object, target: MetricSnapshot
) -> None:
    if target.status == "published":
        raise ValueError("published metric snapshots are append-only")


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
    exact_value: Mapped[str] = mapped_column(Text, nullable=False)
    calculation_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    metric_snapshot: Mapped[MetricSnapshot] = relationship()
    metric_definition: Mapped[MetricDefinition] = relationship()


def _metric_value_snapshot_is_published(connection: Any, target: MetricValue) -> bool:
    snapshot_id = target.metric_snapshot_id
    if snapshot_id is None and target.metric_snapshot is not None:
        snapshot_id = target.metric_snapshot.id
    status = connection.scalar(
        select(MetricSnapshot.status).where(MetricSnapshot.id == snapshot_id)
    )
    return status is not None and str(status) == "published"


@event.listens_for(MetricValue, "before_update")
@event.listens_for(MetricValue, "before_delete")
def _protect_published_metric_value(
    _mapper: object, connection: Any, target: MetricValue
) -> None:
    if _metric_value_snapshot_is_published(connection, target):
        raise ValueError("published metric values are append-only")


class AnalysisRun(IdentityTimestampMixin, Base):
    __tablename__ = "analysis_run"
    __table_args__ = (
        UniqueConstraint(
            "metric_snapshot_id",
            "policy_set_hash",
            "engine_version",
            name="uq_analysis_run_identity",
        ),
        CheckConstraint(
            "status in ('building', 'published', 'failed')",
            name="ck_analysis_run_status",
        ),
        CheckConstraint(
            "length(policy_set_hash) = 64", name="ck_analysis_run_policy_hash_length"
        ),
        CheckConstraint(
            "length(fingerprint) = 64", name="ck_analysis_run_fingerprint_length"
        ),
    )

    metric_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("metric_snapshot.id", ondelete="RESTRICT"),
        nullable=False,
    )
    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_version.id", ondelete="RESTRICT"),
        nullable=False,
    )
    policy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    policy_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(128), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="building", server_default="building"
    )

    metric_snapshot: Mapped[MetricSnapshot] = relationship()
    import_version: Mapped[ImportVersion] = relationship()
    results: Mapped[list[AnalysisResult]] = relationship(
        back_populates="analysis_run", cascade="all, delete-orphan"
    )


@event.listens_for(AnalysisRun, "before_update")
def _protect_published_analysis_run_update(
    _mapper: object, _connection: object, target: AnalysisRun
) -> None:
    status_history = inspect(target).attrs.status.history
    publishing = list(status_history.deleted) == ["building"] and list(
        status_history.added
    ) == ["published"]
    if target.status == "published" and not publishing:
        raise ValueError("published analysis runs are append-only")


@event.listens_for(AnalysisRun, "before_delete")
def _protect_published_analysis_run_delete(
    _mapper: object, _connection: object, target: AnalysisRun
) -> None:
    if target.status == "published":
        raise ValueError("published analysis runs are append-only")


class AnalysisResult(IdentityTimestampMixin, Base):
    __tablename__ = "analysis_result"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id",
            "playbook_code",
            "comparison_basis",
            name="uq_analysis_result_run_playbook_basis",
        ),
        CheckConstraint("playbook_version > 0", name="ck_analysis_result_version_positive"),
        CheckConstraint(
            "status in ('complete', 'degraded', 'not_applicable')",
            name="ck_analysis_result_status",
        ),
        CheckConstraint(
            "comparison_basis in ('prior_year', 'budget')",
            name="ck_analysis_result_comparison_basis",
        ),
        CheckConstraint(
            "reconciliation_tolerance >= 0",
            name="ck_analysis_result_tolerance_nonnegative",
        ),
        CheckConstraint(
            "source_record_count >= 0", name="ck_analysis_result_source_count_nonnegative"
        ),
    )

    analysis_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("analysis_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    playbook_code: Mapped[str] = mapped_column(String(128), nullable=False)
    playbook_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    comparison_basis: Mapped[str] = mapped_column(String(32), nullable=False)
    impact_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    reconciliation_difference: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    reconciliation_tolerance: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    required_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    available_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    missing_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    source_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    calculation_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    degradation_code: Mapped[str | None] = mapped_column(String(64))
    degradation_message: Mapped[str | None] = mapped_column(Text)

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="results")
    drivers: Mapped[list[AnalysisDriver]] = relationship(
        back_populates="analysis_result", cascade="all, delete-orphan"
    )


class AnalysisDriver(IdentityTimestampMixin, Base):
    __tablename__ = "analysis_driver"
    __table_args__ = (
        UniqueConstraint("analysis_result_id", "position", name="uq_analysis_driver_order"),
        UniqueConstraint(
            "analysis_result_id", "driver_code", name="uq_analysis_driver_result_code"
        ),
        CheckConstraint("position > 0", name="ck_analysis_driver_position_positive"),
    )

    analysis_result_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("analysis_result.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_code: Mapped[str] = mapped_column(String(128), nullable=False)
    calculation_method: Mapped[str | None] = mapped_column(Text)
    contribution_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    contribution_ratio: Mapped[Decimal | None] = mapped_column(Numeric(16, 6))
    calculation_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    analysis_result: Mapped[AnalysisResult] = relationship(back_populates="drivers")


def _analysis_run_is_published(connection: Any, analysis_run_id: UUID | None) -> bool:
    if analysis_run_id is None:
        return False
    status = connection.scalar(
        select(AnalysisRun.status).where(AnalysisRun.id == analysis_run_id)
    )
    return status is not None and str(status) == "published"


def _result_run_id(connection: Any, result_id: UUID | None) -> UUID | None:
    if result_id is None:
        return None
    return cast(
        UUID | None,
        connection.scalar(
            select(AnalysisResult.analysis_run_id).where(AnalysisResult.id == result_id)
        ),
    )


@event.listens_for(AnalysisResult, "before_update")
@event.listens_for(AnalysisResult, "before_delete")
def _protect_published_analysis_result(
    _mapper: object, connection: Any, target: AnalysisResult
) -> None:
    if _analysis_run_is_published(connection, target.analysis_run_id):
        raise ValueError("published analysis results are append-only")


@event.listens_for(AnalysisDriver, "before_update")
@event.listens_for(AnalysisDriver, "before_delete")
def _protect_published_analysis_driver(
    _mapper: object, connection: Any, target: AnalysisDriver
) -> None:
    if _analysis_run_is_published(
        connection, _result_run_id(connection, target.analysis_result_id)
    ):
        raise ValueError("published analysis drivers are append-only")


class Finding(IdentityTimestampMixin, Base):
    __tablename__ = "finding"
    __table_args__ = (
        CheckConstraint(
            "status in ('candidate', 'in_review', 'approved', 'rejected')",
            name="ck_finding_status",
        ),
        CheckConstraint("confidence between 0 and 1", name="ck_finding_confidence_range"),
        CheckConstraint(
            "total_score is null or total_score between 0 and 100",
            name="ck_finding_total_score_range",
        ),
        UniqueConstraint(
            "analysis_run_id", "fingerprint", name="uq_finding_run_fingerprint"
        ),
    )

    metric_snapshot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("metric_snapshot.id", ondelete="CASCADE"), nullable=False
    )
    metric_definition_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("metric_definition.id", ondelete="RESTRICT")
    )
    analysis_run_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_run.id", ondelete="CASCADE")
    )
    analysis_result_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("analysis_result.id", ondelete="CASCADE")
    )
    finding_type: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")
    impact_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    business_meaning: Mapped[str | None] = mapped_column(Text)
    fact_statement: Mapped[str | None] = mapped_column(Text)
    comparison_basis: Mapped[str | None] = mapped_column(String(32))
    total_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    policy_version: Mapped[str | None] = mapped_column(String(128))
    fingerprint: Mapped[str | None] = mapped_column(String(64))
    qualification_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    metric_snapshot: Mapped[MetricSnapshot] = relationship()
    metric_definition: Mapped[MetricDefinition | None] = relationship()
    analysis_run: Mapped[AnalysisRun | None] = relationship()
    analysis_result: Mapped[AnalysisResult | None] = relationship()
    drivers: Mapped[list[DriverContribution]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )
    score_components: Mapped[list[FindingScoreComponent]] = relationship(
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
    contribution_ratio: Mapped[Decimal | None] = mapped_column(Numeric(16, 6))
    calculation_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    finding: Mapped[Finding] = relationship(back_populates="drivers")


class Evidence(IdentityTimestampMixin, Base):
    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'verified', 'rejected')", name="ck_evidence_status"),
        CheckConstraint(
            "object_type in ('metric', 'finding', 'evidence', 'source_record', "
            "'analysis_run', 'analysis_result', 'canonical_record_set', 'lineage', "
            "'invariant')",
            name="ck_evidence_object_type",
        ),
    )

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[str] = mapped_column(String(256), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    evidence_digest: Mapped[str | None] = mapped_column(String(64))
    verification_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    finding: Mapped[Finding] = relationship()


class FindingScoreComponent(IdentityTimestampMixin, Base):
    __tablename__ = "finding_score_component"
    __table_args__ = (
        UniqueConstraint(
            "finding_id", "component_code", name="uq_finding_score_component_code"
        ),
        CheckConstraint(
            "normalized_score between 0 and 100",
            name="ck_finding_score_normalized_range",
        ),
        CheckConstraint("weight between 0 and 1", name="ck_finding_score_weight_range"),
        CheckConstraint(
            "weighted_score between 0 and 100",
            name="ck_finding_score_weighted_range",
        ),
    )

    finding_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finding.id", ondelete="CASCADE"), nullable=False
    )
    component_code: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_value: Mapped[Decimal] = mapped_column(Numeric(24, 6), nullable=False)
    normalized_score: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    weighted_score: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    calculation_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    finding: Mapped[Finding] = relationship(back_populates="score_components")


def _finding_run_id(connection: Any, finding_id: UUID | None) -> UUID | None:
    if finding_id is None:
        return None
    return cast(
        UUID | None,
        connection.scalar(
            select(Finding.analysis_run_id).where(Finding.id == finding_id)
        ),
    )


@event.listens_for(FindingScoreComponent, "before_update")
@event.listens_for(FindingScoreComponent, "before_delete")
def _protect_published_finding_score(
    _mapper: object, connection: Any, target: FindingScoreComponent
) -> None:
    if _analysis_run_is_published(
        connection, _finding_run_id(connection, target.finding_id)
    ):
        raise ValueError("published finding scores are append-only")


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
