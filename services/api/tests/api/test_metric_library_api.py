"""指标库只读 API 契约测试。

GET /api/v1/metric-library 返回 flow.metric_dictionary.v0-draft 全量内容：
通用 40 + 物流 15 指标（含嵌套公式与 MPM 标记）、28 项 CAS↔IFRS 取数映射、
3 条勾稽关系、会计基础 164 科目 / 11 准则 / 17 分录模板。数据集为 config/metrics/
下的版本化 YAML（D040），本测试锁定结构完整性而非数值内容。
"""

from __future__ import annotations

from typing import Any

from httpx import ASGITransport, AsyncClient

from flow_api.main import create_app


async def test_metric_library_returns_full_dictionary() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/metric-library")
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()

    assert body["dictionary_id"] == "flow.metric_dictionary.v0-draft"
    assert body["status"] == "draft"
    assert body["decision_ref"] == "D040"

    metrics = body["metrics"]
    assert len(metrics) == 55
    general = [m for m in metrics if m["collection"] == "general"]
    logistics = [m for m in metrics if m["collection"] == "logistics"]
    assert len(general) == 40
    assert len(logistics) == 15
    assert any(m["mpm"] for m in metrics), "应存在 MPM 指标"
    assert any(
        any(isinstance(arg, dict) for arg in m["formula"]["args"]) for m in metrics
    ), "嵌套公式必须保留"
    dupont = next(m for m in metrics if m["metric_code"] == "roe")
    assert dupont["depends_on"] == ["net_margin", "total_asset_turnover", "equity_multiplier"]

    assert len(body["report_items"]) == 28
    assert {item["item_id"] for item in body["report_items"]} >= {"bs.total_assets", "is.revenue"}
    assert len(body["relations"]) == 3

    accounting = body["accounting"]
    assert accounting["dataset_id"] == "flow.accounting_foundation.v0-draft"
    assert len(accounting["accounts"]) == 164
    assert len(accounting["standards"]) == 11
    assert len(accounting["entry_templates"]) == 17
    assert accounting["known_gaps"], "已知缺口必须如实呈现"
