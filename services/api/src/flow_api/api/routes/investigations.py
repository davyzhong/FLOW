from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.investigation import (
    ConclusionResponse,
    ConclusionUpsertRequest,
    EvidenceDecisionRequest,
    EvidenceDecisionResponse,
    FindingListItem,
    FindingListResponse,
    FindingTransitionRequest,
    FindingTransitionResponse,
    InvestigationContextResponse,
    InvestigationErrorResponse,
    InvestigationSourceCellResponse,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot
from flow_api.infrastructure.models.canonical import FactArCollection, FactOperatingActual
from flow_api.infrastructure.models.intake import SourceFile, SourceRecord
from flow_api.investigation.repositories import (
    InvestigationIdentityMismatchError,
    InvestigationNotFoundError,
    InvestigationRepository,
)
from flow_api.investigation.service import InvestigationService
from flow_api.investigation.state_machines import ReviewBlockedError
from flow_api.security.authorization import Action
from flow_api.security.route_policy import (
    LOADERS,
    AuthorizationContext,
    require_action,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])


def get_investigation_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_investigation_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(status_code=http_status, detail=detail.model_dump(mode="json"))


@router.get(
    "",
    response_model=FindingListResponse,
    dependencies=[
        Depends(
            require_action(
                Action.INVESTIGATION_LIST,
                LOADERS["load_single_enterprise"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def list_findings(session: SessionDependency) -> FindingListResponse:
    """列出全部 Finding（含身份交接标识），供「分析与归因」入口选择调查对象。"""
    rows = session.execute(
        select(Finding, MetricSnapshot.batch_id)
        .join(MetricSnapshot, Finding.metric_snapshot_id == MetricSnapshot.id)
        .order_by(Finding.total_score.desc().nulls_last(), Finding.created_at.desc())
    ).all()
    return FindingListResponse(
        findings=[
            FindingListItem(
                finding_id=str(finding.id),
                title=finding.title,
                status=finding.status,
                finding_type=finding.finding_type,
                impact_amount=str(finding.impact_amount),
                comparison_basis=finding.comparison_basis,
                total_score=str(finding.total_score) if finding.total_score is not None else None,
                batch_id=str(batch_id) if batch_id else None,
                metric_snapshot_id=str(finding.metric_snapshot_id),
                analysis_run_id=(str(finding.analysis_run_id) if finding.analysis_run_id else None),
                created_at=(
                    finding.created_at.isoformat(timespec="seconds") if finding.created_at else None
                ),
            )
            for finding, batch_id in rows
        ]
    )


@router.get(
    "/{finding_id}",
    response_model=InvestigationContextResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
        status.HTTP_409_CONFLICT: {"model": InvestigationErrorResponse},
    },
    dependencies=[
        Depends(
            require_action(
                Action.INVESTIGATION_READ,
                LOADERS["load_finding_batch_scope_owner_or_deny_legacy"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def investigation_context(
    finding_id: UUID,
    session: SessionDependency,
    batch_id: Annotated[UUID | None, Query()] = None,
    metric_snapshot_id: Annotated[UUID | None, Query()] = None,
    analysis_run_id: Annotated[UUID | None, Query()] = None,
    source_record_limit: Annotated[int, Query(ge=1, le=100)] = 12,
) -> InvestigationContextResponse:
    try:
        context = InvestigationService().get_context(
            session,
            finding_id,
            batch_id=batch_id,
            metric_snapshot_id=metric_snapshot_id,
            analysis_run_id=analysis_run_id,
            source_record_limit=source_record_limit,
        )
    except InvestigationNotFoundError as error:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "investigation_not_found",
            str(error),
        ) from error
    except InvestigationIdentityMismatchError as error:
        raise _error(
            status.HTTP_409_CONFLICT,
            "investigation_identity_mismatch",
            str(error),
        ) from error
    return InvestigationContextResponse.model_validate(context.model_dump())


@router.get(
    "/{finding_id}/source-records/{fact_id}",
    response_model=InvestigationSourceCellResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse}},
    dependencies=[
        Depends(
            require_action(
                Action.INVESTIGATION_READ,
                LOADERS["load_finding_batch_scope_owner_or_deny_legacy"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def investigation_source_cell(
    finding_id: UUID,
    fact_id: UUID,
    session: SessionDependency,
) -> InvestigationSourceCellResponse:
    """在 Finding 的不可变导入血缘范围内读取源 Excel 单元格快照。"""
    try:
        binding = InvestigationRepository().load_binding(
            session,
            finding_id,
            batch_id=None,
            metric_snapshot_id=None,
            analysis_run_id=None,
        )
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error

    fact: FactOperatingActual | FactArCollection | None = session.scalar(
        select(FactOperatingActual).where(
            FactOperatingActual.id == fact_id,
            FactOperatingActual.import_version_id == binding.import_version.id,
        )
    )
    if fact is None:
        fact = session.scalar(
            select(FactArCollection).where(
                FactArCollection.id == fact_id,
                FactArCollection.import_version_id == binding.import_version.id,
            )
        )
    source_record = session.get(SourceRecord, fact.source_record_id) if fact else None
    source_file = session.get(SourceFile, source_record.source_file_id) if source_record else None
    if (
        fact is None
        or source_record is None
        or source_record.import_version_id != binding.import_version.id
        or source_file is None
        or source_file.batch_id != binding.snapshot.batch_id
    ):
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "source_record_not_found",
            "该来源单元格不属于当前调查的导入批次",
        )
    return InvestigationSourceCellResponse(
        fact_id=str(fact.id),
        source_file_name=source_file.original_filename,
        sheet_name=source_record.sheet_name,
        source_row=source_record.source_row,
        source_column=source_record.source_column,
        canonical_field=source_record.canonical_field,
        raw_value=source_record.raw_value,
        transformed_value=source_record.transformed_value,
    )


_DEP_EVIDENCE_DECIDE = require_action(
    Action.INVESTIGATION_EVIDENCE_DECIDE,
    LOADERS["load_finding_evidence_batch_scope_or_deny_legacy"],
    session_provider=get_investigation_session,
)


@router.post(
    "/{finding_id}/evidence/{evidence_id}/decision",
    response_model=EvidenceDecisionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
        status.HTTP_409_CONFLICT: {"model": InvestigationErrorResponse},
    },
    dependencies=[Depends(_DEP_EVIDENCE_DECIDE)],
)
def decide_evidence(
    finding_id: UUID,
    evidence_id: UUID,
    request: EvidenceDecisionRequest,
    session: SessionDependency,
    *,
    auth: Annotated[AuthorizationContext, Depends(_DEP_EVIDENCE_DECIDE)],
) -> EvidenceDecisionResponse:
    if request.reviewer is None:
        request = request.model_copy(update={"reviewer": auth.principal.actor_id})
    try:
        acknowledgement = InvestigationService().decide_evidence(
            session, finding_id, evidence_id, request
        )
    except ReviewBlockedError as error:
        raise _error(status.HTTP_409_CONFLICT, error.code, error.message) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return EvidenceDecisionResponse.model_validate(acknowledgement.model_dump())


@router.put(
    "/{finding_id}/conclusion",
    response_model=ConclusionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
    },
    dependencies=[
        Depends(
            require_action(
                Action.INVESTIGATION_CONCLUSION_WRITE,
                LOADERS["load_finding_batch_scope_or_deny_legacy"],
                session_provider=get_investigation_session,
            )
        )
    ],
)
def save_conclusion(
    finding_id: UUID,
    request: ConclusionUpsertRequest,
    session: SessionDependency,
) -> ConclusionResponse:
    try:
        acknowledgement = InvestigationService().save_conclusion(session, finding_id, request)
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return ConclusionResponse.model_validate(acknowledgement.model_dump())


_DEP_TRANSITION = require_action(
    Action.INVESTIGATION_TRANSITION,
    LOADERS["load_finding_batch_scope_or_deny_legacy"],
    session_provider=get_investigation_session,
)


@router.post(
    "/{finding_id}/transition",
    response_model=FindingTransitionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": InvestigationErrorResponse},
        status.HTTP_409_CONFLICT: {"model": InvestigationErrorResponse},
    },
    dependencies=[Depends(_DEP_TRANSITION)],
)
def transition_finding(
    finding_id: UUID,
    request: FindingTransitionRequest,
    session: SessionDependency,
    *,
    auth: Annotated[AuthorizationContext, Depends(_DEP_TRANSITION)],
) -> FindingTransitionResponse:
    if request.reviewer is None:
        request = request.model_copy(update={"reviewer": auth.principal.actor_id})
    try:
        acknowledgement = InvestigationService().transition_finding(session, finding_id, request)
    except ReviewBlockedError as error:
        raise _error(status.HTTP_409_CONFLICT, error.code, error.message) from error
    except InvestigationNotFoundError as error:
        raise _error(status.HTTP_404_NOT_FOUND, "investigation_not_found", str(error)) from error
    return FindingTransitionResponse.model_validate(acknowledgement.model_dump())


__all__ = ["get_investigation_session", "router"]
