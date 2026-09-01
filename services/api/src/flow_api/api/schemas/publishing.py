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
    sequence: int
    format: str
    status: str
    stored_object_id: str | None
    error_message: str | None


class PublicationAttemptsResponse(BaseModel):
    report_snapshot_id: str
    attempts: list[PublicationAttemptLine]


class PublishingErrorResponse(BaseModel):
    detail: ErrorDetail


__all__ = [
    "PublishRequest",
    "PublishResponse",
    "PublicationAttemptLine",
    "PublicationAttemptsResponse",
    "PublishingErrorResponse",
]
