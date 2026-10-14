"""批次 B4/B5：驾驶舱行动项闭环 API 测试。

覆盖（真实 bearer + role_binding，项目惯例）：
- 401 无凭据且无 dev actor（fail-closed）；
- 403 角色不允许（finance_bp 不能 create/acknowledge）与 loader 未解析；
- cfo 全链路：create（201）→ list → acknowledge（回执，不改业务行）；
- 行动项行不可变；durable AuditEvent（action=cockpit.action_item.acknowledge）
  即确认凭证。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from flow_api.api.routes.cockpit import get_cockpit_session
from flow_api.enterprise.models import AnalysisCycle
from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot, Period
from flow_api.infrastructure.models.cockpit import ActionItem
from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion
from flow_api.settings import get_settings

CFO = "cockpit-cfo-a"
FINANCE_BP = "cockpit-finance-bp-a"
_ENTERPRISE = "00000000-0000-0000-0000-00000000d001"


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (ActionItem, Finding, MetricSnapshot, ImportVersion, AnalysisBatch):
        session.execute(delete_all(table))
    session.execute(text("DELETE FROM analysis_cycle"))
    # bootstrap 单企业（load_single_enterprise 要求唯一企业）
    session.add(
        AnalysisCycle(enterprise_id=uuid.UUID(_ENTERPRISE), period_key="2023-03")
    )
    session.commit()
    try:
        yield session
    finally:
        # 还原我建的数据（含 analysis_cycle——迁移测试对 enterprise 的
        # RESTRICT 删除会被残留 cycle 卡住）
        for table in (
            ActionItem,
            Finding,
            MetricSnapshot,
            ImportVersion,
            AnalysisBatch,
            AnalysisCycle,
        ):
            session.execute(delete_all(table))
        session.commit()
        session.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def role_bindings(db_session: Session) -> Iterator[dict[str, str]]:
    engine = create_engine(get_settings().database_url)
    conn = engine.connect()
    try:
        # conftest autouse 会为 env 中的 dev actor 硬编码种 analyst 行（且
        # WHERE NOT EXISTS 使脏行跨测试永存）——先清后种，保证本测试角色权威
        conn.execute(
            text("DELETE FROM role_binding WHERE actor_id IN (:cfo, :fbp)"),
            {"cfo": CFO, "fbp": FINANCE_BP},
        )
        for actor, role in ((CFO, "cfo"), (FINANCE_BP, "finance_bp")):
            conn.execute(
                text(
                    "INSERT INTO role_binding (actor_id, role, enterprise_id,"
                    " is_service_account, active)"
                    " VALUES (CAST(:actor AS varchar), :role,"
                    f" CAST('{_ENTERPRISE}' AS uuid), false, true)"
                ),
                {"actor": actor, "role": role},
            )
        conn.commit()
    finally:
        conn.close()
    yield {"cfo": CFO, "finance_bp": FINANCE_BP}


@pytest.fixture()
def api_client(db_session: Session) -> Iterator[TestClient]:
    """覆盖 cockpit 会话为测试会话（断言用）；授权走真实 bearer。"""

    from flow_api.main import create_app

    app = create_app()
    app.dependency_overrides[get_cockpit_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def delete_all(model):
    from sqlalchemy import delete

    return delete(model)


def _become(actor: str) -> None:
    """项目惯例：dev principal 切换（角色来自 role_binding 表）。"""

    import os

    from flow_api.settings import get_settings

    os.environ["FLOW_DEV_ACTOR_ID"] = actor
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_actor() -> Any:
    """测试后恢复 dev actor——env 全局态不外泄到同会话的其他测试文件。"""

    import os

    from flow_api.settings import get_settings

    yield
    os.environ["FLOW_DEV_ACTOR_ID"] = "flow-dev-bp"
    get_settings.cache_clear()


def _seed_finding(db_session: Session) -> tuple[str, str]:
    """最小事实链：period → batch → import_version → snapshot → finding。"""

    period = db_session.scalar(select(Period).where(Period.month_key == 202301))
    if period is None:
        period = Period(month_key=202301, year=2023, quarter=1, month=1)
        db_session.add(period)
        db_session.flush()
    batch = AnalysisBatch(
        name="行动项测试批次",
        created_by=CFO,
        module_kind="public",
        fact_context_version=1,
    )
    db_session.add(batch)
    db_session.flush()
    version = ImportVersion(batch_id=batch.id, sequence=1)
    db_session.add(version)
    db_session.flush()
    snapshot = MetricSnapshot(
        batch_id=batch.id,
        import_version_id=version.id,
        as_of_period_id=period.id,
        version=1,
        status="published",
        engine_version="test",
        definition_set_id="test-definition-set",
        definition_set_hash="a" * 64,
        fingerprint="b" * 64,
    )
    db_session.add(snapshot)
    db_session.flush()
    finding = Finding(
        metric_snapshot_id=snapshot.id,
        title="现金流背离",
        status="approved",
        impact_amount=Decimal("-100.0000"),
        confidence=Decimal("0.8000"),
    )
    db_session.add(finding)
    db_session.commit()
    return str(finding.id), str(snapshot.id)


def _seed_item(db_session: Session) -> ActionItem:
    finding_id, snapshot_id = _seed_finding(db_session)
    item = ActionItem(
        enterprise_id=uuid.UUID(_ENTERPRISE),
        finding_id=uuid.UUID(finding_id),
        snapshot_id=uuid.UUID(snapshot_id),
        title="应收账龄恶化：出具催收行动建议",
        detail="E3 事件对应结论的行动项",
        created_by=CFO,
    )
    db_session.add(item)
    db_session.commit()
    return item


def test_action_items_require_authentication(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """无凭据且无 dev actor → 401（fail-closed；与 auth_boundary 同隔离法）。"""


    from flow_api.main import create_app
    from flow_api.settings import get_settings

    for var in ("AUTH_TOKEN", "FLOW_DEV_ACTOR_ID", "FLOW_LEGACY_ACTOR_ID"):
        monkeypatch.delenv(var, raising=False)
    get_settings.cache_clear()
    try:
        app = create_app()
        app.dependency_overrides[get_cockpit_session] = lambda: db_session
        with TestClient(app) as isolated:
            assert isolated.get("/api/v1/cockpit/action-items").status_code == 401
    finally:
        get_settings.cache_clear()


def test_finance_bp_can_read_but_not_create_or_acknowledge(
    api_client: TestClient, db_session: Session
) -> None:
    _become(FINANCE_BP)
    item = _seed_item(db_session)
    listed = api_client.get("/api/v1/cockpit/action-items")
    assert listed.status_code == 200
    created = api_client.post(
        "/api/v1/cockpit/action-items",
        json={
            "finding_id": str(uuid.uuid4()),
            "snapshot_id": str(uuid.uuid4()),
            "title": "x",
        },
    )
    assert created.status_code == 403, created.text
    acknowledged = api_client.post(
        f"/api/v1/cockpit/action-items/{item.id}/acknowledge"
    )
    assert acknowledged.status_code == 403


def test_cfo_full_loop_and_immutability(
    api_client: TestClient, db_session: Session
) -> None:
    _become(CFO)
    finding_id, snapshot_id = _seed_finding(db_session)
    created = api_client.post(
        "/api/v1/cockpit/action-items",
        json={
            "finding_id": finding_id,
            "snapshot_id": snapshot_id,
            "title": "现金流背离专项说明",
            "detail": "E5 对应行动项",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["acknowledgment"] == "audit_event"

    listed = api_client.get("/api/v1/cockpit/action-items")
    assert listed.status_code == 200
    assert any(row["id"] == body["id"] for row in listed.json())

    item_row = db_session.scalar(select(ActionItem).where(ActionItem.id == uuid.UUID(body["id"])))
    assert item_row is not None
    before = (item_row.title, item_row.detail, item_row.created_at)

    acknowledged = api_client.post(
        f"/api/v1/cockpit/action-items/{body['id']}/acknowledge",
        )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["acknowledged_via"] == "audit_event"

    db_session.expire_all()
    item_row = db_session.scalar(select(ActionItem).where(ActionItem.id == uuid.UUID(body["id"])))
    assert (item_row.title, item_row.detail, item_row.created_at) == before, (
        "确认动作不得改业务行（V1.1.1 §14 裁决 2）"
    )
    event = db_session.execute(
        text(
            "SELECT decision FROM audit_event"
            " WHERE resource_id = :rid AND action = 'cockpit.action_item.acknowledge'"
        ),
        {"rid": body["id"]},
    ).first()
    assert event is not None and event[0] == "allow"


def test_acknowledge_unknown_item_is_403_scope_unresolved(api_client: TestClient) -> None:
    _become(CFO)
    missing = api_client.post(
        f"/api/v1/cockpit/action-items/{uuid.uuid4()}/acknowledge",
        )
    assert missing.status_code == 403
    assert missing.json()["detail"]["code"] == "resource_scope_unresolved"
