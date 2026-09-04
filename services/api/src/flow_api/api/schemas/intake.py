from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

IntakeStatus = Literal["draft", "validating", "blocked", "ready", "published"]
Severity = Literal["blocking", "warning"]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class BatchCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class BatchResponse(BaseModel):
    id: UUID
    name: str
    status: IntakeStatus
    description: str | None


class SourceResponse(BaseModel):
    id: UUID
    batch_id: UUID
    filename: str
    sha256: str
    size_bytes: int


class ColumnProfileResponse(BaseModel):
    column: str
    header: str
    stable_field_id: str | None
    inferred_type: str
    nullable: bool
    non_null_count: int


class SheetProfileResponse(BaseModel):
    name: str
    header_row: int | None
    data_start_row: int | None
    data_end_row: int | None
    data_row_count: int
    columns: list[ColumnProfileResponse]


class WorkbookProfileResponse(BaseModel):
    source_file_id: UUID
    sha256: str
    size_bytes: int
    sheet_count: int
    sheets: list[SheetProfileResponse]


class FieldMappingResponse(BaseModel):
    source_header: str
    source_column: str
    target_field_id: str
    method: str
    score: float
    confidence: str
    requires_confirmation: bool
    rationale: str


class SheetMappingResponse(BaseModel):
    source_sheet: str
    target_sheet_id: str
    method: str
    score: float
    fields: list[FieldMappingResponse]
    unresolved_required_fields: list[str]
    ignored_source_headers: list[str]


class MappingResponse(BaseModel):
    id: UUID
    batch_id: UUID
    sequence: int
    mapping_hash: str
    contract_version: str
    sheets: list[SheetMappingResponse]
    unresolved_sheet_ids: list[str]
    ignored_source_sheets: list[str]
    confidence_summary: dict[str, int]
    confirmed_by: str | None = None


class MappingConfirmationRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=255)


class MappingOverrideItem(BaseModel):
    target_sheet_id: str = Field(min_length=1)
    target_field_id: str = Field(min_length=1)
    source_sheet: str = Field(min_length=1)
    source_header: str = Field(min_length=1)


class MappingOverrideRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=255)
    source_file_id: UUID
    source_sha256: str = Field(min_length=64, max_length=64)
    overrides: list[MappingOverrideItem] = Field(min_length=1)


class ValidateImportRequest(BaseModel):
    mapping_version_id: UUID


class WarningAcknowledgementRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1)


class WarningAcknowledgementResponse(BaseModel):
    id: UUID
    quality_issue_id: UUID
    actor: str
    reason: str


class QualityIssueResponse(BaseModel):
    id: UUID
    severity: Severity
    code: str
    message: str
    evidence: str
    repair_suggestion: str
    sheet_name: str | None
    source_row: int | None
    source_column: str | None
    acknowledged: bool


class ReconciliationResponse(BaseModel):
    code: str
    passed: bool
    expected_value: str | None
    actual_value: str | None
    details: dict[str, Any]


class ImportVersionResponse(BaseModel):
    id: UUID
    batch_id: UUID
    mapping_version_id: UUID | None
    sequence: int
    status: IntakeStatus
    is_published: bool
    source_file_id: UUID | None
    issues: list[QualityIssueResponse]
    reconciliations: list[ReconciliationResponse]
    next_allowed_actions: list[str]


class VersionHistoryResponse(BaseModel):
    batch_id: UUID
    versions: list[ImportVersionResponse]
