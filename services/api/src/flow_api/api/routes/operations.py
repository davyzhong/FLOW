"""O2：经营轨六主题概览 typed 只读端点（D050/OP-0 分层，缺失不补造）。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.schemas.publishing import (
    PublicationAttemptLine,
    PublicationAttemptsResponse,
    PublishRequest,
    PublishResponse,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.intake import StoredObject
from flow_api.infrastructure.models.publishing import PublicationAttempt
from flow_api.infrastructure.models.statement import StatementReport
from flow_api.operations.engine import (
    OperationsOverview,
    OperationsSnapshotLine,
    OperationsSnapshotList,
    PublicOperatingPeriodList,
    build_operations_overview,
    build_public_operating_overview,
    list_public_operating_periods,
)
from flow_api.publishing.objective_freeze import (
    ObjectiveFreezeError,
    ObjectiveReportSnapshot,
)

router = APIRouter(prefix="/operations", tags=["operations"])


def get_operations_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_operations_session)]


@router.get("/public-periods", response_model=PublicOperatingPeriodList)
def get_public_operating_periods() -> PublicOperatingPeriodList:
    """列出公开经营事实的真实期间；不合成月度期间。"""

    return PublicOperatingPeriodList(periods=list_public_operating_periods())


@router.get("/public/{stock_code}/{period_label}", response_model=OperationsOverview)
def get_public_operating_overview(
    stock_code: Annotated[str, Path(max_length=32)],
    period_label: Annotated[str, Path(max_length=64)],
) -> OperationsOverview:
    """读取没有完整财报的公开经营期间，只呈现严格同期间事实。"""

    try:
        return build_public_operating_overview(stock_code=stock_code, selected_period=period_label)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "operating_period_not_found",
                "message": "未找到该公司的公开经营披露期间",
            },
        ) from error


@router.get("/overview/{report_id}", response_model=OperationsOverview)
def get_operations_overview(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> OperationsOverview:
    """六主题经营概览：L1 出数，L2/L3 typed not_applicable（U 遗留/O2）。"""
    report = session.get(StatementReport, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "statement_report_not_found", "message": "财报不存在"},
        )
    return build_operations_overview(session, report_id=str(report.id))


@router.get("/snapshots", response_model=OperationsSnapshotList)
def list_operations_snapshots(session: SessionDependency) -> OperationsSnapshotList:
    rows = session.execute(
        select(ObjectiveReportSnapshot, StatementReport)
        .join(
            StatementReport,
            ObjectiveReportSnapshot.statement_report_id == StatementReport.id,
        )
        .where(ObjectiveReportSnapshot.report_type == "operations_overview")
        .order_by(ObjectiveReportSnapshot.created_at.desc())
    ).all()
    return OperationsSnapshotList(
        snapshots=[
            OperationsSnapshotLine(
                id=str(snapshot.id),
                statement_report_id=str(report.id),
                version=snapshot.version,
                company_name=report.company_name,
                stock_code=report.stock_code,
                period_label=report.period_label,
                payload_hash=snapshot.payload_hash,
                created_at=(
                    snapshot.created_at.isoformat(timespec="seconds")
                    if snapshot.created_at
                    else None
                ),
            )
            for snapshot, report in rows
        ]
    )


@router.post("/overview/{report_id}/publish", response_model=PublishResponse)
def publish_operations_overview(
    session: SessionDependency,
    report_id: Annotated[UUID, Path()],
    request: PublishRequest,
) -> PublishResponse:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.publication import OperationsPublicationService

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
        outcomes = OperationsPublicationService().publish(
            session, snapshot.id, formats=tuple(request.formats)
        )
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return PublishResponse(report_snapshot_id=str(snapshot.id), outcomes=outcomes)


@router.get("/snapshots/{snapshot_id}/attempts", response_model=PublicationAttemptsResponse)
def operations_publication_attempts(
    session: SessionDependency, snapshot_id: Annotated[UUID, Path()]
) -> PublicationAttemptsResponse:
    snapshot = session.get(ObjectiveReportSnapshot, snapshot_id)
    if snapshot is None or snapshot.report_type != "operations_overview":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "operations_snapshot_not_found",
                "message": "经营报告快照不存在",
            },
        )
    attempts = session.scalars(
        select(PublicationAttempt)
        .where(PublicationAttempt.objective_report_snapshot_id == snapshot.id)
        .order_by(PublicationAttempt.sequence)
    ).all()
    lines: list[PublicationAttemptLine] = []
    for attempt in attempts:
        stored = (
            session.get(StoredObject, attempt.stored_object_id)
            if attempt.stored_object_id
            else None
        )
        lines.append(
            PublicationAttemptLine(
                attempt_id=str(attempt.id),
                sequence=attempt.sequence,
                format=attempt.format,
                status=attempt.status,
                stored_object_id=(
                    str(attempt.stored_object_id) if attempt.stored_object_id else None
                ),
                error_message=attempt.error_message,
                size_bytes=stored.size_bytes if stored else None,
                content_type=stored.content_type if stored else None,
                created_at=(
                    attempt.created_at.isoformat(timespec="seconds") if attempt.created_at else None
                ),
                download_available=attempt.status == "succeeded" and stored is not None,
                stored_sha256=stored.sha256 if stored else None,
            )
        )
    return PublicationAttemptsResponse(report_snapshot_id=str(snapshot.id), attempts=lines)


@router.post(
    "/overview/{report_id}/freeze",
    responses={404: {"content": {}}, 422: {"content": {}}},
)
def freeze_operations_snapshot(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> dict[str, str | int]:
    """六主题概览冻结：过 U5 客观资格合同后幂等落快照（O3 slice-2）。"""
    from flow_api.operations.freeze import freeze_operations_overview

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return {
        "snapshot_id": str(snapshot.id),
        "version": snapshot.version,
        "report_type": snapshot.report_type,
        "payload_hash": snapshot.payload_hash,
    }


@router.get(
    "/overview/{report_id}/html",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
)
def get_operations_overview_html(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_html

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    html = render_operations_html(snapshot.payload)
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"cache-control": "no-store", "x-content-type-options": "nosniff"},
    )


@router.get(
    "/overview/{report_id}/xlsx",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
)
def get_operations_overview_xlsx(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_xlsx

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return Response(
        content=render_operations_xlsx(snapshot.payload),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "content-disposition": 'attachment; filename="flow-operations.xlsx"',
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
    )


@router.get(
    "/overview/{report_id}/pptx",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
)
def get_operations_overview_pptx(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_pptx

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    return Response(
        content=render_operations_pptx(snapshot.payload),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "content-disposition": 'attachment; filename="flow-operations.pptx"',
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
    )


@router.get(
    "/overview/{report_id}/pdf",
    response_class=Response,
    responses={404: {"content": {}}, 422: {"content": {}}},
)
def get_operations_overview_pdf(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    import tempfile
    from pathlib import Path

    from flow_api.operations.freeze import freeze_operations_overview
    from flow_api.operations.renderers import render_operations_html
    from flow_api.statements.objective_report_pdf import print_pdf

    try:
        snapshot = freeze_operations_overview(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=http_status,
            detail={"code": error.code, "message": error.message},
        ) from error
    html = render_operations_html(snapshot.payload)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "operations.pdf"
        try:
            print_pdf(
                html,
                out_path=out,
                footer_left=f"FLOW 经营分析概览 · {snapshot.payload_hash[:16]}",
            )
            data = out.read_bytes()
        except RuntimeError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "chromium_unavailable", "message": str(error)},
            ) from error
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"cache-control": "no-store", "x-content-type-options": "nosniff"},
    )


__all__ = ["get_operations_session", "router"]
