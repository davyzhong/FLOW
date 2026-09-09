"""U7/P07：四问分析工作台 typed 只读端点（数据只来自归一化事实与主题合同）。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from flow_api.analysis.workbench import build_four_question_workbench
from flow_api.infrastructure.db import get_session_factory

router = APIRouter(prefix="/analysis", tags=["analysis"])


def get_workbench_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_workbench_session)]


@router.get("/workbench/{report_id}")
def get_workbench(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Any:
    """四问分析工作台：问题域导航 + 每问指标可用性与预计算值（U7/P07）。"""
    from flow_api.infrastructure.models.statement import StatementReport

    report = session.get(StatementReport, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "statement_report_not_found", "message": "财报不存在"},
        )
    return build_four_question_workbench(session, report_id=str(report.id))


__all__ = ["get_workbench_session", "router"]
