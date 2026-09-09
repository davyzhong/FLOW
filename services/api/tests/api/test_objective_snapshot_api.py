"""U6 切片二补充：客观快照端点契约测试。

GET  /api/v1/statements/{id}/objective-snapshot   摘要+黄金值（幂等冻结）
POST /api/v1/statements/{id}/objective-snapshot   幂等冻结
GET  /api/v1/statements/{id}/objective-snapshot/html  真渲染 HTML
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.api.routes.statements import get_statement_session
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.main import create_app
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (StatementNormalizedItem, StatementLineItem, StatementReport):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
async def client(db_session: Session) -> Iterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_statement_session] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def _import(db_session: Session) -> Any:
    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        db_session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="a" * 64,
    )
    db_session.flush()
    normalize_report(db_session, report)
    report.status = "published"
    db_session.flush()
    return report


async def test_objective_snapshot_summary_and_freeze(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import(db_session)
    db_session.commit()

    frozen = await client.post(f"/api/v1/statements/{report.id}/objective-snapshot")
    assert frozen.status_code == 200
    assert frozen.json()["payload_hash"]

    summary = await client.get(f"/api/v1/statements/{report.id}/objective-snapshot")
    assert summary.status_code == 200
    body = summary.json()
    assert body["report_type"] == "objective_statement"
    assert body["golden"]["revenue_current"] == "74142121.0000"
    assert body["statements_count"]["合并资产负债表"] >= 1
    assert body["source"]["company_name"] == "顺丰控股"


async def test_objective_html_contains_golden_values(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import(db_session)
    db_session.commit()
    response = await client.get(f"/api/v1/statements/{report.id}/objective-snapshot/html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "74142121.0000" in response.text
    assert "顺丰控股" in response.text


async def test_objective_snapshot_unknown_report_404(client: AsyncClient) -> None:
    from uuid import uuid4

    response = await client.get(f"/api/v1/statements/{uuid4()}/objective-snapshot")
    assert response.status_code == 404
