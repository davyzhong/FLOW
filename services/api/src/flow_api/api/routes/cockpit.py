"""CFO 驾驶舱路由（批次 A）。

安全纪律：
- 复用已批准的 Action.DASHBOARD_OVERVIEW_READ（批次 A 不引入新 Action；
  新 Action 属批次 B，须先修订安全规格 V1.1.1 并重新批准）。
- 沿用 dashboard 的 require_action + loader + 错误语义（404 未就绪 / 422 筛选非法）。
- 单一聚合 endpoint：一次返回该模块全部 KPI + 趋势 + 结论条，禁止前端逐图调用（N+1）。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.cockpit import CockpitOverviewResponse
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.cockpit.service import CockpitProjectionService
from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.repositories import DashboardSourceUnavailableError
from flow_api.dashboard.service import DashboardFilterError
from flow_api.infrastructure.db import get_session_factory
from flow_api.security.authorization import Action
from flow_api.security.route_policy import LOADERS, require_action

router = APIRouter(prefix="/cockpit", tags=["cockpit"])

# 演示数据源提示（设计文档 §7：演示/公开期必须全局标注，不解除 C 级门禁）
SOURCE_NOTICE = (
    "当前数据源为演示数据（大麦物流合成财报）。"
    "本看板不构成公开财报 C 级能力证明，不解除 C 级门禁。"
)


def get_cockpit_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_cockpit_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail=ErrorDetail(code=code, message=message).model_dump(mode="json"),
    )


@router.get(
    "/overview",
    response_model=CockpitOverviewResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorDetail},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorDetail},
    },
    dependencies=[
        Depends(
            require_action(
                Action.DASHBOARD_OVERVIEW_READ,
                LOADERS["load_single_enterprise"],
                session_provider=get_cockpit_session,
            )
        )
    ],
)
def cockpit_overview(
    session: SessionDependency,
    period_view: Annotated[Literal["month", "ytd"], Query()] = "ytd",
    organization_id: Annotated[UUID | None, Query()] = None,
    customer_segment_id: Annotated[UUID | None, Query()] = None,
    logistics_product_id: Annotated[UUID | None, Query()] = None,
    region_id: Annotated[UUID | None, Query()] = None,
) -> CockpitOverviewResponse:
    """集团总览：KPI 三基准 + 趋势 + 经营结论条（一次聚合，不 N+1）。"""
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
        projection = CockpitProjectionService().overview(
            session, filters=filters, source_notice=SOURCE_NOTICE
        )
    except DashboardSourceUnavailableError as error:
        raise _error(
            status.HTTP_404_NOT_FOUND,
            "cockpit_not_ready",
            "尚无可用的已发布经营数据",
        ) from error
    except DashboardFilterError as error:
        raise _error(status.HTTP_422_UNPROCESSABLE_CONTENT, error.code, str(error)) from error
    return CockpitOverviewResponse.model_validate(
        {
            "state": projection.state,
            "context": projection.context,
            "data_status": projection.data_status,
            "kpi_cards": [card.__dict__ for card in projection.kpi_cards],
            "trends": [
                {
                    "status": trend.status,
                    "unit": trend.unit,
                    "degradation_message": trend.degradation_message,
                    "series": [
                        {
                            "key": s.key,
                            "title": s.title,
                            "unit": s.unit,
                            "points": s.points,
                        }
                        for s in trend.series
                    ],
                }
                for trend in projection.trends
            ],
            "conclusion": {
                "text": projection.conclusion.text,
                "findings": projection.conclusion.findings,
                "tone": projection.conclusion.tone,
            },
            "source_notice": projection.source_notice,
        }
    )


__all__ = ["SOURCE_NOTICE", "get_cockpit_session", "router"]
