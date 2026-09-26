"""MetricSnapshot / AnalysisRun 只读详情端点（全站超链接化批次二 §3.2）。

消费方：/reports?snapshot= 深链回退定位、/analysis?run_id= 接收端、
investigation 身份条四 ID 跳转。端点只读（仅 SELECT），缺失对象经 loader
lineage 解析失败 → 403 resource_scope_unresolved（§6 防存在性枚举，
与 GET /investigations/{finding_id} 同一语义）。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from flow_api.api.schemas.analytics import (
    AnalysisRunDetailResponse,
    MetricSnapshotDetailResponse,
)
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.analytics import AnalysisRun, MetricSnapshot
from flow_api.security.authorization import Action
from flow_api.security.route_policy import (
    LOADERS,
    require_action,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_analytics_session)]


@router.get(
    "/metric-snapshots/{snapshot_id}",
    response_model=MetricSnapshotDetailResponse,
    responses={status.HTTP_403_FORBIDDEN: {"model": ErrorDetail}},
    dependencies=[
        Depends(
            require_action(
                Action.METRIC_SNAPSHOT_READ,
                LOADERS["load_metric_snapshot_batch_scope_or_deny_legacy"],
                session_provider=get_analytics_session,
            )
        )
    ],
)
def get_metric_snapshot(
    snapshot_id: UUID, session: SessionDependency
) -> MetricSnapshotDetailResponse:
    """指标快照只读身份（loader 已保证存在性与企业域，handler 只做投影）。"""
    snapshot = session.get(MetricSnapshot, snapshot_id)
    assert snapshot is not None  # loader lineage 解析通过即存在
    return MetricSnapshotDetailResponse(
        id=str(snapshot.id),
        batch_id=str(snapshot.batch_id),
        import_version_id=str(snapshot.import_version_id),
        as_of_period_id=str(snapshot.as_of_period_id),
        as_of_month_key=snapshot.as_of_period.month_key if snapshot.as_of_period else None,
        version=snapshot.version,
        engine_version=snapshot.engine_version,
        definition_set_id=snapshot.definition_set_id,
        definition_set_hash=snapshot.definition_set_hash,
        fingerprint=snapshot.fingerprint,
        status=snapshot.status,
        created_at=(
            snapshot.created_at.isoformat(timespec="seconds") if snapshot.created_at else None
        ),
    )


@router.get(
    "/analysis-runs/{run_id}",
    response_model=AnalysisRunDetailResponse,
    responses={status.HTTP_403_FORBIDDEN: {"model": ErrorDetail}},
    dependencies=[
        Depends(
            require_action(
                Action.ANALYSIS_RUN_READ,
                LOADERS["load_analysis_run_batch_scope_or_deny_legacy"],
                session_provider=get_analytics_session,
            )
        )
    ],
)
def get_analysis_run(run_id: UUID, session: SessionDependency) -> AnalysisRunDetailResponse:
    """分析运行只读身份（loader 已保证存在性与企业域，handler 只做投影）。"""
    run = session.get(AnalysisRun, run_id)
    assert run is not None  # loader lineage 解析通过即存在
    return AnalysisRunDetailResponse(
        id=str(run.id),
        metric_snapshot_id=str(run.metric_snapshot_id),
        import_version_id=str(run.import_version_id),
        policy_id=run.policy_id,
        policy_set_hash=run.policy_set_hash,
        engine_version=run.engine_version,
        fingerprint=run.fingerprint,
        status=run.status,
        created_at=(run.created_at.isoformat(timespec="seconds") if run.created_at else None),
    )


__all__ = ["get_analytics_session", "router"]
