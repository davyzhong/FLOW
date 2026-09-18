"""指标库只读 API 契约测试。

GET /api/v1/metric-library 返回 flow.metric_dictionary.v1（D047 定稿）全量内容：
通用 50 + 物流 15 指标（含嵌套公式、MPM 标记与默认口径裁决）、16 行业参考包、
28 项 CAS↔IFRS 取数映射、3 条勾稽关系、会计基础 167 科目 / 48 准则 / 32 分录模板。
数据集为 config/metrics/ 下的版本化 YAML，本测试锁定结构完整性而非数值内容。
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

    assert body["dictionary_id"] == "flow.metric_dictionary.v1"
    assert body["status"] == "effective"
    assert body["decision_ref"].startswith("D047")

    metrics = body["metrics"]
    assert len(metrics) == 65
    general = [m for m in metrics if m["collection"] == "general"]
    logistics = [m for m in metrics if m["collection"] == "logistics"]
    assert len(general) == 50
    assert len(logistics) == 15
    # P01/C02：MPM 是监管级断言，静态字典不得授予——须携带结构化判定（候选/不适用）
    assert not any(m["mpm"] for m in metrics), "静态字典不得打监管 MPM 标签"
    ebitda = next(m for m in metrics if m["metric_code"] == "ebitda")
    assert (ebitda.get("mpm_review") or {}).get("determination") == "candidate"
    assert (ebitda.get("mpm_review") or {}).get("basis"), "候选判定必须携带依据（IFRS 18 条款）"
    assert any(
        any(isinstance(arg, dict) for arg in m["formula"]["args"]) for m in metrics
    ), "嵌套公式必须保留"
    dupont = next(m for m in metrics if m["metric_code"] == "roe")
    assert dupont["depends_on"] == ["net_margin", "total_asset_turnover", "equity_multiplier"]
    # D047：口径分歧项必须有默认口径裁决与依据
    assert dupont["default_caliber"].startswith("净利润 ÷ 平均净资产")
    assert dupont["default_basis"]
    assert dupont["alternative_calibers"]
    ruled = [m for m in metrics if m.get("default_caliber")]
    assert len(ruled) == 15, "15 项口径裁决必须全部生效"

    assert len(body["report_items"]) == 28
    assert {item["item_id"] for item in body["report_items"]} >= {"bs.total_assets", "is.revenue"}
    assert len(body["relations"]) == 3

    # 借鉴 #21 行业参考包 v1.2：YAML 权威、零迁移（与 relations 同模式，DB 无列透传）
    packs = body["industry_reference_packs"]
    assert len(packs) == 16
    pack_ids = {p["industry_id"] for p in packs}
    assert pack_ids >= {"ecommerce", "logistics", "local_services", "retail", "manufacturing"}
    assert all(p["provenance"] for p in packs), "行业参考包必须登记来源"
    retail = next(p for p in packs if p["industry_id"] == "retail")
    assert "current_asset_ratio" in retail["financial_reference"]
    logistics_pack = next(p for p in packs if p["industry_id"] == "logistics")
    assert len(logistics_pack["ops_indicators"]) == 3
    assert all(ind["meaning"] for p in packs for ind in p["ops_indicators"])
    # 新增通用指标：流动资产率（结构比率，facts 可执行：bs.* 项目已登记 + div 受支持）
    car = next(m for m in metrics if m["metric_code"] == "current_asset_ratio")
    assert car["formula"]["args"] == ["bs.current_assets", "bs.total_assets"]
    assert car["domain"] == "operation"

    accounting = body["accounting"]
    assert accounting["dataset_id"] == "flow.accounting_foundation.v1"
    assert len(accounting["accounts"]) == 167
    assert len(accounting["standards"]) == 48
    assert len(accounting["entry_templates"]) == 32
    cas_numbers = sorted(
        int(s["id"].split("-")[1])
        for s in accounting["standards"]
        if s["id"].startswith("CAS-") and s["id"].split("-")[1].isdigit()
    )
    assert cas_numbers == list(range(1, 43)), "42 项具体准则必须全量登记"
    assert any(a["code"] == "1802" for a in accounting["accounts"]), "使用权资产编号正式化"
    assert accounting["known_gaps"], "已知缺口必须如实呈现"


async def test_semantic_context_projects_four_elements() -> None:
    """O-01：语义上下文 = 对象/维度/限定/值投影，引用身份齐备。"""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/metric-library/semantic-context")
        assert response.status_code == 200, response.text
        filtered = await client.get(
            "/api/v1/metric-library/semantic-context?codes=current_ratio,quick_ratio"
        )
    body: dict[str, Any] = response.json()
    assert body["dictionary_id"] == "flow.metric_dictionary.v1"
    assert body["metric_count"] == 65

    current_ratio = next(
        m for m in body["metrics"] if m["metric_code"] == "current_ratio"
    )
    assert current_ratio["object"]["definition"]
    assert "benchmark" in current_ratio["dimensions"]
    assert current_ratio["qualifications"]["benchmark"]
    assert current_ratio["qualifications"]["caliber"]
    assert current_ratio["value"]["formula_text"]
    assert current_ratio["value"]["unit"] == "倍"
    assert current_ratio["entry_id"], "DB 在效条目必须携带 entry_id 供引用回链"

    assert filtered.status_code == 200
    filtered_body = filtered.json()
    assert filtered_body["metric_count"] == 2
    assert {m["metric_code"] for m in filtered_body["metrics"]} == {
        "current_ratio",
        "quick_ratio",
    }


async def test_computation_proposal_verified_matches_facts() -> None:
    """O-02：治理指标提议 → 确定性复算；数值与事实库独立核对一致。"""
    from decimal import Decimal

    from flow_api.api.routes.metric_library import resolve_metric_library_root
    from flow_api.infrastructure.db import get_session_factory
    from flow_api.metric_library_store.importer import import_all

    root = resolve_metric_library_root()
    with get_session_factory()() as session:
        import_all(session, root / "config" / "metrics")
        session.commit()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/metric-library/computation-proposals",
            json={
                "metric_code": "current_ratio",
                "company": "sf_002352",
                "period": "2026Q1",
            },
        )
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    assert body["status"] == "verified", body
    assert body["refusal_code"] is None
    assert body["entry_id"]
    assert body["referenced_items"] == ["bs.current_assets", "bs.current_liab"]

    # 独立核对：直接从事实库取期末值相除（不复用求值器路径）
    import yaml as _yaml

    facts_path = root / "docs" / "implementation" / "p5" / "statement_facts.yaml"
    facts_doc = _yaml.safe_load(facts_path.read_text(encoding="utf-8"))
    values = {
        (fact["item_id"], fact["role"]): Decimal(str(fact["value"]))
        for fact in facts_doc["facts"]
        if fact["company"] == "sf_002352" and fact["period"] == "2026Q1"
    }
    expected = values[("bs.current_assets", "end")] / values[("bs.current_liab", "end")]
    assert Decimal(body["value"]) == expected


async def test_computation_proposal_refusals_are_structured() -> None:
    """O-02：未知指标 / 缺事实都是结构化 refusal，绝不编造数值。"""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unknown = await client.post(
            "/api/v1/metric-library/computation-proposals",
            json={
                "metric_code": "no_such_metric",
                "company": "sf_002352",
                "period": "2026Q1",
            },
        )
        missing = await client.post(
            "/api/v1/metric-library/computation-proposals",
            json={
                "metric_code": "current_ratio",
                "company": "no_such_company",
                "period": "2026Q1",
            },
        )
        inventory = await client.get("/api/v1/metric-library/computation-inventory")
    assert unknown.status_code == 200
    unknown_body: dict[str, Any] = unknown.json()
    assert unknown_body["status"] == "refused"
    assert unknown_body["refusal_code"] == "unknown_metric"
    assert unknown_body["value"] is None

    assert missing.status_code == 200
    missing_body: dict[str, Any] = missing.json()
    assert missing_body["status"] == "refused"
    assert missing_body["refusal_code"] == "missing_fact"

    assert inventory.status_code == 200
    inventory_body: dict[str, Any] = inventory.json()
    sf = next(
        c for c in inventory_body["companies"] if c["company"] == "sf_002352"
    )
    assert "2026Q1" in sf["periods"]
