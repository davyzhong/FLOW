"""U3/P04 切片二：主题投影 typed GET 端点契约测试。

GET /api/v1/statements/{report_id}/projection?mapping_version=v1
- 200：快照身份 + 目录身份 + 条目（值/状态/口径/来源定位）；
- 404 statement_report_not_found：未知报告；
- 409 snapshot_not_normalized：报告存在但该映射版本无归一化行。
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


def _import_and_normalize(db_session: Session) -> Any:
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


async def test_projection_endpoint_returns_identity_and_entries(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import_and_normalize(db_session)
    response = await client.get(f"/api/v1/statements/{report.id}/projection")
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    assert body["identity"] == {
        "report_id": str(report.id),
        "mapping_version": "v1",
    }
    assert body["catalog_id"]
    computed = [e for e in body["entries"] if e["status"] == "computed"]
    assert computed
    with_prov = next(e for e in computed if e["provenance"])
    point = with_prov["provenance"][0]
    assert point["item_id"] and point["source_sha256"] == "a" * 64
    # 值为精确字符串（前端只格式化）
    assert isinstance(with_prov["value"], str | type(None))


async def test_projection_unknown_report_typed_404(
    client: AsyncClient, db_session: Session
) -> None:
    from uuid import uuid4

    response = await client.get(f"/api/v1/statements/{uuid4()}/projection")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "statement_report_not_found"


async def test_projection_unnormalized_reports_409(
    client: AsyncClient, db_session: Session
) -> None:
    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        db_session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
    )
    db_session.commit()
    response = await client.get(f"/api/v1/statements/{report.id}/projection")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "snapshot_not_normalized"
