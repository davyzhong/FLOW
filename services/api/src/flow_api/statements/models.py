"""报表分析领域模型（frozen，Decimal 禁止 float）。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, TypeAdapter


def _reject_float(value: Any) -> Any:
    if isinstance(value, float):
        raise ValueError("报表数值禁止二进制浮点，请使用字符串或 int/Decimal")
    return value


StrictDecimal = Annotated[Decimal, BeforeValidator(_reject_float)]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StatementLine(FrozenModel):
    item_name: str
    sort_order: int
    value_end: StrictDecimal | None = None
    value_begin: StrictDecimal | None = None
    value_current: StrictDecimal | None = None
    value_prior: StrictDecimal | None = None


class StatementSection(FrozenModel):
    statement_type: str
    items: tuple[StatementLine, ...]


class StatementReportSummary(FrozenModel):
    id: UUID
    company_name: str
    stock_code: str
    report_kind: str
    period_label: str
    unit_note: str
    source_ref: str
    source_sha256: str | None = None
    statement_types: tuple[str, ...]
    line_item_count: int
    created_at: datetime


class StatementReportDetail(StatementReportSummary):
    sections: tuple[StatementSection, ...]


class StatementReportList(FrozenModel):
    reports: tuple[StatementReportSummary, ...]


_DECIMAL_TEXT = TypeAdapter(Decimal)


def as_exact_string(value: Decimal | None) -> str | None:
    """数据库 Numeric 的精确十进制字符串表示（跨 JSON 不丢精度）。"""

    if value is None:
        return None
    return format(value, "f")
