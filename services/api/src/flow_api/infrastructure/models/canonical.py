from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from flow_api.domain.ids import new_uuid7
from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.intake import ImportVersion, SourceRecord


class CanonicalIdentityMixin:
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=new_uuid7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Period(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_period"
    __table_args__ = (
        CheckConstraint("month between 1 and 12", name="ck_dim_period_month"),
        CheckConstraint("quarter between 1 and 4", name="ck_dim_period_quarter"),
        CheckConstraint("month_key = year * 100 + month", name="ck_dim_period_month_key"),
    )

    month_key: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)


class Organization(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_organization"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dim_organization.id", ondelete="RESTRICT")
    )


class CustomerSegment(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_customer_segment"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Customer(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_customer"
    __table_args__ = (
        CheckConstraint(
            "credit_term_days is null or credit_term_days >= 0",
            name="ck_dim_customer_credit_term_nonnegative",
        ),
    )

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128))
    tier: Mapped[str | None] = mapped_column(String(64))
    credit_term_days: Mapped[int | None] = mapped_column(Integer)
    segment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dim_customer_segment.id", ondelete="RESTRICT")
    )

    segment: Mapped[CustomerSegment | None] = relationship()


class LogisticsProduct(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_logistics_product"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str | None] = mapped_column(String(64))
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dim_logistics_product.id", ondelete="RESTRICT")
    )


class Region(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_region"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    province: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dim_region.id", ondelete="RESTRICT")
    )


class ManagementAccount(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_management_account"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    financial_account_code: Mapped[str | None] = mapped_column(String(128))
    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("dim_management_account.id", ondelete="RESTRICT")
    )


class ScenarioVersion(CanonicalIdentityMixin, Base):
    __tablename__ = "dim_scenario_version"

    code: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(128))


class LineageFactMixin:
    business_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, default=new_uuid7
    )
    import_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_version.id", ondelete="RESTRICT"), nullable=False
    )
    source_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("source_record.id", ondelete="RESTRICT"), nullable=False
    )

    @declared_attr
    def import_version(cls) -> Mapped[ImportVersion]:
        return relationship()

    @declared_attr
    def source_record(cls) -> Mapped[SourceRecord]:
        return relationship()


class FactOperatingActual(CanonicalIdentityMixin, LineageFactMixin, Base):
    __tablename__ = "fact_operating_actual"
    __table_args__ = (
        UniqueConstraint(
            "import_version_id",
            "period_id",
            "organization_id",
            "customer_id",
            "logistics_product_id",
            "region_id",
            name="uq_operating_actual_grain",
        ),
    )

    period_id: Mapped[UUID] = mapped_column(ForeignKey("dim_period.id"), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("dim_organization.id"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("dim_customer.id"), nullable=False)
    logistics_product_id: Mapped[UUID] = mapped_column(
        ForeignKey("dim_logistics_product.id"), nullable=False
    )
    region_id: Mapped[UUID] = mapped_column(ForeignKey("dim_region.id"), nullable=False)
    order_count: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    shipment_count: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    warehousing_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    transportation_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    other_direct_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)

    period: Mapped[Period] = relationship()
    organization: Mapped[Organization] = relationship()
    customer: Mapped[Customer] = relationship()
    logistics_product: Mapped[LogisticsProduct] = relationship()
    region: Mapped[Region] = relationship()


class FactFinancialActual(CanonicalIdentityMixin, LineageFactMixin, Base):
    __tablename__ = "fact_financial_actual"
    __table_args__ = (
        UniqueConstraint(
            "import_version_id",
            "period_id",
            "organization_id",
            "management_account_id",
            name="uq_financial_actual_grain",
        ),
    )

    period_id: Mapped[UUID] = mapped_column(ForeignKey("dim_period.id"), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("dim_organization.id"), nullable=False)
    management_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("dim_management_account.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)

    period: Mapped[Period] = relationship()
    organization: Mapped[Organization] = relationship()
    management_account: Mapped[ManagementAccount] = relationship()


class FactBudget(CanonicalIdentityMixin, LineageFactMixin, Base):
    __tablename__ = "fact_budget"
    __table_args__ = (
        Index(
            "uq_fact_budget_grain",
            "import_version_id",
            "period_id",
            "organization_id",
            "customer_segment_id",
            "logistics_product_id",
            "management_account_id",
            "scenario_version_id",
            "metric_code",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
    )

    period_id: Mapped[UUID] = mapped_column(ForeignKey("dim_period.id"), nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("dim_organization.id"), nullable=False)
    customer_segment_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim_customer_segment.id"))
    logistics_product_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dim_logistics_product.id")
    )
    management_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dim_management_account.id")
    )
    scenario_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("dim_scenario_version.id"), nullable=False
    )
    metric_code: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)

    period: Mapped[Period] = relationship()
    organization: Mapped[Organization] = relationship()
    customer_segment: Mapped[CustomerSegment | None] = relationship()
    logistics_product: Mapped[LogisticsProduct | None] = relationship()
    management_account: Mapped[ManagementAccount | None] = relationship()
    scenario_version: Mapped[ScenarioVersion] = relationship()


class FactArCollection(CanonicalIdentityMixin, LineageFactMixin, Base):
    __tablename__ = "fact_ar_collection"
    __table_args__ = (
        CheckConstraint(
            "invoice_number is not null or aging_bucket is not null",
            name="ck_ar_invoice_or_aging_bucket",
        ),
        Index(
            "uq_fact_ar_collection_grain",
            "import_version_id",
            "period_id",
            "customer_id",
            "invoice_number",
            "aging_bucket",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
    )

    period_id: Mapped[UUID] = mapped_column(ForeignKey("dim_period.id"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("dim_customer.id"), nullable=False)
    invoice_number: Mapped[str | None] = mapped_column(String(128))
    aging_bucket: Mapped[str | None] = mapped_column(String(64))
    receivable_balance: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    due_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    overdue_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    collected_amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)

    period: Mapped[Period] = relationship()
    customer: Mapped[Customer] = relationship()
