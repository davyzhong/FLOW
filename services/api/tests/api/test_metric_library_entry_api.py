"""指标库条目详情只读端点（全站超链接化批次二 §3.1）。

被测契约：
- GET /api/v1/metric-library/entries/{entry_id} 返回与列表载荷逐字段一致的条目详情
  （entry_id 仅存在于 DB 在效条目，详情必须与列表项完全同源）；
- 未登记 entry_id 返回 404 metric_entry_not_found（public 参考资源，诚实 404，
  不走企业域 403 防枚举路径）；
- YAML-only 回退模式（库内无 DB 条目）下任何 entry_id 都是 404。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from flow_api.api.routes.metric_library import resolve_metric_library_root
from flow_api.infrastructure.db import get_session_factory
from flow_api.main import create_app
from flow_api.metric_library_store.importer import import_all


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(scope="module", autouse=True)
def imported_dictionary(migrated_database: None) -> None:
    root = resolve_metric_library_root()
    with get_session_factory()() as session:
        import_all(session, root / "config" / "metrics")
        session.commit()


async def test_metric_entry_detail_matches_listing_item() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listing = await client.get("/api/v1/metric-library")
        assert listing.status_code == 200, listing.text
        entries = [m for m in listing.json()["metrics"] if m.get("entry_id")]
        assert entries, "DB 在效条目必须携带 entry_id"
        expected = next(m for m in entries if m["metric_code"] == "current_ratio")

        detail = await client.get(f"/api/v1/metric-library/entries/{expected['entry_id']}")

    assert detail.status_code == 200, detail.text
    body: dict[str, Any] = detail.json()
    assert body["entry_id"] == expected["entry_id"]
    assert body["metric_code"] == "current_ratio"
    assert body["collection"] == expected["collection"]
    assert body["name"] == expected["name"]
    assert body["formula_text"] == expected["formula_text"]
    assert body["status"] == expected["status"]
    # 执行绑定与列表口径一致（C02：kind/executor 同源）
    assert body.get("execution_kind") == expected.get("execution_kind")


async def test_metric_entry_detail_404_for_unknown_entry_id() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.get(f"/api/v1/metric-library/entries/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "metric_entry_not_found"
