"""CFO 驾驶舱路由（批次 A）。

安全纪律：
- 复用已批准的 Action.DASHBOARD_OVERVIEW_READ（批次 A 不引入新 Action；
  新 Action 属批次 B，须先修订安全规格 V1.1.1 并重新批准）。
- 沿用 dashboard 的 require_action + loader + 错误语义（404 未就绪 / 422 筛选非法）。
- 单一聚合 endpoint：一次返回该模块全部 KPI + 趋势 + 结论条，禁止前端逐图调用（N+1）。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.cockpit import (
    CockpitActionItemAcknowledgeResponse,
    CockpitActionItemCreate,
    CockpitActionItemResponse,
    CockpitOverviewResponse,
)
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.cockpit.service import CockpitProjectionService
from flow_api.dashboard.models import ActiveFilters
from flow_api.dashboard.repositories import DashboardSourceUnavailableError
from flow_api.dashboard.service import DashboardFilterError
from flow_api.infrastructure.db import get_session_factory
from flow_api.security.authorization import Action
from flow_api.security.route_policy import (
    LOADERS,
    PRINCIPAL_DEP,
    ResourceScopeUnresolved,
    require_action,
)

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


# ---------------------------------------------------------------------------
# 批次 B4/B5：行动项闭环（cfo 角色；确认动作只写 durable AuditEvent）
# ---------------------------------------------------------------------------


def _load_action_items(
    session: Session, *, enterprise_id: UUID, finding_id: UUID | None
) -> list[Any]:
    from sqlalchemy import select

    from flow_api.infrastructure.models.cockpit import ActionItem

    statement = select(ActionItem).where(ActionItem.enterprise_id == enterprise_id)
    if finding_id is not None:
        statement = statement.where(ActionItem.finding_id == finding_id)
    return list(session.scalars(statement.order_by(ActionItem.created_at.desc())))


def _enterprise_scope_id(session: Session) -> UUID:
    """bootstrap 单租户：与 route_policy 的 load_single_enterprise 同语义。"""

    from sqlalchemy import text

    rows = session.execute(text("SELECT DISTINCT enterprise_id FROM analysis_cycle")).all()
    if len(rows) != 1 or rows[0][0] is None:
        raise _error(403, "enterprise_scope_unresolved", "企业范围无法唯一解析")
    return UUID(str(rows[0][0]))


@router.get(
    "/action-items",
    response_model=list[CockpitActionItemResponse],
    responses={status.HTTP_403_FORBIDDEN: {"model": ErrorDetail}},
    dependencies=[
        Depends(
            require_action(
                Action.COCKPIT_ACTION_ITEM_READ,
                LOADERS["load_single_enterprise"],
                session_provider=get_cockpit_session,
            )
        )
    ],
)
def list_cockpit_action_items(
    session: SessionDependency,
    finding_id: Annotated[UUID | None, Query()] = None,
) -> list[CockpitActionItemResponse]:
    from flow_api.security.route_policy import ResourceScopeUnresolved

    try:
        enterprise_id = _enterprise_scope_id(session)
    except ResourceScopeUnresolved as error:
        raise _error(403, "enterprise_scope_unresolved", str(error)) from error
    items = _load_action_items(session, enterprise_id=enterprise_id, finding_id=finding_id)
    return [
        CockpitActionItemResponse(
            id=str(item.id),
            finding_id=str(item.finding_id),
            snapshot_id=str(item.snapshot_id),
            title=item.title,
            detail=item.detail,
            created_by=item.created_by,
            created_at=item.created_at.isoformat(),
            acknowledgment="audit_event",
        )
        for item in items
    ]


@router.post(
    "/action-items",
    response_model=CockpitActionItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorDetail},
        status.HTTP_404_NOT_FOUND: {"model": ErrorDetail},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorDetail},
    },
    dependencies=[
        Depends(
            require_action(
                Action.COCKPIT_ACTION_ITEM_CREATE,
                LOADERS["load_single_enterprise"],
                session_provider=get_cockpit_session,
            )
        )
    ],
)
def create_cockpit_action_item(
    payload: CockpitActionItemCreate,
    session: SessionDependency,
    principal: Annotated[Any, Depends(PRINCIPAL_DEP)],
) -> CockpitActionItemResponse:
    from uuid import uuid4

    from sqlalchemy import select

    from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot
    from flow_api.infrastructure.models.cockpit import ActionItem

    try:
        enterprise_id = _enterprise_scope_id(session)
    except ResourceScopeUnresolved as error:
        raise _error(403, "enterprise_scope_unresolved", str(error)) from error
    try:
        finding_id = UUID(payload.finding_id)
        snapshot_id = UUID(payload.snapshot_id)
    except ValueError as error:
        raise _error(422, "invalid_uuid", "finding_id/snapshot_id 必须是 UUID") from error
    finding = session.scalar(select(Finding).where(Finding.id == finding_id))
    if finding is None:
        raise _error(404, "finding_not_found", "来源 Finding 不存在")
    snapshot = session.scalar(
        select(MetricSnapshot).where(MetricSnapshot.id == snapshot_id)
    )
    if snapshot is None:
        raise _error(404, "snapshot_not_found", "关联指标快照不存在（可追溯铁律）")
    # 企业隔离：Finding 归属企业经 analysis_run → batch → enterprise 链；
    # bootstrap 单租户下以唯一企业为准，跨企业请求由 loader 层 enterprise 隔离拒绝。
    item = ActionItem(
        id=uuid4(),
        enterprise_id=enterprise_id,
        finding_id=finding_id,
        snapshot_id=snapshot_id,
        title=payload.title,
        detail=payload.detail,
        created_by=principal.actor_id,
    )
    session.add(item)
    session.commit()
    return CockpitActionItemResponse(
        id=str(item.id),
        finding_id=str(item.finding_id),
        snapshot_id=str(item.snapshot_id),
        title=item.title,
        detail=item.detail,
        created_by=item.created_by,
        created_at=item.created_at.isoformat(),
        acknowledgment="audit_event",
    )


@router.post(
    "/action-items/{item_id}/acknowledge",
    response_model=CockpitActionItemAcknowledgeResponse,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorDetail},
        status.HTTP_404_NOT_FOUND: {"model": ErrorDetail},
    },
    dependencies=[
        Depends(
            require_action(
                Action.COCKPIT_ACTION_ITEM_ACKNOWLEDGE,
                LOADERS["load_cockpit_action_item"],
                session_provider=get_cockpit_session,
            )
        )
    ],
)
def acknowledge_cockpit_action_item(item_id: UUID) -> CockpitActionItemAcknowledgeResponse:
    """B5：确认动作不改业务行——durable allow 决策（resource_id=item_id）即凭证。

    本 handler 只做存在性回执；授权中间件已完成 durable 审计写入（fail closed）。
    """
    return CockpitActionItemAcknowledgeResponse(id=str(item_id))
