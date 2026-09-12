"""U6 切片二补充：客观报告快照（冻结载荷）typed 端点。

GET /api/v1/statements/{report_id}/objective-snapshot
  返回冻结载荷摘要（身份 + 黄金值 + statements 计数），供报告中心展示。
POST /api/v1/statements/{report_id}/objective-snapshot
  幂等冻结（内容哈希同则复用）。
GET /api/v1/statements/{report_id}/objective-snapshot/html
  从冻结载荷渲染 HTML（真渲染非占位）。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.api.schemas.statement import StatementErrorResponse
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.logging import log_event
from flow_api.publishing.objective_freeze import (
    ObjectiveFreezeError,
    ObjectiveReportSnapshot,
    freeze_objective_statement_report,
)

router = APIRouter(prefix="/statements", tags=["statements"])


def get_objective_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_objective_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail=ErrorDetail(code=code, message=message).model_dump(mode="json"),
    )


def _freeze_or_error(session: Session, report_id: UUID) -> ObjectiveReportSnapshot:
    try:
        return freeze_objective_statement_report(session, report_id=report_id)
    except ObjectiveFreezeError as error:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if error.code == "statement_report_not_found"
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise _error(http_status, error.code, error.message) from error


@router.get(
    "/{report_id}/objective-snapshot",
    response_model=None,
    responses={404: {"model": StatementErrorResponse}, 409: {"model": StatementErrorResponse}},
)
def get_objective_snapshot(session: SessionDependency, report_id: Annotated[UUID, Path()]) -> Any:
    snapshot = _freeze_or_error(session, report_id)
    payload = snapshot.payload
    source = payload.get("source", {})
    statements = payload.get("statements", {})
    golden: dict[str, Any] = {}
    for statement_rows in statements.values():
        for row in statement_rows:
            item = row.get("item", "")
            if item.startswith("一、营业总收入"):
                golden["revenue_current"] = row.get("value_current")
            if item.startswith("五、净利润"):
                golden["net_profit_current"] = row.get("value_current")
    return {
        "snapshot_id": str(snapshot.id),
        "version": snapshot.version,
        "schema_version": snapshot.schema_version,
        "report_type": snapshot.report_type,
        "payload_hash": snapshot.payload_hash,
        "source": source,
        "golden": golden,
        "statements_count": {
            name: len(rows) for name, rows in statements.items()
        },
    }


@router.post(
    "/{report_id}/objective-snapshot",
    responses={404: {"model": StatementErrorResponse}, 422: {"model": StatementErrorResponse}},
)
def freeze_objective_snapshot(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Any:
    snapshot = _freeze_or_error(session, report_id)
    log_event(
        logging.getLogger("flow.objective"),
        logging.INFO,
        "objective.snapshot_frozen",
        report_id=str(report_id),
        snapshot_id=str(snapshot.id),
        payload_hash=snapshot.payload_hash,
    )
    return {
        "snapshot_id": str(snapshot.id),
        "version": snapshot.version,
        "payload_hash": snapshot.payload_hash,
    }


@router.get(
    "/{report_id}/objective-snapshot/html",
    response_class=Response,
    responses={404: {"model": StatementErrorResponse}, 409: {"model": StatementErrorResponse}},
)
def get_objective_snapshot_html(
    session: SessionDependency, report_id: Annotated[UUID, Path()]
) -> Response:
    from flow_api.publishing.objective_renderers import render_html_from_payload

    snapshot = _freeze_or_error(session, report_id)
    html = render_html_from_payload(snapshot.payload)
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
        },
    )


__all__ = ["get_objective_session", "router"]
