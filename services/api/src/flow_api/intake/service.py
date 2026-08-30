from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.persistence import load_canonical_package
from flow_api.infrastructure.models.intake import (
    AnalysisBatch,
    ImportVersion,
    MappingVersion,
    QualityIssue,
    ReconciliationResult,
    SourceFile,
    StoredObject,
    WarningAcknowledgement,
)
from flow_api.intake.extractor import ExtractedCandidate
from flow_api.intake.mapping import MappingProposal
from flow_api.intake.quality import QualityReport
from flow_api.intake.repositories import IntakeRepository
from flow_api.intake.source_storage import StoredSource


class InvalidIntakeTransitionError(ValueError):
    pass


class PublicationBlockedError(ValueError):
    pass


class IntakeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = IntakeRepository(session)

    def create_batch(self, name: str, description: str | None = None) -> AnalysisBatch:
        if not name.strip():
            raise ValueError("batch name must not be empty")
        batch = AnalysisBatch(name=name.strip(), description=description, status="draft")
        self.session.add(batch)
        self.session.flush()
        return batch

    def attach_source(
        self,
        batch_id: UUID,
        stored: StoredSource,
        *,
        workbook_metadata: dict[str, Any] | None = None,
    ) -> SourceFile:
        batch = self.repository.batch(batch_id)
        stored_object = self.repository.stored_object_by_sha(stored.sha256)
        if stored_object is None:
            stored_object = StoredObject(
                sha256=stored.sha256,
                object_key=stored.object_key,
                size_bytes=stored.size_bytes,
                content_type=stored.content_type,
            )
            self.session.add(stored_object)
            self.session.flush()
        elif (
            stored_object.object_key != stored.object_key
            or stored_object.size_bytes != stored.size_bytes
            or stored_object.content_type != stored.content_type
        ):
            raise ValueError("stored source metadata conflicts with immutable object")
        existing = self.repository.source_for_object(batch.id, stored_object.id)
        if existing is not None:
            return existing
        source = SourceFile(
            batch=batch,
            stored_object=stored_object,
            original_filename=stored.original_filename,
            workbook_metadata=workbook_metadata or {},
        )
        self.session.add(source)
        self.session.flush()
        return source

    def propose_mapping(
        self,
        source_file_id: UUID,
        proposal: MappingProposal,
        *,
        actor: str = "system",
    ) -> MappingVersion:
        source = self.repository.source(source_file_id)
        if source.stored_object.sha256 != proposal.source_sha256:
            raise ValueError("mapping proposal does not match immutable source")
        existing = self.repository.mapping_by_hash(source.batch_id, proposal.mapping_hash)
        if existing is not None:
            return existing
        confidences = Counter(
            field.confidence for sheet in proposal.sheets for field in sheet.fields
        )
        mapping = MappingVersion(
            batch_id=source.batch_id,
            sequence=self.repository.next_mapping_sequence(source.batch_id),
            mapping_hash=proposal.mapping_hash,
            mapping_spec={
                **asdict(proposal),
                "_source_file_id": str(source.id),
            },
            confidence_summary=dict(confidences),
            rationale_summary={
                "unresolved_sheet_ids": list(proposal.unresolved_sheet_ids),
                "unresolved_required_fields": {
                    sheet.target_sheet_id: list(sheet.unresolved_required_fields)
                    for sheet in proposal.sheets
                    if sheet.unresolved_required_fields
                },
            },
            created_by=actor,
        )
        self.session.add(mapping)
        self.session.flush()
        return mapping

    def confirm_mapping(self, mapping_version_id: UUID, *, actor: str) -> MappingVersion:
        if not actor.strip():
            raise ValueError("mapping confirmation actor must not be empty")
        mapping = self.repository.mapping(mapping_version_id)
        spec = dict(mapping.mapping_spec)
        spec["confirmation"] = {
            "actor": actor.strip(),
            "confirmed_at": datetime.now(UTC).isoformat(),
        }
        mapping.mapping_spec = spec
        mapping.created_by = actor.strip()
        self.session.flush()
        return mapping

    def validate_import(
        self,
        source_file_id: UUID,
        mapping_version_id: UUID,
        candidate: ExtractedCandidate,
        report: QualityReport,
    ) -> ImportVersion:
        source = self.repository.source(source_file_id)
        mapping = self.repository.mapping(mapping_version_id)
        if source.batch_id != mapping.batch_id:
            raise ValueError("source and mapping belong to different batches")
        if candidate.source_sha256 != source.stored_object.sha256:
            raise ValueError("candidate does not match immutable source")
        existing = self.repository.candidate_for_source_mapping(source.id, mapping.id)
        if existing is not None:
            return existing
        batch = self.repository.batch(source.batch_id)
        version = ImportVersion(
            batch_id=batch.id,
            mapping_version_id=mapping.id,
            sequence=self.repository.next_import_sequence(batch.id),
            status="validating",
            is_published=False,
            summary={"source_file_id": str(source.id)},
        )
        self.session.add(version)
        self.session.flush()
        load_canonical_package(
            self.session,
            candidate.package,
            source,
            import_version=version,
            lineage_values=candidate.lineage,
        )
        self.session.add_all(
            [
                QualityIssue(
                    import_version_id=version.id,
                    source_file_id=source.id,
                    severity=issue.severity,
                    code=issue.code,
                    message=issue.message,
                    evidence=issue.evidence,
                    repair_suggestion=issue.repair_suggestion,
                    sheet_name=issue.location.source_sheet,
                    source_row=issue.location.source_row,
                    source_column=issue.location.source_column,
                )
                for issue in report.issues
            ]
        )
        self.session.add_all(
            [
                ReconciliationResult(
                    import_version_id=version.id,
                    reconciliation_code=check.code,
                    passed=check.passed,
                    expected_value=str(check.expected_value),
                    actual_value=str(check.actual_value),
                    details={
                        "difference": str(check.difference),
                        "tolerance": str(check.tolerance),
                        "description": check.details,
                    },
                )
                for check in report.reconciliations
            ]
        )
        version.status = "blocked" if report.blocking_issues else "ready"
        if self.repository.published_version(batch.id) is None:
            batch.status = version.status
        self.session.flush()
        return version

    def acknowledge_warning(
        self, quality_issue_id: UUID, *, actor: str, reason: str
    ) -> WarningAcknowledgement:
        if not actor.strip() or not reason.strip():
            raise ValueError("warning acknowledgement requires actor and reason")
        issue = self.session.get(QualityIssue, quality_issue_id)
        if issue is None:
            raise LookupError(f"quality issue not found: {quality_issue_id}")
        if issue.severity != "warning":
            raise PublicationBlockedError("blocking issues cannot be acknowledged")
        existing = self.session.scalar(
            select(WarningAcknowledgement).where(
                WarningAcknowledgement.quality_issue_id == issue.id
            )
        )
        if existing is not None:
            return existing
        acknowledgement = WarningAcknowledgement(
            quality_issue_id=issue.id,
            actor=actor.strip(),
            reason=reason.strip(),
        )
        self.session.add(acknowledgement)
        self.session.flush()
        return acknowledgement

    def publish_import(
        self,
        import_version_id: UUID,
        *,
        failure_hook: Callable[[], None] | None = None,
    ) -> ImportVersion:
        version = self.repository.import_version(import_version_id)
        if version.is_published:
            return version
        if version.status != "ready":
            raise InvalidIntakeTransitionError(
                f"only ready imports can be published, got {version.status}"
            )
        blocking_count = self.session.scalar(
            select(func.count())
            .select_from(QualityIssue)
            .where(
                QualityIssue.import_version_id == version.id,
                QualityIssue.severity == "blocking",
            )
        )
        unacknowledged_warning_count = self.session.scalar(
            select(func.count())
            .select_from(QualityIssue)
            .outerjoin(
                WarningAcknowledgement,
                WarningAcknowledgement.quality_issue_id == QualityIssue.id,
            )
            .where(
                QualityIssue.import_version_id == version.id,
                QualityIssue.severity == "warning",
                WarningAcknowledgement.id.is_(None),
            )
        )
        failed_reconciliation_count = self.session.scalar(
            select(func.count())
            .select_from(ReconciliationResult)
            .where(
                ReconciliationResult.import_version_id == version.id,
                ReconciliationResult.passed.is_(False),
            )
        )
        if blocking_count or failed_reconciliation_count:
            raise PublicationBlockedError("blocking quality or reconciliation issue remains")
        if unacknowledged_warning_count:
            raise PublicationBlockedError("all warnings must be acknowledged before publication")

        with self.session.begin_nested():
            previous = self.repository.published_version(version.batch_id)
            if previous is not None:
                previous.is_published = False
            version.is_published = True
            version.status = "published"
            version.published_at = datetime.now(UTC)
            batch = self.repository.batch(version.batch_id)
            batch.status = "published"
            self.session.flush()
            if failure_hook is not None:
                failure_hook()
        return version

    def create_correction(
        self,
        source_file_id: UUID,
        mapping_version_id: UUID,
        candidate: ExtractedCandidate,
        report: QualityReport,
    ) -> ImportVersion:
        return self.validate_import(source_file_id, mapping_version_id, candidate, report)
