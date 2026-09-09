"""U7 四问工作台 typed 端点契约测试。

GET /api/v1/analysis/workbench/{report_id}
- 200：四问结构 + 每问指标可用性与预计算值 + facts_available；
- 404 statement_report_not_found：未知报告；
- 可用性：缺上年同期（prev）时增长类指标 available=false，不编造。
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

from flow_api.api.routes.objective_reports import get_objective_session
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
    app.dependency_overrides[get_objective_session] = lambda: db_session
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
    return report


async def test_workbench_returns_four_questions(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import(db_session)
    db_session.commit()
    response = await client.get(f"/api/v1/analysis/workbench/{report.id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert [q["key"] for q in body["questions"]] == ["growth", "profit", "capital", "cash"]
    assert body["report"]["company_name"] == "顺丰控股"
    # 事实核对：capital 域的资产负债率可算（归一化事实齐备）
    capital = next(q for q in body["questions"] if q["key"] == "capital")
    debt = next(m for m in capital["metrics"] if m["metric_code"] == "debt_asset_ratio")
    assert debt["available"] is True and debt["value"] == "0.4780"
    # 诚实降级：增长类指标缺上年同期事实 → available=false，不编造数值
    growth = next(q for q in body["questions"] if q["key"] == "growth")
    assert all(m["available"] is False for m in growth["metrics"])


async def test_workbench_unknown_report_404(client: AsyncClient) -> None:
    from uuid import uuid4

    response = await client.get(f"/api/v1/analysis/workbench/{uuid4()}")
    assert response.status_code == 404
