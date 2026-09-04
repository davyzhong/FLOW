from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.data_contract.models import WorkbookContract
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
from flow_api.intake.mapping import (
    FieldMapping,
    MappingOverride,
    MappingProposal,
    SheetMapping,
    _source_type_compatible,
    proposal_from_spec,
)
from flow_api.intake.models import WorkbookProfile
from flow_api.intake.quality import QualityReport
from flow_api.intake.repositories import IntakeRepository
from flow_api.intake.source_storage import StoredSource


class InvalidIntakeTransitionError(ValueError):
    pass


class PublicationBlockedError(ValueError):
    pass


class MappingOverrideRuleError(ValueError):
    code = "mapping_override_invalid"
    http_status = 422


class UnknownMappingTargetError(MappingOverrideRuleError):
    code = "unknown_target"


class UnknownSourceColumnError(MappingOverrideRuleError):
    code = "unknown_source_column"


class DuplicateSourceColumnError(MappingOverrideRuleError):
    code = "duplicate_source_column"


class IncompatibleMappingTargetError(MappingOverrideRuleError):
    code = "incompatible_target"


class StaleSourceError(MappingOverrideRuleError):
    code = "stale_source"
    http_status = 409


class CrossBatchSourceError(MappingOverrideRuleError):
    code = "cross_batch_source"
    http_status = 409


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

    def apply_mapping_overrides(
        self,
        mapping_version_id: UUID,
        overrides: tuple[MappingOverride, ...],
        *,
        actor: str,
        contract: WorkbookContract,
        profile: WorkbookProfile,
        expected_source_file_id: UUID,
        expected_source_sha256: str,
    ) -> tuple[MappingVersion, MappingProposal]:
        """应用 Finance BP 手工映射修正：产生新的 MappingVersion（append-only）。

        规则：目标必须是冻结契约中的 sheet/field；源列必须是已 profile 的表头且类型
        兼容；同一目标工作表内不允许两个目标字段共用同一源列；请求必须引用映射的
        不可变源（hash 与批次一致）。
        """
        if not actor.strip():
            raise ValueError("mapping override actor must not be empty")
        if not overrides:
            raise ValueError("mapping override requires at least one override")
        mapping = self.repository.mapping(mapping_version_id)
        spec = dict(mapping.mapping_spec)
        source = self.repository.source(UUID(spec["_source_file_id"]))
        if expected_source_file_id != source.id:
            raise CrossBatchSourceError("override references a source from another batch")
        if expected_source_sha256 != source.stored_object.sha256:
            raise StaleSourceError("override was built against a stale source hash")

        proposal = proposal_from_spec(spec)
        sheet_contract_by_id = {sheet.sheet_id: sheet for sheet in contract.sheets}
        profile_sheets = {sheet.name: sheet for sheet in profile.sheets}
        fields_by_sheet: dict[str, dict[str, FieldMapping]] = {
            sheet.target_sheet_id: {field.target_field_id: field for field in sheet.fields}
            for sheet in proposal.sheets
        }
        unresolved_by_sheet = {
            sheet.target_sheet_id: set(sheet.unresolved_required_fields)
            for sheet in proposal.sheets
        }

        for override in overrides:
            sheet_contract = sheet_contract_by_id.get(override.target_sheet_id)
            if sheet_contract is None:
                raise UnknownMappingTargetError(
                    f"未知目标工作表: {override.target_sheet_id}"
                )
            field_contract = next(
                (
                    field
                    for field in sheet_contract.fields
                    if field.field_id == override.target_field_id
                ),
                None,
            )
            if field_contract is None:
                raise UnknownMappingTargetError(
                    f"未知目标字段: {override.target_sheet_id}.{override.target_field_id}"
                )
            profile_sheet = profile_sheets.get(override.source_sheet)
            if profile_sheet is None:
                raise UnknownSourceColumnError(
                    f"源工作簿不存在工作表: {override.source_sheet}"
                )
            column = next(
                (
                    column
                    for column in profile_sheet.columns
                    if column.header == override.source_header
                ),
                None,
            )
            if column is None:
                raise UnknownSourceColumnError(
                    f"源工作表 {override.source_sheet} 不存在表头: {override.source_header}"
                )
            if not _source_type_compatible(column, field_contract):
                raise IncompatibleMappingTargetError(
                    f"目标字段 {override.target_field_id} 与源列类型 "
                    f"{column.inferred_type} 不兼容"
                )
            fields_by_sheet[override.target_sheet_id][override.target_field_id] = FieldMapping(
                source_header=column.header,
                source_column=column.column_letter,
                target_field_id=override.target_field_id,
                method="manual_override",
                score=1.0,
                confidence="high",
                requires_confirmation=False,
                rationale="Finance BP 手工修正。",
            )
            unresolved_by_sheet[override.target_sheet_id].discard(override.target_field_id)

        for _target_sheet_id, fields in fields_by_sheet.items():
            used: dict[str, str] = {}
            for target_field_id, field in fields.items():
                if field.source_column in used:
                    raise DuplicateSourceColumnError(
                        f"{used[field.source_column]} 与 {target_field_id} 同时映射到源列 "
                        f"{field.source_column}"
                    )
                used[field.source_column] = target_field_id

        new_sheets = tuple(
            SheetMapping(
                source_sheet=sheet.source_sheet,
                target_sheet_id=sheet.target_sheet_id,
                method=sheet.method,
                score=sheet.score,
                fields=tuple(fields_by_sheet[sheet.target_sheet_id].values()),
                unresolved_required_fields=tuple(
                    sorted(unresolved_by_sheet[sheet.target_sheet_id])
                ),
                ignored_source_headers=sheet.ignored_source_headers,
            )
            for sheet in proposal.sheets
        )
        new_proposal = MappingProposal(
            contract_version=proposal.contract_version,
            source_sha256=proposal.source_sha256,
            sheets=new_sheets,
            unresolved_sheet_ids=proposal.unresolved_sheet_ids,
            ignored_source_sheets=proposal.ignored_source_sheets,
        )
        existing = self.repository.mapping_by_hash(mapping.batch_id, new_proposal.mapping_hash)
        if existing is not None:
            return existing, new_proposal

        confidences = Counter(
            field.confidence for sheet in new_proposal.sheets for field in sheet.fields
        )
        new_spec = {
            **asdict(new_proposal),
            "_source_file_id": spec["_source_file_id"],
            "confirmation": {
                "actor": actor.strip(),
                "confirmed_at": datetime.now(UTC).isoformat(),
            },
        }
        new_mapping = MappingVersion(
            batch_id=mapping.batch_id,
            sequence=self.repository.next_mapping_sequence(mapping.batch_id),
            mapping_hash=new_proposal.mapping_hash,
            mapping_spec=new_spec,
            confidence_summary=dict(confidences),
            rationale_summary={
                "unresolved_sheet_ids": list(new_proposal.unresolved_sheet_ids),
                "unresolved_required_fields": {
                    sheet.target_sheet_id: list(sheet.unresolved_required_fields)
                    for sheet in new_proposal.sheets
                    if sheet.unresolved_required_fields
                },
                "overrides": [asdict(override) for override in overrides],
            },
            created_by=actor.strip(),
        )
        self.session.add(new_mapping)
        self.session.flush()
        return new_mapping, new_proposal

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
