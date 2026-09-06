"""指标库 v1 配置落库 + 只读 API 从 DB 读取（T2.2/T2.4）。

被测契约：
- GET /api/v1/metric-library 默认从数据库读取已导入的 v1 内容；
- 数据库为空时回退 YAML（首次部署体验），响应 header/query 标注来源；
- POST /api/v1/metric-library/import 以整版幂等方式导入配置（受保护操作）；
- 版本化状态流转：effective 为默认读取集；POST retire 将指定 dictionary 置 retired，
  retired 集不再出现在默认读取中，导入审计行记录动作与操作者。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from flow_api.api.routes.metric_library import (
    get_metric_library_session,
    resolve_metric_library_root,
)
from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricDictionaryEntry,
    StatementLineMapping,
)
from flow_api.main import create_app
from flow_api.metric_library_store.importer import import_all
from flow_api.settings import get_settings

CONFIG_ROOT = resolve_metric_library_root() / "config/metrics"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for model in (
        MetricDictionaryEntry,
        AccountingSubject,
        AccountingStandard,
        EntryTemplate,
        StatementLineMapping,
    ):
        session.execute(delete(model))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
async def client(db_session: Session) -> Iterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_metric_library_session] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


async def test_metric_library_falls_back_to_yaml_when_db_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/metric-library")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["dictionary_id"] == "flow.metric_dictionary.v1"
    assert len(body["metrics"]) == 55
    assert len(body["accounting"]["accounts"]) == 167


async def test_import_then_read_from_db(
    client: AsyncClient, db_session: Session
) -> None:
    response = await client.post("/api/v1/metric-library/import", json={"actor": "seed"})
    assert response.status_code == 200, response.text
    summary: dict[str, Any] = response.json()
    assert summary["metrics"] == 55
    assert summary["subjects"] == 167
    assert summary["standards"] == 48
    assert summary["templates"] == 32
    assert summary["mappings"] == 28

    listing = await client.get("/api/v1/metric-library")
    body = listing.json()
    assert body["dictionary_id"] == "flow.metric_dictionary.v1"
    assert len(body["metrics"]) == 55
    roe = next(m for m in body["metrics"] if m["metric_code"] == "roe")
    assert roe["default_caliber"].startswith("净利润 ÷ 平均净资产")
    # 幂等：重复导入不产生重复行
    await client.post("/api/v1/metric-library/import", json={"actor": "seed"})
    rows = db_session.query(MetricDictionaryEntry).count()
    assert rows == 55
    subjects = db_session.query(AccountingSubject).count()
    assert subjects == 167


async def test_retire_dictionary_hides_it_from_default_read(
    client: AsyncClient, db_session: Session
) -> None:
    await client.post("/api/v1/metric-library/import", json={"actor": "seed"})
    response = await client.post(
        "/api/v1/metric-library/retire",
        json={"dictionary_id": "flow.metric_dictionary.v1", "actor": "admin", "reason": "v2 上线"},
    )
    assert response.status_code == 200
    retired = (
        db_session.query(MetricDictionaryEntry)
        .filter(MetricDictionaryEntry.status == "retired")
        .count()
    )
    assert retired == 55
    # 默认读取回退 YAML（DB 无 effective 集），仍可用
    listing = await client.get("/api/v1/metric-library")
    assert listing.status_code == 200
    assert listing.json()["dictionary_id"] == "flow.metric_dictionary.v1"


def test_importer_direct_counts(db_session: Session) -> None:
    summary = import_all(db_session, CONFIG_ROOT)
    assert summary == {
        "metrics": 55,
        "mappings": 28,
        "subjects": 167,
        "standards": 48,
        "templates": 32,
    }


def test_statement_line_mapping_resolves_subject_codes(db_session: Session) -> None:
    """T2.5：报表项目 ↔ 科目映射落库且科目编码在科目表中存在（溯源闭合）。"""
    import_all(db_session, CONFIG_ROOT)
    db_session.expire_all()
    mappings = db_session.scalars(select(StatementLineMapping)).all()
    by_item = {m.item_id: m for m in mappings}
    assert by_item["bs.ar"].subject_codes == ["1122"]
    assert by_item["bs.cash"].subject_codes == ["1001", "1002"]
    assert by_item["is.revenue"].subject_codes == ["6001", "6051"]
    assert by_item["bs.total_assets"].subject_codes == []
    subject_codes = {
        s.code for s in db_session.scalars(select(AccountingSubject)).all()
    }
    unresolved = [
        m.item_id
        for m in mappings
        if m.subject_codes
        and not set(m.subject_codes) <= subject_codes
    ]
    assert not unresolved, f"映射指向科目表不存在的编码: {unresolved}"
    # 报表项目 → 指标反向索引：is.revenue 至少被收入类指标引用
    revenue_refs = [
        m.metric_code
        for m in db_session.scalars(select(MetricDictionaryEntry)).all()
        if "营业收入" in (m.source_cas or [])
    ]
    assert revenue_refs, "营业收入报表项目应被至少一个指标引用"
