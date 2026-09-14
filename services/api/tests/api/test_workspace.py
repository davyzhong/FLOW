"""GET /api/v1/workspace 契约测试。

2A 后 workspace 挂在 `require_bearer_auth` 之后；本测试用 dependency override
提供 dev Principal 的 fake binding（§2.2），使其在无 DB 的 unit job 可运行。
真实 dev/legacy 解析由 tests/security/ 与集成线覆盖。
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient

from flow_api.api import auth as api_auth
from flow_api.main import create_app
from flow_api.security.audit import AuditContext, get_audit_writer
from flow_api.security.principal import Role

DEV_ENTERPRISE_ID = UUID("00000000-0000-0000-0000-00000000d001")


class _FakeBinding:
    """duck-type security.models.RoleBinding（仅 require_bearer_auth 读取的字段）。"""

    def __init__(self) -> None:
        self.id = uuid4()
        self.actor_id = "flow-dev-bp"
        self.role = Role.ANALYST.value
        self.enterprise_id = DEV_ENTERPRISE_ID
        self.is_service_account = False
        self.active = True
        self.created_at = datetime.now(tz=UTC)
        self.revoked_at = None


class _FakeSession:
    def scalar(self, *_args: object, **_kwargs: object) -> _FakeBinding:
        return _FakeBinding()


class _NoopAuditWriter:
    def write_decision(
        self, *, audit_context: AuditContext, decision: object, request_id: str
    ) -> None:
        return None

    def write_intent(self, **kwargs: object) -> None:
        return None

    def write_outcome(self, **kwargs: object) -> None:
        return None


def _fake_readonly_session() -> _FakeSession:
    return _FakeSession()


async def test_workspace_contract() -> None:
    app = create_app()
    app.dependency_overrides[api_auth.get_session] = _FakeSession
    app.dependency_overrides[get_audit_writer] = _NoopAuditWriter
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/workspace")

    assert response.status_code == 200
    assert response.json() == {
        "workspace_id": "flow-v1",
        "name": "FLOW",
        "primary_role": "finance_bp",
        "industry": "logistics_supply_chain",
        "timezone": "Asia/Shanghai",
        "currency": "CNY",
    }
