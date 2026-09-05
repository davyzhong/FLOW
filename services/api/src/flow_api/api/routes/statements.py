"""报表分析 typed 只读 API：外部公开财报抽取数据的系统内入口。

数据边界：浏览器只消费本路由（或后续派生路由），不读取抽取 YAML 与原始 PDF。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.statement import (
    StatementErrorResponse,
    StatementLineResponse,
    StatementReportDetailResponse,
    StatementReportListResponse,
    StatementReportSummaryResponse,
    StatementSectionResponse,
    exact,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.statements.repository import StatementReportUnavailableError
from flow_api.statements.service import StatementService

router = APIRouter(prefix="/statements", tags=["statements"])


def get_statement_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_statement_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(
        status_code=http_status,
        detail=detail.model_dump(mode="json"),
    )


@router.get(
    "",
    response_model=StatementReportListResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": StatementErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": StatementErrorResponse},
    },
)
def list_statement_reports(session: SessionDependency) -> StatementReportListResponse:
    listing = StatementService().list_reports(session)
    return StatementReportListResponse(
        reports=tuple(
            StatementReportSummaryResponse.model_validate(summary.model_dump())
            for summary in listing.reports
        )
    )


@router.get(
    "/{report_id}",
    response_model=StatementReportDetailResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": StatementErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": StatementErrorResponse},
    },
)
def get_statement_report(
    session: SessionDependency,
    report_id: Annotated[UUID, Path()],
) -> StatementReportDetailResponse:
    try:
        detail = StatementService().get_report(session, report_id)
    except StatementReportUnavailableError as error:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            error.code,
            "指定的财报报告不存在",
        ) from error
    return StatementReportDetailResponse(
        **detail.model_dump(exclude={"sections"}),
        sections=tuple(
            StatementSectionResponse(
                statement_type=section.statement_type,
                items=tuple(
                    StatementLineResponse(
                        item_name=line.item_name,
                        sort_order=line.sort_order,
                        value_end=exact(line.value_end),
                        value_begin=exact(line.value_begin),
                        value_current=exact(line.value_current),
                        value_prior=exact(line.value_prior),
                    )
                    for line in section.items
                ),
            )
            for section in detail.sections
        ),
    )


__all__ = ["get_statement_session", "router"]
