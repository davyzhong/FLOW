from typing import NewType
from uuid import UUID

from uuid6 import uuid7

BatchId = NewType("BatchId", UUID)
SourceFileId = NewType("SourceFileId", UUID)
ImportVersionId = NewType("ImportVersionId", UUID)
MetricDefinitionId = NewType("MetricDefinitionId", str)
MetricSnapshotId = NewType("MetricSnapshotId", UUID)
FindingId = NewType("FindingId", UUID)
EvidenceId = NewType("EvidenceId", UUID)
ReportSnapshotId = NewType("ReportSnapshotId", UUID)
PublicationId = NewType("PublicationId", UUID)


def new_uuid7() -> UUID:
    """Create a monotonically ordered RFC 9562 UUIDv7."""
    return uuid7()
