"""S01 Task 7（模块边界）API 测试：只读 /api/v1/modules 与合同 fixture。"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from flow_api.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_modules_endpoint_returns_contract_fixture(client: TestClient) -> None:
    response = client.get("/api/v1/modules")
    assert response.status_code == 200
    body = response.json()
    modules = body["modules"]
    assert {m["id"] for m in modules} == {
        "public_analysis",
        "internal_workbench",
        "professional_governance",
    }
    assert "shared_core" not in {m["id"] for m in modules}
    by_id = {m["id"]: m for m in modules}
    assert by_id["public_analysis"] == {
        "id": "public_analysis",
        "name": "公开财报分析",
        "layer": "product",
        "status": "implemented",
    }
    assert by_id["internal_workbench"]["status"] == "designed"
    assert by_id["professional_governance"]["layer"] == "governance"


def test_modules_endpoint_is_read_only_and_typed(client: TestClient) -> None:
    post = client.post("/api/v1/modules")
    assert post.status_code in (404, 405), "模块端点必须只读"
