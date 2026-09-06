"""发布后编排入口（T2.6/B06）：已发布批次 → 指标快照序列 → 分析运行。

B06 起：
- 期间由批次数据的分析窗口（事实期间）生成，可选请求范围收窄，不再使用固定演示月份；
- 每次构建持久化为 BuildJob（queued/running/succeeded/failed），失败留痕、可重试；
- 同批次同期间范围重复提交幂等回放既有成功任务；
- 快照/运行的身份唯一与不可变约束由各治理服务承担。
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.analysis.policy import load_analysis_policy
from flow_api.analysis.service import AnalysisRunService
from flow_api.api.schemas.intake import ErrorDetail
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.intake import AnalysisBatch, BuildJob
from flow_api.metrics.repositories import MetricSourceRepository
from flow_api.metrics.service import MetricSnapshotService
from flow_api.metrics_store import resolve_metric_catalog

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


def _repository_root() -> Path:
    """惰性解析仓库根（容器内代码在 /app 下，层级与开发机不同）。"""

    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "config/metrics/flow_v1_metrics.yaml").is_file():
            return candidate
    raise RuntimeError(f"FLOW repository root not found from {current}")


def get_orchestration_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_orchestration_session)]


def _error(http_status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail=ErrorDetail(code=code, message=message).model_dump(mode="json"),
    )


def _month_key(value: str) -> int:
    normalized = value.strip().replace("-", "")
    if not normalized.isdigit() or len(normalized) != 6:
        raise ValueError(f"期间必须是 YYYYMM 或 YYYY-MM：{value!r}")
    month = int(normalized) % 100
    if month < 1 or month > 12:
        raise ValueError(f"非法月份：{value!r}")
    return int(normalized)


def _month_range(start: int, end: int) -> list[int]:
    if start > end:
        return []
    months: list[int] = []
    year, month = divmod(start, 100)
    while year * 100 + month <= end:
        months.append(year * 100 + month)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


class OrchestrationBuildRequest(BaseModel):
    from_month: str | None = Field(default=None, description="分析窗口起点 YYYY-MM（含）")
    to_month: str | None = Field(default=None, description="分析窗口终点 YYYY-MM（含）")


class OrchestrationBuildResponse(BaseModel):
    job_id: UUID
    batch_id: UUID
    status: str
    months: list[int]
    metric_snapshot_ids: list[UUID]
    analysis_run_id: UUID | None
    replayed: bool


class BuildJobLine(BaseModel):
    job_id: UUID
    status: str
    months: list[int]
    metric_snapshot_ids: list[str]
    analysis_run_id: str | None
    error: str | None
    created_at: str | None
    finished_at: str | None = None


class BuildJobListResponse(BaseModel):
    jobs: list[BuildJobLine]


def _job_line(job: BuildJob) -> BuildJobLine:
    return BuildJobLine(
        job_id=job.id,
        status=job.status,
        months=list(job.months),
        metric_snapshot_ids=list(job.metric_snapshot_ids),
        analysis_run_id=str(job.analysis_run_id) if job.analysis_run_id else None,
        error=job.error,
        created_at=job.created_at.isoformat(timespec="seconds") if job.created_at else None,
        finished_at=job.finished_at.isoformat(timespec="seconds") if job.finished_at else None,
    )


def _resolve_months(
    session: Session, batch_id: UUID, request: OrchestrationBuildRequest
) -> list[int]:
    source = MetricSourceRepository().get_published_source(session, batch_id)
    start, end = source.analysis_start_month, source.analysis_end_month
    try:
        from_key = _month_key(request.from_month) if request.from_month else None
        to_key = _month_key(request.to_month) if request.to_month else None
    except ValueError as error:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_period_range", str(error)
        ) from error
    if from_key:
        start = max(start, from_key)
    if to_key:
        end = min(end, to_key)
    months = _month_range(start, end)
    if not months:
        raise _error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "no_periods_in_scope",
            f"请求范围与批次分析窗口（{source.analysis_start_month}–{source.analysis_end_month}）不相交",
        )
    return months


@router.post(
    "/batches/{batch_id}/build",
    response_model=OrchestrationBuildResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": dict},
        status.HTTP_409_CONFLICT: {"model": dict},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": dict},
    },
)
def build_batch_analysis(
    session: SessionDependency,
    batch_id: UUID,
    request: OrchestrationBuildRequest | None = None,
) -> OrchestrationBuildResponse:
    request = request or OrchestrationBuildRequest()
    batch = session.scalar(select(AnalysisBatch).where(AnalysisBatch.id == batch_id))
    if batch is None:
        raise _error(status.HTTP_404_NOT_FOUND, "batch_not_found", "指定的接入批次不存在")
    if batch.status != "published":
        raise _error(
            status.HTTP_409_CONFLICT,
            "batch_not_published",
            "批次尚未发布，不能构建指标快照与分析",
        )

    months = _resolve_months(session, batch_id, request)

    # 幂等回放：同批次同期间范围已有成功任务时直接复用
    replay = session.scalar(
        select(BuildJob).where(
            BuildJob.batch_id == batch_id,
            BuildJob.status == "succeeded",
            BuildJob.months == months,
        )
    )
    if replay is not None:
        return OrchestrationBuildResponse(
            job_id=replay.id,
            batch_id=batch_id,
            status="succeeded",
            months=months,
            metric_snapshot_ids=[UUID(v) for v in replay.metric_snapshot_ids],
            analysis_run_id=replay.analysis_run_id,
            replayed=True,
        )

    job = BuildJob(batch_id=batch_id, status="running", months=months)
    session.add(job)
    session.flush()

    metrics_config = _repository_root() / "config/metrics/flow_v1_metrics.yaml"
    catalog = resolve_metric_catalog(session, metrics_config)
    snapshot_service = MetricSnapshotService()
    try:
        snapshots = [
            snapshot_service.create_snapshot(
                session, batch_id=batch_id, as_of_month=month, catalog=catalog
            )
            for month in months
        ]
        session.flush()
        policy = load_analysis_policy(
            _repository_root() / "services/api/config/analysis/flow-logistics-v1.yaml"
        )
        run = AnalysisRunService().create_run(
            session, snapshot_id=snapshots[-1].id, loaded_policy=policy
        )
    except Exception as error:
        job.status = "failed"
        job.error = str(error)[:500]
        job.finished_at = datetime.now(UTC)
        session.commit()
        raise _error(
            status.HTTP_409_CONFLICT,
            "build_failed",
            f"构建失败（任务 {job.id}，可修正后重试）：{job.error}",
        ) from error

    job.status = "succeeded"
    job.metric_snapshot_ids = [str(snapshot.id) for snapshot in snapshots]
    job.analysis_run_id = run.id
    job.finished_at = datetime.now(UTC)
    session.commit()
    return OrchestrationBuildResponse(
        job_id=job.id,
        batch_id=batch_id,
        status="succeeded",
        months=months,
        metric_snapshot_ids=[snapshot.id for snapshot in snapshots],
        analysis_run_id=run.id,
        replayed=False,
    )


@router.get("/batches/{batch_id}/builds", response_model=BuildJobListResponse)
def list_batch_builds(session: SessionDependency, batch_id: UUID) -> BuildJobListResponse:
    jobs = session.scalars(
        select(BuildJob)
        .where(BuildJob.batch_id == batch_id)
        .order_by(BuildJob.created_at.desc())
    ).all()
    return BuildJobListResponse(jobs=[_job_line(job) for job in jobs])


@router.get("/builds/{job_id}", response_model=BuildJobLine)
def get_build_job(session: SessionDependency, job_id: UUID) -> BuildJobLine:
    job = session.get(BuildJob, job_id)
    if job is None:
        raise _error(status.HTTP_404_NOT_FOUND, "build_job_not_found", "指定的构建任务不存在")
    return _job_line(job)


__all__ = ["get_orchestration_session", "router"]
