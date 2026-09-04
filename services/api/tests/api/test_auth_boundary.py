"""Task A 契约测试：API 认证边界。

配置 `auth_token` 后：
- 除 GET /api/v1/health 外，所有 /api/v1 路由要求 Authorization: Bearer <token>；
- 缺失/错误凭据 → 401 {code:"unauthorized"}；token 比较恒时；
未配置（开发模式）时开放访问。
"""

from __future__ import annotations

from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from flow_api.main import create_app
from flow_api.settings import get_settings

TEST_TOKEN = "unit-test-token-0123456789"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(scope="module", autouse=True)
def restore_auth_env() -> None:
    yield
    import os

    os.environ.pop("AUTH_TOKEN", None)
    get_settings.cache_clear()


def _client_with_token(token: str | None) -> Any:
    get_settings.cache_clear()
    import os

    if token is None:
        os.environ.pop("AUTH_TOKEN", None)
    else:
        os.environ["AUTH_TOKEN"] = token
    app = create_app()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_missing_token_is_rejected_when_auth_enabled() -> None:
    client = _client_with_token(TEST_TOKEN)
    async with client as http:
        response = await http.get("/api/v1/workspace")
        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_wrong_token_is_rejected_with_constant_time_compare() -> None:
    client = _client_with_token(TEST_TOKEN)
    async with client as http:
        wrong = await http.get(
            "/api/v1/workspace", headers={"Authorization": "Bearer wrong-token"}
        )
        assert wrong.status_code == 401
        assert wrong.json()["detail"]["code"] == "unauthorized"
        malformed = await http.get(
            "/api/v1/workspace", headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert malformed.status_code == 401


@pytest.mark.asyncio
async def test_correct_token_grants_access() -> None:
    client = _client_with_token(TEST_TOKEN)
    async with client as http:
        response = await http.get(
            "/api/v1/workspace", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_is_exempt_from_auth() -> None:
    client = _client_with_token(TEST_TOKEN)
    async with client as http:
        response = await http.get("/api/v1/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_disabled_when_token_not_configured() -> None:
    client = _client_with_token(None)
    async with client as http:
        response = await http.get("/api/v1/workspace")
        assert response.status_code == 200
