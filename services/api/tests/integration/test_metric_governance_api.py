"""指标库治理 API（C04）契约测试：草稿→生效→事件链，经 HTTP 层。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from flow_api.api.routes.metric_library import get_metric_library_session
from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricCatalogDocument,
    MetricDictionaryEntry,
    MetricGovernanceEvent,
    StatementLineMapping,
)
from flow_api.main import create_app
from flow_api.metric_library_store.importer import import_metric_dictionary
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]
DICT_YAML = REPO_ROOT / "config/metrics/metric_dictionary_v1.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
async def client() -> Any:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        MetricGovernanceEvent,
        MetricDictionaryEntry,
        MetricCatalogDocument,
        AccountingSubject,
        AccountingStandard,
        EntryTemplate,
        StatementLineMapping,
    ):
        session.execute(delete(table))
    session.commit()
    import_metric_dictionary(session, DICT_YAML)
    session.commit()

    app = create_app()
    app.dependency_overrides[get_metric_library_session] = lambda: session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    session.close()
    engine.dispose()


async def test_draft_activate_events_over_http(client: AsyncClient) -> None:
    listing = await client.get("/api/v1/metric-library")
    assert listing.status_code == 200
    # 找到 effective 的 current_ratio 条目 id：经 DB 直查（HTTP 列表不暴露条目 id）
    # 走 drafts 前先确认库内存在
    # 通过事件链验证：起草 → 生效 → 事件三条
    # 取一个条目 id：直接查库不在此处职责；经 API 仅有列表。用字典导入的已知条目经服务层取。
    from flow_api.infrastructure.db import get_engine

    with Session(get_engine()) as reader:
        entry = reader.scalar(
            select(MetricDictionaryEntry).where(
                MetricDictionaryEntry.metric_code == "current_ratio",
                MetricDictionaryEntry.status == "effective",
            )
        )
        assert entry is not None
        entry_id = str(entry.id)

    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={
            "changes": {"benchmark": "经验参考约 2.2"},
            "operator": "钟Davy",
            "reason": "基准校准",
        },
    )
    assert draft.status_code == 201, draft.text
    draft_id = draft.json()["id"]

    activated = await client.post(
        f"/api/v1/metric-library/entries/{draft_id}/activate",
        json={"operator": "钟Davy", "reason": "评审通过"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "effective"

    events = await client.get(
        "/api/v1/metric-library/events", params={"metric_code": "current_ratio"}
    )
    assert events.status_code == 200
    actions = [event["action"] for event in events.json()["events"]]
    assert "draft" in actions and "activate" in actions and "retire" in actions


async def test_activate_illegal_ast_rejected_over_http(client: AsyncClient) -> None:
    from flow_api.infrastructure.db import get_engine

    with Session(get_engine()) as reader:
        entry = reader.scalar(
            select(MetricDictionaryEntry).where(
                MetricDictionaryEntry.metric_code == "quick_ratio",
                MetricDictionaryEntry.status == "effective",
            )
        )
        assert entry is not None
        entry_id = str(entry.id)

    draft = await client.post(
        f"/api/v1/metric-library/entries/{entry_id}/drafts",
        json={
            "changes": {"formula": {"op": "median", "args": ["bs.total_assets"]}},
            "operator": "a",
            "reason": "r",
        },
    )
    assert draft.status_code == 201
    blocked = await client.post(
        f"/api/v1/metric-library/entries/{draft.json()['id']}/activate",
        json={"operator": "a", "reason": "r"},
    )
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "invalid_formula_ast"
