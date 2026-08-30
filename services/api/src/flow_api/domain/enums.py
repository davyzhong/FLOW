from enum import StrEnum


class BatchStatus(StrEnum):
    DRAFT = "draft"
    VALIDATING = "validating"
    BLOCKED = "blocked"
    READY = "ready"
    PUBLISHED = "published"


class EvidenceStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class FindingStatus(StrEnum):
    CANDIDATE = "candidate"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class QualitySeverity(StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"


class ObjectType(StrEnum):
    METRIC = "metric"
    FINDING = "finding"
    EVIDENCE = "evidence"
    SOURCE_RECORD = "source_record"
