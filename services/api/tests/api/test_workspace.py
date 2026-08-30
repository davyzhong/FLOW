from httpx import ASGITransport, AsyncClient

from flow_api.main import create_app


async def test_workspace_contract() -> None:
    transport = ASGITransport(app=create_app())
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
