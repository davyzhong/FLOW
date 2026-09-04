from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import UUID

import boto3  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import (
    BatchCreateRequest,
    BatchResponse,
    ColumnProfileResponse,
    ErrorDetail,
    FieldMappingResponse,
    ImportVersionResponse,
    IntakeStatus,
    MappingConfirmationRequest,
    MappingResponse,
    QualityIssueResponse,
    ReconciliationResponse,
    Severity,
    SheetMappingResponse,
    SheetProfileResponse,
    SourceResponse,
    ValidateImportRequest,
    VersionHistoryResponse,
    WarningAcknowledgementRequest,
    WarningAcknowledgementResponse,
    WorkbookProfileResponse,
)
from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.template import (
    TEMPLATE_FILENAME,
    TEMPLATE_ID,
    TEMPLATE_MIME,
    render_blank_template,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.intake import (
    ImportVersion,
    MappingVersion,
    QualityIssue,
    ReconciliationResult,
    SourceFile,
)
from flow_api.infrastructure.object_store import ObjectStore
from flow_api.intake.detector import WorkbookDetectionError, profile_workbook
from flow_api.intake.extractor import CandidateExtractionError, extract_candidate_package
from flow_api.intake.mapping import MappingProposal, load_aliases, propose_mapping
from flow_api.intake.quality import evaluate_quality
from flow_api.intake.service import (
    IntakeService,
    InvalidIntakeTransitionError,
    PublicationBlockedError,
)
from flow_api.intake.source_storage import SourceStorage, SourceStorageError
from flow_api.intake.transforms import load_transform_rules
from flow_api.settings import get_settings

router = APIRouter(prefix="/intake", tags=["intake"])
UPLOAD_CHUNK_SIZE = 1024 * 1024
INTAKE_CONFIGURATION_PATHS = (
    Path("templates/excel/flow_v1_contract.yaml"),
    Path("config/intake/flow_v1_aliases.yaml"),
    Path("config/intake/flow_v1_transforms.yaml"),
)


def resolve_intake_configuration_root(module_path: Path = Path(__file__)) -> Path:
    resolved_module_path = module_path.resolve()
    candidates = (resolved_module_path.parent, *resolved_module_path.parents)
    for candidate in candidates:
        if all(
            (candidate / relative_path).is_file()
            for relative_path in INTAKE_CONFIGURATION_PATHS
        ):
            return candidate
    raise RuntimeError(f"FLOW intake configuration files not found from {resolved_module_path}")


def get_db_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


@lru_cache
def get_source_storage() -> SourceStorage:
    settings = get_settings()
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
    )
    return SourceStorage(ObjectStore(client=client, bucket=settings.s3_bucket))


@lru_cache
def _intake_configuration() -> tuple[Any, Any, Any]:
    repository_root = resolve_intake_configuration_root()
    return (
        load_contract(repository_root / INTAKE_CONFIGURATION_PATHS[0]),
        load_aliases(repository_root / INTAKE_CONFIGURATION_PATHS[1]),
        load_transform_rules(repository_root / INTAKE_CONFIGURATION_PATHS[2]),
    )


SessionDependency = Annotated[Session, Depends(get_db_session)]
StorageDependency = Annotated[SourceStorage, Depends(get_source_storage)]


def _error(http_status: int, code: str, message: str, **details: Any) -> HTTPException:
    payload = ErrorDetail(code=code, message=message, details=details)
    return HTTPException(status_code=http_status, detail=payload.model_dump(mode="json"))


@router.get("/templates/{template_id}")
def download_template(template_id: str) -> Response:
    """下载治理化的空白标准工作簿模板（确定性字节输出）。"""
    if template_id != TEMPLATE_ID:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "template_not_found",
            f"未知模板: {template_id}",
            known_templates=[TEMPLATE_ID],
        )
    contract, _, _ = _intake_configuration()
    content = render_blank_template(contract)
    return Response(
        content=content,
        media_type=TEMPLATE_MIME,
        headers={
            "content-disposition": f'attachment; filename="{TEMPLATE_FILENAME}"',
            "cache-control": "no-store",
        },
    )


def _source(session: Session, source_file_id: UUID) -> SourceFile:
    source = session.get(SourceFile, source_file_id)
    if source is None:
        raise _error(status.HTTP_404_NOT_FOUND, "source_not_found", "源文件不存在")
    return source


def _mapping(session: Session, mapping_version_id: UUID) -> MappingVersion:
    mapping = session.get(MappingVersion, mapping_version_id)
    if mapping is None:
        raise _error(status.HTTP_404_NOT_FOUND, "mapping_not_found", "映射版本不存在")
    return mapping


def _source_bytes(source: SourceFile, storage: SourceStorage) -> bytes:
    return storage.read(source.stored_object.sha256)


def _deterministic_proposal(content: bytes) -> tuple[Any, MappingProposal]:
    contract, aliases, _ = _intake_configuration()
    profile = profile_workbook(content)
    return profile, propose_mapping(profile, contract, aliases)


def _mapping_response(mapping: MappingVersion, proposal: MappingProposal) -> MappingResponse:
    confirmation = mapping.mapping_spec.get("confirmation", {})
    confirmed_by = confirmation.get("actor") if isinstance(confirmation, dict) else None
    return MappingResponse(
        id=mapping.id,
        batch_id=mapping.batch_id,
        sequence=mapping.sequence,
        mapping_hash=mapping.mapping_hash or proposal.mapping_hash,
        contract_version=proposal.contract_version,
        sheets=[
            SheetMappingResponse(
                source_sheet=sheet.source_sheet,
                target_sheet_id=sheet.target_sheet_id,
                method=sheet.method,
                score=sheet.score,
                fields=[FieldMappingResponse(**asdict(field)) for field in sheet.fields],
                unresolved_required_fields=list(sheet.unresolved_required_fields),
                ignored_source_headers=list(sheet.ignored_source_headers),
            )
            for sheet in proposal.sheets
        ],
        unresolved_sheet_ids=list(proposal.unresolved_sheet_ids),
        ignored_source_sheets=list(proposal.ignored_source_sheets),
        confidence_summary={key: int(value) for key, value in mapping.confidence_summary.items()},
        confirmed_by=confirmed_by,
    )


def _version_response(session: Session, version: ImportVersion) -> ImportVersionResponse:
    issues = list(
        session.scalars(
            select(QualityIssue)
            .where(QualityIssue.import_version_id == version.id)
            .order_by(QualityIssue.severity, QualityIssue.code, QualityIssue.id)
        )
    )
    reconciliations = list(
        session.scalars(
            select(ReconciliationResult)
            .where(ReconciliationResult.import_version_id == version.id)
            .order_by(ReconciliationResult.reconciliation_code)
        )
    )
    if version.status == "ready":
        has_unacknowledged_warning = any(
            issue.severity == "warning" and issue.acknowledgement is None for issue in issues
        )
        actions = ["acknowledge_warnings", "publish"] if has_unacknowledged_warning else ["publish"]
    elif version.status == "blocked":
        actions = ["create_correction"]
    elif version.status == "published":
        actions = ["create_correction", "export"]
    else:
        actions = ["validate"]
    return ImportVersionResponse(
        id=version.id,
        batch_id=version.batch_id,
        mapping_version_id=version.mapping_version_id,
        sequence=version.sequence,
        status=cast(IntakeStatus, version.status),
        is_published=version.is_published,
        source_file_id=(
            UUID(version.summary["source_file_id"])
            if version.summary.get("source_file_id")
            else None
        ),
        issues=[
            QualityIssueResponse(
                id=issue.id,
                severity=cast(Severity, issue.severity),
                code=issue.code,
                message=issue.message,
                evidence=issue.evidence,
                repair_suggestion=issue.repair_suggestion,
                sheet_name=issue.sheet_name,
                source_row=issue.source_row,
                source_column=issue.source_column,
                acknowledged=issue.acknowledgement is not None,
            )
            for issue in issues
        ],
        reconciliations=[
            ReconciliationResponse(
                code=item.reconciliation_code,
                passed=item.passed,
                expected_value=item.expected_value,
                actual_value=item.actual_value,
                details=item.details,
            )
            for item in reconciliations
        ],
        next_allowed_actions=actions,
    )


@router.post("/batches", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(request: BatchCreateRequest, session: SessionDependency) -> BatchResponse:
    batch = IntakeService(session).create_batch(request.name, request.description)
    return BatchResponse.model_validate(batch, from_attributes=True)


@router.post(
    "/batches/{batch_id}/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_source(
    batch_id: UUID,
    session: SessionDependency,
    storage: StorageDependency,
    workbook: Annotated[UploadFile, File(description="Macro-free XLSX workbook")],
) -> SourceResponse:
    filename = workbook.filename or "source.xlsx"
    maximum = get_settings().intake_max_upload_bytes
    content = bytearray()
    while chunk := await workbook.read(UPLOAD_CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > maximum:
            raise _error(
                status.HTTP_413_CONTENT_TOO_LARGE,
                "source_too_large",
                "上传文件超过允许大小",
                maximum_bytes=maximum,
            )
    try:
        stored = storage.store(bytes(content), filename)
        source = IntakeService(session).attach_source(batch_id, stored)
    except LookupError as error:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "batch_not_found",
            str(error),
        ) from error
    except SourceStorageError as error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_source",
            str(error),
        ) from error
    return SourceResponse(
        id=source.id,
        batch_id=source.batch_id,
        filename=source.original_filename,
        sha256=stored.sha256,
        size_bytes=stored.size_bytes,
    )


@router.get("/sources/{source_file_id}/profile", response_model=WorkbookProfileResponse)
def get_profile(
    source_file_id: UUID, session: SessionDependency, storage: StorageDependency
) -> WorkbookProfileResponse:
    source = _source(session, source_file_id)
    try:
        profile = profile_workbook(_source_bytes(source, storage))
    except WorkbookDetectionError as error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "workbook_profile_failed",
            str(error),
        ) from error
    return WorkbookProfileResponse(
        source_file_id=source.id,
        sha256=profile.sha256,
        size_bytes=profile.size_bytes,
        sheet_count=profile.sheet_count,
        sheets=[
            SheetProfileResponse(
                name=sheet.name,
                header_row=sheet.header_row,
                data_start_row=sheet.data_start_row,
                data_end_row=sheet.data_end_row,
                data_row_count=sheet.data_row_count,
                columns=[
                    ColumnProfileResponse(
                        column=column.column_letter,
                        header=column.header,
                        stable_field_id=column.stable_field_id,
                        inferred_type=column.inferred_type,
                        nullable=column.nullable,
                        non_null_count=column.non_null_count,
                    )
                    for column in sheet.columns
                ],
            )
            for sheet in profile.sheets
        ],
    )


@router.post(
    "/sources/{source_file_id}/mapping-proposals",
    response_model=MappingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mapping_proposal(
    source_file_id: UUID, session: SessionDependency, storage: StorageDependency
) -> MappingResponse:
    source = _source(session, source_file_id)
    try:
        _, proposal = _deterministic_proposal(_source_bytes(source, storage))
    except WorkbookDetectionError as error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "workbook_mapping_failed",
            str(error),
        ) from error
    mapping = IntakeService(session).propose_mapping(source.id, proposal)
    return _mapping_response(mapping, proposal)


@router.post("/mappings/{mapping_version_id}/confirm", response_model=MappingResponse)
def confirm_mapping(
    mapping_version_id: UUID,
    request: MappingConfirmationRequest,
    session: SessionDependency,
    storage: StorageDependency,
) -> MappingResponse:
    mapping = _mapping(session, mapping_version_id)
    source_id = mapping.mapping_spec.get("_source_file_id")
    source = session.get(SourceFile, UUID(source_id)) if isinstance(source_id, str) else None
    if source is None:
        raise _error(status.HTTP_409_CONFLICT, "source_missing", "映射版本没有可用源文件")
    _, proposal = _deterministic_proposal(_source_bytes(source, storage))
    if mapping.mapping_hash != proposal.mapping_hash:
        raise _error(status.HTTP_409_CONFLICT, "mapping_source_mismatch", "映射与源文件不匹配")
    confirmed = IntakeService(session).confirm_mapping(mapping.id, actor=request.actor)
    return _mapping_response(confirmed, proposal)


@router.post("/sources/{source_file_id}/validate", response_model=ImportVersionResponse)
def validate_source(
    source_file_id: UUID,
    request: ValidateImportRequest,
    session: SessionDependency,
    storage: StorageDependency,
) -> ImportVersionResponse:
    source = _source(session, source_file_id)
    mapping = _mapping(session, request.mapping_version_id)
    content = _source_bytes(source, storage)
    profile, proposal = _deterministic_proposal(content)
    if mapping.batch_id != source.batch_id or mapping.mapping_hash != proposal.mapping_hash:
        raise _error(status.HTTP_409_CONFLICT, "mapping_source_mismatch", "映射与源文件不匹配")
    contract, _, transforms = _intake_configuration()
    try:
        candidate = extract_candidate_package(content, profile, proposal, contract, transforms)
    except CandidateExtractionError as error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "candidate_extraction_failed",
            str(error),
            failed_value_count=len(error.failed_lineage),
        ) from error
    report = evaluate_quality(candidate.package, contract, proposal)
    version = IntakeService(session).validate_import(source.id, mapping.id, candidate, report)
    return _version_response(session, version)


@router.post(
    "/issues/{quality_issue_id}/acknowledge",
    response_model=WarningAcknowledgementResponse,
)
def acknowledge_warning(
    quality_issue_id: UUID,
    request: WarningAcknowledgementRequest,
    session: SessionDependency,
) -> WarningAcknowledgementResponse:
    try:
        acknowledgement = IntakeService(session).acknowledge_warning(
            quality_issue_id, actor=request.actor, reason=request.reason
        )
    except LookupError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "issue_not_found", str(error)) from error
    except PublicationBlockedError as error:
        raise _error(status.HTTP_409_CONFLICT, "issue_not_acknowledgeable", str(error)) from error
    return WarningAcknowledgementResponse.model_validate(acknowledgement, from_attributes=True)


@router.post("/imports/{import_version_id}/publish", response_model=ImportVersionResponse)
def publish_import(import_version_id: UUID, session: SessionDependency) -> ImportVersionResponse:
    try:
        version = IntakeService(session).publish_import(import_version_id)
    except LookupError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "import_not_found", str(error)) from error
    except (InvalidIntakeTransitionError, PublicationBlockedError) as error:
        raise _error(status.HTTP_409_CONFLICT, "publication_blocked", str(error)) from error
    return _version_response(session, version)


@router.get("/batches/{batch_id}/versions", response_model=VersionHistoryResponse)
def version_history(batch_id: UUID, session: SessionDependency) -> VersionHistoryResponse:
    versions = list(
        session.scalars(
            select(ImportVersion)
            .where(ImportVersion.batch_id == batch_id)
            .order_by(ImportVersion.sequence)
        )
    )
    if not versions:
        raise _error(status.HTTP_404_NOT_FOUND, "batch_not_found", "批次不存在或尚无导入版本")
    return VersionHistoryResponse(
        batch_id=batch_id,
        versions=[_version_response(session, version) for version in versions],
    )
