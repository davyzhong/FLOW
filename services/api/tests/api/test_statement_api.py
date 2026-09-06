"""报表分析 typed API 契约测试。

被测契约：
GET /api/v1/statements 返回已导入财报列表（空态返回空列表）；
GET /api/v1/statements/{id} 返回报表元数据 + 按披露顺序组织的三大报表行项目，
数值以精确十进制字符串跨 JSON；未知 id 返回 404 statement_report_not_found；
同身份重复导入幂等（报表 id 不变，行项目整体重建）。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.api.routes.statements import get_statement_session
from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport
from flow_api.main import create_app
from flow_api.settings import get_settings
from flow_api.statements.importer import StatementImportError, import_statement_report

IMPORT_KWARGS = {
    "company_name": "顺丰控股",
    "stock_code": "002352.SZ",
    "report_kind": "一季报",
    "period_label": "2026Q1",
}

SAMPLE_PAYLOAD: dict[str, Any] = {
    "unit": "人民币千元",
    "statements": {
        "合并资产负债表": [
            {"item": "流动资产：", "期末余额": None, "期初余额": None},
            {"item": "货币资金", "期末余额": 16992297, "期初余额": 20969400},
            {"item": "应收账款", "期末余额": 29039844, "期初余额": 30606710},
        ],
        "合并利润表": [
            {"item": "一、营业总收入", "本期发生额": 74142121, "上期发生额": 62432100},
            {"item": "其中：营业收入", "本期发生额": 74142121, "上期发生额": 62432100},
            {
                "item": "五、净利润（净亏损以“－”号填列）",
                "本期发生额": 2650843,
                "上期发生额": 2017475,
            },
        ],
    },
}


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    session.execute(delete(StatementLineItem))
    session.execute(delete(StatementReport))
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


def _import(session: Session, payload: dict[str, Any] | None = None) -> Any:
    return import_statement_report(
        session,
        **IMPORT_KWARGS,
        payload=payload or SAMPLE_PAYLOAD,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="a" * 64,
    )


@pytest.mark.asyncio
async def test_empty_list_returns_no_reports(client: AsyncClient) -> None:
    response = await client.get("/api/v1/statements")
    assert response.status_code == 200
    assert response.json() == {"reports": []}


@pytest.mark.asyncio
async def test_unknown_report_returns_typed_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/statements/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "statement_report_not_found"


@pytest.mark.asyncio
async def test_import_then_list_and_detail(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import(db_session)
    db_session.commit()
    db_session.expire_all()

    listed = await client.get("/api/v1/statements")
    assert listed.status_code == 200
    reports = listed.json()["reports"]
    assert len(reports) == 1
    summary = reports[0]
    assert summary["id"] == str(report.id)
    assert summary["company_name"] == "顺丰控股"
    assert summary["statement_types"] == ["合并资产负债表", "合并利润表"]
    assert summary["line_item_count"] == 6
    assert summary["unit_note"] == "人民币千元"

    detail = await client.get(f"/api/v1/statements/{report.id}")
    assert detail.status_code == 200
    body = detail.json()
    assert [s["statement_type"] for s in body["sections"]] == [
        "合并资产负债表",
        "合并利润表",
    ]
    bs_items = body["sections"][0]["items"]
    assert bs_items[0]["item_name"] == "流动资产："
    assert bs_items[0]["value_end"] is None
    assert bs_items[1]["item_name"] == "货币资金"
    assert bs_items[1]["value_end"] == "16992297.0000"
    assert bs_items[1]["value_begin"] == "20969400.0000"
    is_items = body["sections"][1]["items"]
    assert is_items[2]["value_current"] == "2650843.0000"
    assert is_items[2]["value_prior"] == "2017475.0000"


@pytest.mark.asyncio
async def test_reimport_same_identity_is_idempotent(
    client: AsyncClient, db_session: Session
) -> None:
    first = _import(db_session)
    db_session.commit()

    # 同内容重导入：幂等，报表 id 与行项目不变
    second = _import(db_session)
    db_session.commit()
    assert second.id == first.id

    # 同身份不同内容（重述）：递增版本，旧版保留（B03）
    extended = {
        "unit": "人民币千元",
        "statements": {
            "合并资产负债表": [
                {"item": "货币资金", "期末余额": 1, "期初余额": 2},
                {"item": "应收账款", "期末余额": 3, "期初余额": 4},
            ],
        },
    }
    restated = _import(db_session, extended)
    db_session.commit()
    assert restated.id != first.id
    assert restated.version == 2
    db_session.expire_all()  # 让 GET 经数据库回读，验证 Numeric(24,4) 规范化

    detail = await client.get(f"/api/v1/statements/{restated.id}")
    bs_items = detail.json()["sections"][0]["items"]
    assert [item["item_name"] for item in bs_items] == ["货币资金", "应收账款"]
    assert bs_items[0]["value_end"] == "1.0000"


def test_unknown_column_is_rejected(db_session: Session) -> None:
    with pytest.raises(StatementImportError) as excinfo:
        import_statement_report(
            db_session,
            **IMPORT_KWARGS,
            payload={
                "unit": "人民币千元",
                "statements": {"合并利润表": [{"item": "营业收入", "本期金额": 1, "备注": "x"}]},
            },
            source_ref="test",
        )
    assert excinfo.value.code == "unknown_statement_column"
    db_session.rollback()
