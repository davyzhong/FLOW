from flow_api.domain.enums import (
    BatchStatus,
    EvidenceStatus,
    FindingStatus,
    JobStatus,
    ObjectType,
    QualitySeverity,
)


def test_public_lifecycle_values_are_stable() -> None:
    assert [status.value for status in BatchStatus] == [
        "draft",
        "validating",
        "blocked",
        "ready",
        "published",
    ]
    assert [status.value for status in EvidenceStatus] == [
        "pending",
        "verified",
        "rejected",
    ]
    assert [status.value for status in FindingStatus] == [
        "candidate",
        "in_review",
        "approved",
        "rejected",
    ]
    assert [status.value for status in JobStatus] == [
        "queued",
        "running",
        "succeeded",
        "failed",
    ]
    assert [severity.value for severity in QualitySeverity] == ["blocking", "warning"]
    assert [object_type.value for object_type in ObjectType] == [
        "metric",
        "finding",
        "evidence",
        "source_record",
    ]
