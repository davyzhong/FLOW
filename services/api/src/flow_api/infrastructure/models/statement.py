"""外部公开财报抽取数据（P5 反向解析验证）的落库模型。

报表项目按披露原文的列式存储四类可空数值列，不换算单位；
单位与来源随 statement_report 记录，保持原始值不可变原则。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.canonical import CanonicalIdentityMixin


class StatementReport(CanonicalIdentityMixin, Base):
    __tablename__ = "statement_report"
    __table_args__ = (
        UniqueConstraint(
            "stock_code",
            "period_label",
            "report_kind",
            "version",
            name="uq_statement_report_identity",
        ),
        CheckConstraint("version > 0", name="ck_statement_report_version_positive"),
        CheckConstraint("status in ('draft', 'published')", name="ck_statement_report_status"),
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stock_code: Mapped[str] = mapped_column(String(32), nullable=False)
    report_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    period_label: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit_note: Mapped[str] = mapped_column(String(64), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    items: Mapped[list[StatementLineItem]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="StatementLineItem.statement_type, StatementLineItem.sort_order",
    )
    corrections: Mapped[list[StatementCorrection]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="StatementCorrection.created_at",
    )


class StatementLineItem(CanonicalIdentityMixin, Base):
    __tablename__ = "statement_line_item"
    __table_args__ = (
        Index("ix_statement_line_item_report_stmt", "report_id", "statement_type", "sort_order"),
    )

    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("statement_report.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    # 余额列式（资产负债表）：期末 / 期初；发生额列式（利润表、现金流量表）：本期 / 上期。
    value_end: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    value_begin: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    value_current: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    value_prior: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)

    report: Mapped[StatementReport] = relationship(back_populates="items")


class StatementSource(CanonicalIdentityMixin, Base):
    """公开财报原始文件登记（B01）：内容寻址不可变源文件 + 识别候选。

    同一 sha256 重复上传幂等（返回既有登记）；只登记文本 PDF，
    扫描件/OCR 在入库前被拒绝（不写本表）。
    """

    __tablename__ = "statement_source"
    __table_args__ = (
        CheckConstraint("length(sha256) = 64", name="ck_statement_source_sha256_length"),
        CheckConstraint("size_bytes >= 0", name="ck_statement_source_size_nonnegative"),
        CheckConstraint("page_count >= 1", name="ck_statement_source_page_count_positive"),
        CheckConstraint(
            "status in ('registered')", name="ck_statement_source_status"
        ),
    )

    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    text_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="registered")
    company_candidate: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stock_code_candidate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    period_candidate: Mapped[str | None] = mapped_column(String(64), nullable=True)
    report_kind_candidate: Mapped[str | None] = mapped_column(String(64), nullable=True)


class StatementNormalizedItem(CanonicalIdentityMixin, Base):
    """原始行 → 标准报表项目 item_id 的归一化结果（B03）。

    按 (report_id, mapping_version) 修订并存：同一映射版本重复归一幂等重建，
    新映射版本新增行集、旧版保留；原始行（statement_line_item）不受影响。
    """

    __tablename__ = "statement_normalized_item"
    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "mapping_version",
            "statement_type",
            "group_ordinal",
            "item_name",
            name="uq_statement_normalized_item",
        ),
        Index(
            "ix_statement_normalized_item_report",
            "report_id",
            "mapping_version",
            "statement_type",
        ),
    )

    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("statement_report.id", ondelete="CASCADE"),
        nullable=False,
    )
    mapping_version: Mapped[str] = mapped_column(String(32), nullable=False)
    statement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_ordinal: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("'0'")
    )
    item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    value_end: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    value_begin: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    value_current: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    value_prior: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    report: Mapped[StatementReport] = relationship()


class StatementCorrection(CanonicalIdentityMixin, Base):
    """人工修正审计（B05）：只增不改；发布后不得再新增。"""

    __tablename__ = "statement_correction"
    __table_args__ = (
        CheckConstraint(
            "column_key in ('value_end', 'value_begin', 'value_current', 'value_prior')",
            name="ck_statement_correction_column",
        ),
        Index(
            "ix_statement_correction_report",
            "report_id",
            "statement_type",
            "item_name",
        ),
    )

    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("statement_report.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    column_key: Mapped[str] = mapped_column(String(32), nullable=False)
    old_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    new_value: Mapped[Decimal | None] = mapped_column(Numeric(24, 4), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    operator: Mapped[str] = mapped_column(String(128), nullable=False)

    report: Mapped[StatementReport] = relationship(back_populates="corrections")


__all__ = [
    "StatementCorrection",
    "StatementLineItem",
    "StatementNormalizedItem",
    "StatementReport",
    "StatementSource",
]
