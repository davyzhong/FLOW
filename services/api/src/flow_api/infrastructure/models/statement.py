"""外部公开财报抽取数据（P5 反向解析验证）的落库模型。

报表项目按披露原文的列式存储四类可空数值列，不换算单位；
单位与来源随 statement_report 记录，保持原始值不可变原则。
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
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
            name="uq_statement_report_identity",
        ),
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stock_code: Mapped[str] = mapped_column(String(32), nullable=False)
    report_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    period_label: Mapped[str] = mapped_column(String(64), nullable=False)
    unit_note: Mapped[str] = mapped_column(String(64), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(512), nullable=False)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    items: Mapped[list[StatementLineItem]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="StatementLineItem.statement_type, StatementLineItem.sort_order",
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


__all__ = ["StatementLineItem", "StatementReport", "StatementSource"]
