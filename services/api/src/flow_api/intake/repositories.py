from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    MappingVersion,
    SourceFile,
    StoredObject,
)


class IntakeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def batch(self, batch_id: UUID) -> AnalysisBatch:
        batch = self.session.get(AnalysisBatch, batch_id)
        if batch is None:
            raise LookupError(f"analysis batch not found: {batch_id}")
        return batch

    def source(self, source_file_id: UUID) -> SourceFile:
        source = self.session.get(SourceFile, source_file_id)
        if source is None:
            raise LookupError(f"source file not found: {source_file_id}")
        return source

    def mapping(self, mapping_version_id: UUID) -> MappingVersion:
        mapping = self.session.get(MappingVersion, mapping_version_id)
        if mapping is None:
            raise LookupError(f"mapping version not found: {mapping_version_id}")
        return mapping

    def import_version(self, import_version_id: UUID) -> ImportVersion:
        version = self.session.get(ImportVersion, import_version_id)
        if version is None:
            raise LookupError(f"import version not found: {import_version_id}")
        return version

    def next_mapping_sequence(self, batch_id: UUID) -> int:
        current = self.session.scalar(
            select(func.coalesce(func.max(MappingVersion.sequence), 0)).where(
                MappingVersion.batch_id == batch_id
            )
        )
        return int(current or 0) + 1

    def next_import_sequence(self, batch_id: UUID) -> int:
        current = self.session.scalar(
            select(func.coalesce(func.max(ImportVersion.sequence), 0)).where(
                ImportVersion.batch_id == batch_id
            )
        )
        return int(current or 0) + 1

    def stored_object_by_sha(self, sha256: str) -> StoredObject | None:
        return self.session.scalar(select(StoredObject).where(StoredObject.sha256 == sha256))

    def source_for_object(self, batch_id: UUID, stored_object_id: UUID) -> SourceFile | None:
        return self.session.scalar(
            select(SourceFile).where(
                SourceFile.batch_id == batch_id,
                SourceFile.stored_object_id == stored_object_id,
            )
        )

    def mapping_by_hash(self, batch_id: UUID, mapping_hash: str) -> MappingVersion | None:
        return self.session.scalar(
            select(MappingVersion).where(
                MappingVersion.batch_id == batch_id,
                MappingVersion.mapping_hash == mapping_hash,
            )
        )

    def candidate_for_source_mapping(
        self, source_file_id: UUID, mapping_version_id: UUID
    ) -> ImportVersion | None:
        return self.session.scalar(
            select(ImportVersion).where(
                ImportVersion.mapping_version_id == mapping_version_id,
                ImportVersion.summary["source_file_id"].astext == str(source_file_id),
            )
        )

    def published_version(self, batch_id: UUID) -> ImportVersion | None:
        return self.session.scalar(
            select(ImportVersion).where(
                ImportVersion.batch_id == batch_id,
                ImportVersion.is_published.is_(True),
            )
        )
