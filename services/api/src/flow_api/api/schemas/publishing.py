"""Public typed schemas for the unified publishing API."""

from pydantic import BaseModel, Field

from flow_api.api.schemas.intake import ErrorDetail


class PublishRequest(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["pptx", "xlsx", "html", "pdf"])
    actor: str = Field(min_length=1)


class PublishResponse(BaseModel):
    report_snapshot_id: str
    outcomes: dict[str, str]


class PublicationAttemptLine(BaseModel):
    attempt_id: str
    sequence: int
    format: str
    status: str
    stored_object_id: str | None
    error_message: str | None
    size_bytes: int | None = None
    content_type: str | None = None
    created_at: str | None = None
    download_available: bool = False
    stored_sha256: str | None = None


class PublicationAttemptsResponse(BaseModel):
    report_snapshot_id: str
    attempts: list[PublicationAttemptLine]


class ReportSnapshotFreezeRequest(BaseModel):
    metric_snapshot_id: str = Field(min_length=1)


class ReportSnapshotCreatedResponse(BaseModel):
    id: str
    metric_snapshot_id: str
    version: int
    title: str
    created_at: str | None = None


class ReportSnapshotLine(BaseModel):
    id: str
    metric_snapshot_id: str
    version: int
    title: str
    created_at: str | None = None


class ReportSnapshotListResponse(BaseModel):
    snapshots: list[ReportSnapshotLine]


class PublishingErrorResponse(BaseModel):
    detail: ErrorDetail


__all__ = [
    "PublishRequest",
    "PublishResponse",
    "PublicationAttemptLine",
    "PublicationAttemptsResponse",
    "ReportSnapshotFreezeRequest",
    "ReportSnapshotLine",
    "ReportSnapshotListResponse",
    "PublishingErrorResponse",
]
