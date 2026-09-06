"""发布后编排入口契约测试（T2.6）。

被测契约：POST /api/v1/orchestration/batches/{batch_id}/build
对一个已发布的 intake 批次串联构建：指标快照序列（全部分析月）→ 最新快照上的分析运行；
同一批次重复构建幂等（返回相同快照与运行 id）。
未发布批次返回 409 batch_not_published；未知批次 404 batch_not_found。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from flow_api.api.routes.orchestration import get_orchestration_session
from flow_api.dashboard.fixture import DEFAULT_REPOSITORY_ROOT as REPOSITORY_ROOT
from flow_api.dashboard.fixture import bootstrap_dashboard_demo
from flow_api.main import create_app
from flow_api.settings import get_settings


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
async def client(db_session: Session) -> Iterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_orchestration_session] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def test_build_orchestrates_snapshots_and_analysis(
    client: AsyncClient, db_session: Session
) -> None:
    publication = bootstrap_dashboard_demo(
        db_session, repository_root=REPOSITORY_ROOT, fresh_batch=True
    )
    db_session.commit()

    response = await client.post(f"/api/v1/orchestration/batches/{publication.batch_id}/build")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["metric_snapshot_ids"]) >= 1
    assert body["analysis_run_id"]

    # 幂等：重复构建返回相同身份
    again = await client.post(f"/api/v1/orchestration/batches/{publication.batch_id}/build")
    assert again.status_code == 200
    repeated = again.json()
    assert repeated["metric_snapshot_ids"] == body["metric_snapshot_ids"]
    assert repeated["analysis_run_id"] == body["analysis_run_id"]


async def test_unknown_batch_returns_typed_404(client: AsyncClient) -> None:
    from uuid import uuid4

    response = await client.post(f"/api/v1/orchestration/batches/{uuid4()}/build")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "batch_not_found"


async def test_unpublished_batch_returns_409(client: AsyncClient, db_session: Session) -> None:
    from flow_api.intake.service import IntakeService

    service = IntakeService(db_session)
    batch = service.create_batch(name="orchestration-unpublished-test")
    db_session.commit()
    response = await client.post(f"/api/v1/orchestration/batches/{batch.id}/build")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "batch_not_published"


async def test_build_with_request_range_and_replay(
    client: AsyncClient, db_session: Session
) -> None:
    publication = bootstrap_dashboard_demo(
        db_session, repository_root=REPOSITORY_ROOT, fresh_batch=True
    )
    db_session.commit()

    # 请求范围收窄：2025-11 ~ 2026-02（4 个月），覆盖非默认期间
    scoped = await client.post(
        f"/api/v1/orchestration/batches/{publication.batch_id}/build",
        json={"from_month": "2025-11", "to_month": "2026-02"},
    )
    assert scoped.status_code == 200, scoped.text
    body = scoped.json()
    assert body["months"] == [202511, 202512, 202601, 202602]
    assert len(body["metric_snapshot_ids"]) == 4
    assert body["replayed"] is False

    # 同范围重复提交：幂等回放既有任务
    again = await client.post(
        f"/api/v1/orchestration/batches/{publication.batch_id}/build",
        json={"from_month": "2025-11", "to_month": "2026-02"},
    )
    assert again.status_code == 200
    assert again.json()["replayed"] is True
    assert again.json()["job_id"] == body["job_id"]

    # 任务列表可查（浏览器进度入口的 API 面）
    listing = await client.get(f"/api/v1/orchestration/batches/{publication.batch_id}/builds")
    assert listing.status_code == 200
    jobs = listing.json()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["status"] == "succeeded"
    assert jobs[0]["finished_at"]

    detail = await client.get(f"/api/v1/orchestration/builds/{body['job_id']}")
    assert detail.status_code == 200
    assert detail.json()["months"] == [202511, 202512, 202601, 202602]


async def test_build_rejects_out_of_window_range(
    client: AsyncClient, db_session: Session
) -> None:
    publication = bootstrap_dashboard_demo(
        db_session, repository_root=REPOSITORY_ROOT, fresh_batch=True
    )
    db_session.commit()
    rejected = await client.post(
        f"/api/v1/orchestration/batches/{publication.batch_id}/build",
        json={"from_month": "2020-01", "to_month": "2020-12"},
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "no_periods_in_scope"

    bad = await client.post(
        f"/api/v1/orchestration/batches/{publication.batch_id}/build",
        json={"from_month": "2025-13"},
    )
    assert bad.status_code == 422
    assert bad.json()["detail"]["code"] == "invalid_period_range"
