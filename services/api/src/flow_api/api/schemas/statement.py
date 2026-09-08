"""报表分析 typed API 响应模型（数值以精确十进制字符串跨 JSON）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from flow_api.api.schemas.intake import ErrorDetail


class FrozenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StatementLineResponse(FrozenResponse):
    item_name: str
    sort_order: int
    value_end: str | None = None
    value_begin: str | None = None
    value_current: str | None = None
    value_prior: str | None = None


class StatementSectionResponse(FrozenResponse):
    statement_type: str
    items: tuple[StatementLineResponse, ...]


class StatementReportSummaryResponse(FrozenResponse):
    id: UUID
    company_name: str
    stock_code: str
    report_kind: str
    period_label: str
    version: int = 1
    status: str = "draft"
    unit_note: str
    source_ref: str
    source_sha256: str | None = None
    statement_types: tuple[str, ...]
    line_item_count: int
    created_at: datetime


class StatementReportDetailResponse(StatementReportSummaryResponse):
    sections: tuple[StatementSectionResponse, ...]


class StatementReportListResponse(FrozenResponse):
    reports: tuple[StatementReportSummaryResponse, ...]


class StatementErrorResponse(FrozenResponse):
    detail: ErrorDetail


class ProvenancePointResponse(FrozenResponse):
    item_id: str
    statement_type: str
    item_name: str
    role: str
    source_sha256: str | None = None
    trace: dict[str, Any] | None = None


class ProjectionEntryResponse(FrozenResponse):
    entry_id: str
    name: str
    status: str
    value: str | None = None
    caliber: str | None = None
    provenance: tuple[ProvenancePointResponse, ...] = ()


class SnapshotIdentityResponse(FrozenResponse):
    report_id: str
    mapping_version: str


class TopicProjectionResponse(FrozenResponse):
    identity: SnapshotIdentityResponse
    catalog_id: str
    unit_note: str
    entries: tuple[ProjectionEntryResponse, ...]


StatementErrorCode = Literal[
    "statement_report_not_found",
]


def exact(value: object | None) -> str | None:
    """Numeric/Decimal → 精确十进制字符串（跨 JSON 不丢精度）。"""

    if value is None:
        return None
    return format(value, "f")


class StatementSourceCandidatesResponse(FrozenResponse):
    company_name: str | None = None
    stock_code: str | None = None
    period_label: str | None = None
    report_kind: str | None = None


class StatementSourceResponse(FrozenResponse):
    id: UUID
    sha256: str
    original_filename: str
    size_bytes: int
    page_count: int
    text_chars: int
    duplicate: bool
    candidates: StatementSourceCandidatesResponse
    created_at: datetime


class StatementSourceListResponse(FrozenResponse):
    sources: tuple[StatementSourceResponse, ...]


class CorrectionCreateRequest(BaseModel):
    statement_type: str = Field(min_length=1)
    item_name: str = Field(min_length=1)
    column_key: str = Field(min_length=1)
    value: str
    reason: str = Field(min_length=1)
    operator: str = Field(min_length=1)


class CorrectionResponse(FrozenResponse):
    id: UUID
    report_id: UUID
    statement_type: str
    item_name: str
    column_key: str
    old_value: str | None = None
    new_value: str | None = None
    reason: str
    operator: str
    created_at: datetime


class CorrectionListResponse(FrozenResponse):
    corrections: tuple[CorrectionResponse, ...]


class StatementPublishResponse(FrozenResponse):
    id: UUID
    status: str
