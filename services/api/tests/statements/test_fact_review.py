"""事实复核、人工更正与发布门禁（B05）测试。

- 更正必须带原因与操作者，写入只增不改的审计记录；原值留痕；
- 未解决关键勾稽不平衡时发布被阻断（critical_imbalance 409）；
- 发布后报表锁定：更正与重复发布均拒绝；
- 修正视图影响勾稽结果（更正后阻断解除可发布）；
- 不存在报表 404、未知行/未知列/无变化 422/409。
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.api.routes.statements import get_statement_session
from flow_api.infrastructure.models.statement import (
    StatementCorrection,
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.main import create_app
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report

REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        StatementCorrection,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
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


def _import_payload(session: Session, rows: list[dict[str, Any]]) -> StatementReport:
    return import_statement_report(
        session,
        company_name="测试股份",
        stock_code="600000",
        report_kind="一季报",
        period_label="2026Q1",
        payload={"unit": "人民币千元", "statements": {"合并资产负债表": rows}},
        source_ref="test.pdf",
    )


BALANCED_ROWS = [
    {"item": "流动资产合计", "期末余额": 60, "期初余额": 50},
    {"item": "非流动资产合计", "期末余额": 40, "期初余额": 40},
    {"item": "资产总计", "期末余额": 100, "期初余额": 90},
    {"item": "流动负债合计", "期末余额": 30, "期初余额": 30},
    {"item": "非流动负债合计", "期末余额": 20, "期初余额": 20},
    {"item": "负债合计", "期末余额": 50, "期初余额": 50},
    {"item": "归属于母公司所有者权益合计", "期末余额": 45, "期初余额": 35},
    {"item": "少数股东权益", "期末余额": 5, "期初余额": 5},
    {"item": "所有者权益合计", "期末余额": 50, "期初余额": 40},
    {"item": "负债和所有者权益总计", "期末余额": 100, "期初余额": 90},
]


async def test_correction_audit_and_publish_flow(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import_payload(db_session, BALANCED_ROWS)
    db_session.commit()

    created = await client.post(
        f"/api/v1/statements/{report.id}/corrections",
        json={
            "statement_type": "合并资产负债表",
            "item_name": "资产总计",
            "column_key": "value_end",
            "value": "101",
            "reason": "原文 OCR 少一位，按披露原文复核修正",
            "operator": "钟Davy",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert Decimal(body["old_value"]) == Decimal("100")
    assert Decimal(body["new_value"]) == Decimal("101")
    assert body["reason"]

    listed = await client.get(f"/api/v1/statements/{report.id}/corrections")
    assert listed.status_code == 200
    assert len(listed.json()["corrections"]) == 1

    # 保持平衡的成组更正（+1 同步到各恒等两侧）
    for item_name, value in (
        ("流动资产合计", "61"),
        ("归属于母公司所有者权益合计", "46"),
        ("所有者权益合计", "51"),
        ("负债和所有者权益总计", "101"),
    ):
        kept = await client.post(
            f"/api/v1/statements/{report.id}/corrections",
            json={
                "statement_type": "合并资产负债表",
                "item_name": item_name,
                "column_key": "value_end",
                "value": value,
                "reason": "同组修正保持平衡",
                "operator": "钟Davy",
            },
        )
        assert kept.status_code == 201, kept.text

    published = await client.post(f"/api/v1/statements/{report.id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    # 发布后锁定：更正与重复发布均拒绝
    locked = await client.post(
        f"/api/v1/statements/{report.id}/corrections",
        json={
            "statement_type": "合并资产负债表",
            "item_name": "资产总计",
            "column_key": "value_end",
            "value": "101",
            "reason": "发布后尝试更正",
            "operator": "钟Davy",
        },
    )
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "report_locked"
    again = await client.post(f"/api/v1/statements/{report.id}/publish")
    assert again.status_code == 409

    # 原始行不变
    db_session.expire_all()
    item = db_session.scalar(
        __import__("sqlalchemy").select(StatementLineItem).where(
            StatementLineItem.report_id == report.id,
            StatementLineItem.item_name == "资产总计",
        )
    )
    assert item is not None and float(item.value_end) == 100


async def test_publish_blocked_by_critical_imbalance_then_unblocked_by_correction(
    client: AsyncClient, db_session: Session
) -> None:
    rows = [dict(row) for row in BALANCED_ROWS]
    rows[2] = {"item": "资产总计", "期末余额": 101, "期初余额": 90}  # 打破恒等
    report = _import_payload(db_session, rows)
    db_session.commit()

    blocked = await client.post(f"/api/v1/statements/{report.id}/publish")
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "critical_imbalance"

    # 更正恢复平衡后可发布
    corrected = await client.post(
        f"/api/v1/statements/{report.id}/corrections",
        json={
            "statement_type": "合并资产负债表",
            "item_name": "资产总计",
            "column_key": "value_end",
            "value": "100",
            "reason": "抽取错位修正",
            "operator": "钟Davy",
        },
    )
    assert corrected.status_code == 201
    published = await client.post(f"/api/v1/statements/{report.id}/publish")
    assert published.status_code == 200


async def test_correction_validation_errors(
    client: AsyncClient, db_session: Session
) -> None:
    import uuid as uuid_module

    report = _import_payload(db_session, BALANCED_ROWS)
    db_session.commit()

    missing = await client.post(
        f"/api/v1/statements/{uuid_module.uuid4()}/corrections",
        json={
            "statement_type": "合并资产负债表",
            "item_name": "资产总计",
            "column_key": "value_end",
            "value": "1",
            "reason": "x",
            "operator": "y",
        },
    )
    assert missing.status_code == 404

    unknown_item = await client.post(
        f"/api/v1/statements/{report.id}/corrections",
        json={
            "statement_type": "合并资产负债表",
            "item_name": "不存在的科目",
            "column_key": "value_end",
            "value": "1",
            "reason": "x",
            "operator": "y",
        },
    )
    assert unknown_item.status_code == 404
    assert unknown_item.json()["detail"]["code"] == "item_not_found"

    no_change = await client.post(
        f"/api/v1/statements/{report.id}/corrections",
        json={
            "statement_type": "合并资产负债表",
            "item_name": "资产总计",
            "column_key": "value_end",
            "value": "100",
            "reason": "x",
            "operator": "y",
        },
    )
    assert no_change.status_code == 409
    assert no_change.json()["detail"]["code"] == "no_change"
