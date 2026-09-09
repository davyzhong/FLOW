"""O2：经营轨六主题概览 typed 只读端点（D050/OP-0 分层，缺失不补造）。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_session_factory
from flow_api.operations.engine import OperationsOverview, build_operations_overview

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
