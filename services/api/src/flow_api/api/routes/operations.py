"""O2：经营轨六主题概览 typed 只读端点（D050/OP-0 分层，缺失不补造）。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_session_factory
from flow_api.operations.engine import OperationsOverview, build_operations_overview
from flow_api.publishing.objective_freeze import ObjectiveFreezeError

router = APIRouter(prefix="/operations", tags=["operations"])


def get_operations_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_operations_session)]


@router.get("/overview/{report_id}", response_model=OperationsOverview)
def get_operations_overview(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> OperationsOverview:
    """六主题经营概览：L1 出数，L2/L3 typed not_applicable（U 遗留/O2）。"""
    from flow_api.infrastructure.models.statement import StatementReport

    report = session.get(StatementReport, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "statement_report_not_found", "message": "财报不存在"},
        )
    return build_operations_overview(session, report_id=str(report.id))


__all__ = ["get_operations_session", "router"]


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
