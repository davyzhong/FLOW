"""API 认证边界契约测试（S01 规格 §3.2 legacy Bearer + §2.2 development 模式）。

自 2A 认证合同升级后，本文件覆盖无 DB 环境可判定的负路径：
- 配置 AUTH_TOKEN 后：缺凭据 → 401 `authentication_required`；
  错误凭据 → 401 `credential_invalid`；格式非法 → 401；
- 未配置任何凭据且无 dev actor：一律 401（fail-closed，不再「未配置即放行」）；
- /api/v1/health 豁免。
正路径（正确 token → service_account Principal、dev actor → Principal）
依赖 DB RoleBinding（§3.1.5 DB 唯一权威），由 tests/security/ 与集成线覆盖；
本文件在有 DB 时也探测验证，无 DB（unit job，port 1）时跳过正路径。
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from flow_api.main import create_app
from flow_api.security.audit import get_audit_writer
from flow_api.settings import get_settings


class _NoopAuditWriter:
    """unit job 无 DB：审计屏障用 no-op writer（持久化语义由 security 测试覆盖）。"""

    def write_decision(self, **kwargs: object) -> None:
        return None

    def write_intent(self, **kwargs: object) -> None:
        return None

    def write_outcome(self, **kwargs: object) -> None:
        return None

TEST_TOKEN = "unit-test-token-0123456789"
# §3.2 legacy 冻结身份（与 conftest 种子的 local-dev-web binding 同值）
LEGACY_ACTOR = "local-dev-web"
LEGACY_ENTERPRISE = "00000000-0000-0000-0000-00000000d001"


@pytest.fixture(autouse=True)
def restore_auth_env() -> None:
    """每个用例独立隔离 AUTH_TOKEN / FLOW_DEV_ACTOR_ID，不依赖执行顺序。"""
    saved = (
        os.environ.get("AUTH_TOKEN"),
        os.environ.get("FLOW_DEV_ACTOR_ID"),
        os.environ.get("FLOW_LEGACY_ACTOR_ID"),
        os.environ.get("FLOW_LEGACY_ENTERPRISE_ID"),
    )
    get_settings.cache_clear()
    yield
    for name, value in zip(
        ("AUTH_TOKEN", "FLOW_DEV_ACTOR_ID", "FLOW_LEGACY_ACTOR_ID", "FLOW_LEGACY_ENTERPRISE_ID"),
        saved,
        strict=True,
    ):
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    get_settings.cache_clear()


def _client_without_dev_actor(token: str | None) -> Any:
    """配置 legacy token、显式关闭 dev 模式（不触 DB 的负路径前提）。"""
    get_settings.cache_clear()
    if token is None:
        os.environ.pop("AUTH_TOKEN", None)
    else:
        os.environ["AUTH_TOKEN"] = token
        os.environ["FLOW_LEGACY_ACTOR_ID"] = LEGACY_ACTOR
        os.environ["FLOW_LEGACY_ENTERPRISE_ID"] = LEGACY_ENTERPRISE
    os.environ.pop("FLOW_DEV_ACTOR_ID", None)
    app = create_app()
    app.dependency_overrides[get_audit_writer] = _NoopAuditWriter
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _database_reachable() -> bool:
    try:
        from sqlalchemy import text

        from flow_api.infrastructure.db import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - unit job 刻意无 DB（port 1）
        return False


@pytest.mark.asyncio
async def test_missing_token_is_rejected_when_auth_enabled() -> None:
    client = _client_without_dev_actor(TEST_TOKEN)
    async with client as http:
        response = await http.get("/api/v1/workspace")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "authentication_required"


@pytest.mark.asyncio
async def test_wrong_token_is_rejected_with_constant_time_compare() -> None:
    client = _client_without_dev_actor(TEST_TOKEN)
    async with client as http:
        wrong = await http.get(
            "/api/v1/workspace", headers={"Authorization": "Bearer wrong-token"}
        )
        assert wrong.status_code == 401
        assert wrong.json()["detail"]["code"] == "credential_invalid"
        malformed = await http.get(
            "/api/v1/workspace", headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert malformed.status_code == 401


@pytest.mark.asyncio
async def test_fail_closed_when_nothing_configured() -> None:
    """规格升级点：未配置任何凭据且无 dev actor 时不再开放访问。

    该分支在 require_bearer_auth 内部兜底（未进入 resolve_principal），
    错误码为 unauthorized。
    """
    client = _client_without_dev_actor(None)
    async with client as http:
        response = await http.get("/api/v1/workspace")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_health_endpoint_is_exempt_from_auth() -> None:
    client = _client_without_dev_actor(TEST_TOKEN)
    async with client as http:
        response = await http.get("/api/v1/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_correct_token_grants_access() -> None:
    if not _database_reachable():
        pytest.skip("legacy Bearer 正路径需要 DB service_account binding（§3.2）")
    get_settings.cache_clear()
    os.environ["AUTH_TOKEN"] = TEST_TOKEN
    os.environ["FLOW_LEGACY_ACTOR_ID"] = LEGACY_ACTOR
    os.environ["FLOW_LEGACY_ENTERPRISE_ID"] = LEGACY_ENTERPRISE
    os.environ.pop("FLOW_DEV_ACTOR_ID", None)
    # conftest._seed_dev_principal 已播种与冻结身份匹配的 service_account binding
    app = create_app()
    app.dependency_overrides[get_audit_writer] = _NoopAuditWriter
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        response = await http.get(
            "/api/v1/workspace", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
    assert response.status_code == 200
