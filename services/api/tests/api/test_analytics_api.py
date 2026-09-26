"""MetricSnapshot / AnalysisRun 只读详情端点（全站超链接化批次二 §3.2）。

被测契约：
- GET /api/v1/analytics/metric-snapshots/{snapshot_id} 返回快照身份
  （版本/引擎/定义集/指纹/状态/批次链/期间），供 /reports?snapshot= 深链回退定位；
- GET /api/v1/analytics/analysis-runs/{run_id} 返回运行身份
  （策略集/引擎/指纹/状态/所属快照），供 investigation 身份条与 /analysis?run_id= 定位；
- 未登记 id 一律 403 resource_scope_unresolved（§6 防存在性枚举，与调查详情同一语义）；
- 端点只读：仅 SELECT，不写库、不渲染产物。
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from integration.analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import publish_analysis_run
from sqlalchemy.orm import Session

from flow_api.api.routes.analytics import get_analytics_session
from flow_api.main import create_app


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


def _override(session: Session) -> Any:
    def _factory() -> Any:
        yield session

    return _factory


async def test_metric_snapshot_detail_returns_identity(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)
    snapshot = run.metric_snapshot

    app = create_app()
    app.dependency_overrides[get_analytics_session] = _override(analysis_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get(f"/api/v1/analytics/metric-snapshots/{uuid.uuid4()}")
        assert missing.status_code == 403  # §6 防存在性枚举
        assert missing.json()["detail"]["code"] == "resource_scope_unresolved"

        response = await client.get(f"/api/v1/analytics/metric-snapshots/{snapshot.id}")

    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    assert body["id"] == str(snapshot.id)
    assert body["batch_id"] == str(snapshot.batch_id)
    assert body["import_version_id"] == str(snapshot.import_version_id)
    assert body["as_of_period_id"] == str(snapshot.as_of_period_id)
    assert body["as_of_month_key"] == snapshot.as_of_period.month_key
    assert body["version"] == snapshot.version
    assert body["engine_version"] == snapshot.engine_version
    assert body["definition_set_id"] == snapshot.definition_set_id
    assert len(body["definition_set_hash"]) == 64
    assert len(body["fingerprint"]) == 64
    assert body["status"] == "published"
    assert body["created_at"]


async def test_analysis_run_detail_returns_identity(
    analysis_session: Session,
) -> None:
    run = publish_analysis_run(analysis_session)

    app = create_app()
    app.dependency_overrides[get_analytics_session] = _override(analysis_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get(f"/api/v1/analytics/analysis-runs/{uuid.uuid4()}")
        assert missing.status_code == 403  # §6 防存在性枚举
        assert missing.json()["detail"]["code"] == "resource_scope_unresolved"

        response = await client.get(f"/api/v1/analytics/analysis-runs/{run.id}")

    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    assert body["id"] == str(run.id)
    assert body["metric_snapshot_id"] == str(run.metric_snapshot_id)
    assert body["import_version_id"] == str(run.import_version_id)
    assert body["policy_id"] == run.policy_id
    assert len(body["policy_set_hash"]) == 64
    assert body["engine_version"] == "flow-analysis/1"
    assert len(body["fingerprint"]) == 64
    assert body["status"] == "published"
    assert body["created_at"]
