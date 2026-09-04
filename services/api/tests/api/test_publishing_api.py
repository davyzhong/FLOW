"""Task 7 契约测试：报告快照冻结/列表、attempt 明细扩展、产物下载流。

- POST /api/v1/publishing/snapshots：从已发布指标快照 + 已批准 findings 冻结；
  findings 未批准 → 409 freeze_blocked 并给出原因；
- GET  /api/v1/publishing/snapshots：发现；
- GET  /api/v1/publishing/snapshots/{id}/attempts：行包含 attempt_id/size_bytes/
  content_type/created_at/download_available/stored_sha256；
- GET  /api/v1/publishing/attempts/{attempt_id}/download：仅 succeeded 且库内有对象
  可下载；服务端命名 + no-store/nosniff；下载字节与登记 sha 一致。
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from integration.intake_service_support import clean
from integration.metric_snapshot_support import metric_session_fixture as metric_session  # noqa: F401
from publishing.publishing_support import approve_top_findings, publish_analysis_run
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.api.routes.intake import get_db_session
from flow_api.api.routes.investigations import get_investigation_session
from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.analytics import Finding
from flow_api.main import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def client() -> Any:
    with Session(get_engine(), expire_on_commit=False) as session:
        clean(session)
        app = create_app()

        def session_override() -> Any:
            yield session
            session.flush()

        app.dependency_overrides[get_db_session] = session_override
        app.dependency_overrides[get_investigation_session] = session_override
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
        session.rollback()
        clean(session)


async def _approved_snapshot_id(session: Session) -> Any:
    run = publish_analysis_run(session)
    approve_top_findings(session, count=1, run_id=run.id)
    session.commit()
    return session.scalar(
        select(Finding.metric_snapshot_id).where(Finding.analysis_run_id == run.id).limit(1)
    )


async def test_freeze_list_publish_and_download(client: Any) -> None:
    with Session(get_engine(), expire_on_commit=False) as session:
        snapshot_id = await _approved_snapshot_id(session)
    freeze = await client.post(
        "/api/v1/publishing/snapshots", json={"metric_snapshot_id": str(snapshot_id)}
    )
    assert freeze.status_code == 201, freeze.text
    report = freeze.json()
    assert report["version"] >= 1 and report["title"]

    listing = await client.get("/api/v1/publishing/snapshots")
    assert listing.status_code == 200
    assert any(row["id"] == report["id"] for row in listing.json()["snapshots"])

    publish = await client.post(
        f"/api/v1/publishing/snapshots/{report['id']}/publish",
        json={"formats": ["html", "pdf"], "actor": "finance.bp@example.com"},
    )
    assert publish.status_code == 200
    assert publish.json()["outcomes"]["html"] == "succeeded"
    # 未接打印机时 pdf 必须是显式 failed（可重试），不允许假成功
    assert publish.json()["outcomes"]["pdf"] == "failed"

    attempts = (
        await client.get(f"/api/v1/publishing/snapshots/{report['id']}/attempts")
    ).json()["attempts"]
    html_attempts = [a for a in attempts if a["format"] == "html" and a["status"] == "succeeded"]
    assert html_attempts, "应有成功的 html attempt"
    line = html_attempts[0]
    assert line["attempt_id"]
    assert line["size_bytes"] > 0
    assert line["content_type"].startswith("text/html")
    assert line["created_at"]
    assert line["download_available"] is True
    pdf_lines = [a for a in attempts if a["format"] == "pdf"]
    assert all(a["download_available"] is False for a in pdf_lines)

    download = await client.get(f"/api/v1/publishing/attempts/{line['attempt_id']}/download")
    assert download.status_code == 200
    assert download.headers["cache-control"] == "no-store"
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in download.headers["content-disposition"]
    assert download.headers["content-disposition"].endswith('.html"')
    assert hashlib.sha256(download.content).hexdigest() == line["stored_sha256"]


async def test_download_of_failed_attempt_is_blocked(client: Any) -> None:
    with Session(get_engine(), expire_on_commit=False) as session:
        snapshot_id = await _approved_snapshot_id(session)
    report_id = (
        await client.post(
            "/api/v1/publishing/snapshots", json={"metric_snapshot_id": str(snapshot_id)}
        )
    ).json()["id"]
    await client.post(
        f"/api/v1/publishing/snapshots/{report_id}/publish",
        json={"formats": ["pdf"], "actor": "finance.bp@example.com"},
    )
    attempts = (
        await client.get(f"/api/v1/publishing/snapshots/{report_id}/attempts")
    ).json()["attempts"]
    failed_pdf = [a for a in attempts if a["status"] == "failed"][0]

    download = await client.get(
        f"/api/v1/publishing/attempts/{failed_pdf['attempt_id']}/download"
    )
    assert download.status_code == 409
    assert download.json()["detail"]["code"] == "download_not_available"

    missing = await client.get(f"/api/v1/publishing/attempts/{uuid.uuid4()}/download")
    assert missing.status_code == 404


async def test_freeze_blocked_without_approved_findings(client: Any) -> None:
    with Session(get_engine(), expire_on_commit=False) as session:
        run = publish_analysis_run(session)
        # 不做任何 findings 批准 —— 冻结必须被治理规则阻断
        session.commit()
        snapshot_id = session.scalar(
            select(Finding.metric_snapshot_id).where(Finding.analysis_run_id == run.id).limit(1)
        )
    missing = await client.post(
        "/api/v1/publishing/snapshots",
        json={"metric_snapshot_id": str(snapshot_id)},
    )
    assert missing.status_code == 409
    body = missing.json()["detail"]
    assert body["code"] == "freeze_blocked"
    assert "approv" in body["message"].lower() or "finding" in body["message"].lower()
