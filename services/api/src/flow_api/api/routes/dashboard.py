from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.dashboard import (
    DashboardErrorResponse,
    DashboardOverviewResponse,
)
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.repositories import DashboardSourceUnavailableError
from flow_api.dashboard.service import DashboardFilterError, DashboardService
from flow_api.infrastructure.db import get_session_factory

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_dashboard_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    detail = ErrorDetail(code=code, message=message)
    return HTTPException(
        status_code=http_status,
        detail=detail.model_dump(mode="json"),
    )


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": DashboardErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": DashboardErrorResponse},
    },
)
def dashboard_overview(
    session: SessionDependency,
    period_view: Annotated[Literal["month", "ytd"], Query()] = "month",
    organization_id: Annotated[UUID | None, Query()] = None,
    customer_segment_id: Annotated[UUID | None, Query()] = None,
    logistics_product_id: Annotated[UUID | None, Query()] = None,
    region_id: Annotated[UUID | None, Query()] = None,
) -> DashboardOverviewResponse:
    filters = ActiveFilters(
        period_view=period_view,
        organization_id=organization_id,
        customer_segment_id=customer_segment_id,
        logistics_product_id=logistics_product_id,
        region_id=region_id,
        is_total_scope=all(
            item is None
            for item in (
                organization_id,
                customer_segment_id,
                logistics_product_id,
                region_id,
            )
        ),
    )
    try:
        overview = DashboardService().get_overview(session, filters=filters)
    except DashboardSourceUnavailableError as error:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "dashboard_not_ready",
            "尚无可用的已发布经营驾驶舱",
        ) from error
    except DashboardFilterError as error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            error.code,
            str(error),
        ) from error
    return DashboardOverviewResponse.model_validate(overview.model_dump())


__all__ = ["get_dashboard_session", "router"]
