"""指标库与会计基础对象（P3 落库，D040/D047）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.canonical import CanonicalIdentityMixin


class MetricDictionaryEntry(CanonicalIdentityMixin, Base):
    __tablename__ = "metric_dictionary_entry"

    dictionary_id: Mapped[str] = mapped_column(default="")
    collection: Mapped[str] = mapped_column()
    metric_code: Mapped[str] = mapped_column()
    version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(default="draft")
    name: Mapped[str] = mapped_column()
    domain: Mapped[str] = mapped_column()
    definition: Mapped[str] = mapped_column()
    formula_text: Mapped[str] = mapped_column()
    formula: Mapped[dict[str, Any]] = mapped_column(JSONB)
    unit: Mapped[str | None] = mapped_column(default=None)
    time_behavior: Mapped[str | None] = mapped_column(default=None)
    caliber: Mapped[str | None] = mapped_column(default=None)
    default_caliber: Mapped[str | None] = mapped_column(default=None)
    default_basis: Mapped[str | None] = mapped_column(default=None)
    alternative_calibers: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    source_cas: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    source_ifrs: Mapped[str | None] = mapped_column(default=None)
    depends_on: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    decompositions: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    aliases: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    benchmark: Mapped[str | None] = mapped_column(default=None)
    mpm: Mapped[bool] = mapped_column(default=False)
    reconciliation: Mapped[str | None] = mapped_column(default=None)
    migrates_from: Mapped[str | None] = mapped_column(default=None)
    provenance: Mapped[str | None] = mapped_column(default=None)


class AccountingStandard(CanonicalIdentityMixin, Base):
    __tablename__ = "accounting_standard"

    standard_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column()
    issuer: Mapped[str | None] = mapped_column(default=None)
    note: Mapped[str | None] = mapped_column(default=None)


class AccountingSubject(CanonicalIdentityMixin, Base):
    __tablename__ = "accounting_subject"

    code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column()
    category: Mapped[str] = mapped_column()
    balance_side: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    standard_ref: Mapped[str | None] = mapped_column(default=None)
    code_note: Mapped[str | None] = mapped_column(default=None)
    source_note: Mapped[str | None] = mapped_column(default=None)


class EntryTemplate(CanonicalIdentityMixin, Base):
    __tablename__ = "entry_template"

    template_id: Mapped[str] = mapped_column(unique=True)
    scenario: Mapped[str] = mapped_column()
    business_context: Mapped[str | None] = mapped_column(default=None)
    lines: Mapped[list[Any]] = mapped_column(JSONB)
    standard_ref: Mapped[str | None] = mapped_column(default=None)
    related_metrics: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    note: Mapped[str | None] = mapped_column(default=None)


class StatementLineMapping(CanonicalIdentityMixin, Base):
    __tablename__ = "statement_line_mapping"

    item_id: Mapped[str] = mapped_column(unique=True)
    cas_label: Mapped[str] = mapped_column()
    ifrs_label: Mapped[str | None] = mapped_column(default=None)
    subject_codes: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)
    metric_codes: Mapped[list[Any] | None] = mapped_column(JSONB, default=None)


__all__ = [
    "AccountingStandard",
    "AccountingSubject",
    "EntryTemplate",
    "MetricDictionaryEntry",
    "StatementLineMapping",
]
