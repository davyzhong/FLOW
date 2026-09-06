"""报表分析 typed 只读 API：外部公开财报抽取数据的系统内入口。

数据边界：浏览器只消费本路由（或后续派生路由），不读取抽取 YAML 与原始 PDF。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.statement import (
    StatementErrorResponse,
    StatementLineResponse,
    StatementReportDetailResponse,
    StatementReportListResponse,
    StatementReportSummaryResponse,
    StatementSectionResponse,
    StatementSourceCandidatesResponse,
    StatementSourceListResponse,
    StatementSourceResponse,
    exact,
)
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.statement import StatementSource
from flow_api.infrastructure.object_store import ObjectStore
from flow_api.infrastructure.s3_client import build_s3_client
from flow_api.settings import get_settings
from flow_api.statements.intake import StatementSourceError, StatementSourceIntake
from flow_api.statements.repository import StatementReportUnavailableError
from flow_api.statements.service import StatementService

router = APIRouter(prefix="/statements", tags=["statements"])


def get_statement_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_statement_session)]

UPLOAD_CHUNK_SIZE = 1024 * 1024


def get_statement_source_intake() -> StatementSourceIntake:
    settings = get_settings()
    return StatementSourceIntake(
        ObjectStore(client=build_s3_client(settings), bucket=settings.s3_bucket),
        max_bytes=settings.statement_max_upload_bytes,
    )


IntakeDependency = Annotated[StatementSourceIntake, Depends(get_statement_source_intake)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(
        status_code=http_status,
        detail=detail.model_dump(mode="json"),
    )


def _source_response(source: StatementSource, *, duplicate: bool) -> StatementSourceResponse:
    return StatementSourceResponse(
        id=source.id,
        sha256=source.sha256,
        original_filename=source.original_filename,
        size_bytes=source.size_bytes,
        page_count=source.page_count,
        text_chars=source.text_chars,
        duplicate=duplicate,
        candidates=StatementSourceCandidatesResponse(
            company_name=source.company_candidate,
            stock_code=source.stock_code_candidate,
            period_label=source.period_candidate,
            report_kind=source.report_kind_candidate,
        ),
        created_at=source.created_at,
    )


@router.post(
    "/sources",
    response_model=StatementSourceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": StatementErrorResponse}},
)
async def upload_statement_source(
    session: SessionDependency,
    intake: IntakeDependency,
    workbook: Annotated[UploadFile, File(description="公开财报原文 PDF（仅支持文本 PDF）")],
) -> StatementSourceResponse:
    """登记公开财报原始文件：内容寻址不可变存储 + 幂等（同 sha256 返回既有登记）。"""
    filename = workbook.filename or "statement.pdf"
    maximum = get_settings().statement_max_upload_bytes
    content = bytearray()
    while chunk := await workbook.read(UPLOAD_CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > maximum:
            raise _error(
                status.HTTP_413_CONTENT_TOO_LARGE,
                "source_too_large",
                f"上传文件超过允许大小 {maximum} 字节",
            )
    try:
        source, created = intake.register(session, content=bytes(content), filename=filename)
    except StatementSourceError as error:
        raise _error(status.HTTP_422_UNPROCESSABLE_CONTENT, error.code, error.message) from error
    session.commit()
    return _source_response(source, duplicate=not created)


@router.get("/sources", response_model=StatementSourceListResponse)
def list_statement_sources(session: SessionDependency) -> StatementSourceListResponse:
    sources = session.scalars(
        select(StatementSource).order_by(StatementSource.created_at.desc())
    ).all()
    return StatementSourceListResponse(
        sources=tuple(_source_response(source, duplicate=False) for source in sources)
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
