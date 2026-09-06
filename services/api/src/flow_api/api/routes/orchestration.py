"""发布后编排入口（T2.6）：已发布批次 → 指标快照序列 → 分析运行。

数据边界：只串联既有治理服务（MetricSnapshotService / AnalysisRunService），
不绕过发布资格、不重算数字；幂等由各服务自身的身份唯一约束承担。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.dashboard.fixture import DASHBOARD_MONTHS
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.metrics.catalog import load_metric_catalog
from flow_api.metrics.service import MetricSnapshotService

router = APIRouter(prefix="/orchestration", tags=["orchestration"])

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
METRICS_CONFIG = REPOSITORY_ROOT / "config/metrics/flow_v1_metrics.yaml"
ANALYSIS_POLICY_CONFIG = (
    REPOSITORY_ROOT / "services/api/config/analysis/flow-logistics-v1.yaml"
)


def get_orchestration_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_orchestration_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail=ErrorDetail(code=code, message=message).model_dump(mode="json"),
    )


class OrchestrationBuildResponse(BaseModel):
    batch_id: UUID
    metric_snapshot_ids: list[UUID]
    analysis_run_id: UUID
    as_of_months: list[int]


@router.post(
    "/batches/{batch_id}/build",
    response_model=OrchestrationBuildResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": dict},
        status.HTTP_409_CONFLICT: {"model": dict},
    },
)
def build_batch_analysis(
    session: SessionDependency,
    batch_id: UUID,
) -> OrchestrationBuildResponse:
    batch = session.scalar(select(AnalysisBatch).where(AnalysisBatch.id == batch_id))
    if batch is None:
        raise _error(status.HTTP_404_NOT_FOUND, "batch_not_found", "指定的接入批次不存在")
    published = session.scalar(
        select(AnalysisBatch.id).where(
            AnalysisBatch.id == batch_id, AnalysisBatch.status == "published"
        )
    )
    if published is None:
        raise _error(
            status.HTTP_409_CONFLICT,
            "batch_not_published",
            "批次尚未发布，不能构建指标快照与分析",
        )

    catalog = load_metric_catalog(METRICS_CONFIG)
    snapshot_service = MetricSnapshotService()
    months = list(DASHBOARD_MONTHS)
    snapshots = [
        snapshot_service.create_snapshot(
            session, batch_id=batch_id, as_of_month=month, catalog=catalog
        )
        for month in months
    ]
    session.flush()

    policy = load_analysis_policy(ANALYSIS_POLICY_CONFIG)
    run = AnalysisRunService().create_run(
        session, snapshot_id=snapshots[-1].id, loaded_policy=policy
    )
    session.commit()
    return OrchestrationBuildResponse(
        batch_id=batch_id,
        metric_snapshot_ids=[snapshot.id for snapshot in snapshots],
        analysis_run_id=run.id,
        as_of_months=months,
    )


__all__ = ["get_orchestration_session", "router"]
