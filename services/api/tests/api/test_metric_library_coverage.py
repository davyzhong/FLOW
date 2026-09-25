"""指标库覆盖矩阵只读端点（GET /api/v1/metric-library/coverage）。

被测契约：
- 默认（dataset=public）返回 P5 真实财报矩阵：15 个公司期间快照 × 40 个通用指标，
  逐格带 display/missing；
- dataset=damai 返回独立 synthetic 矩阵（大麦物流两年快照，synthetic=true），
  缺口格保留结构化 missing，不以 0 补值；
- 未知数据集返回 400 + ErrorDetail(coverage_dataset_unknown)；
- 数据集缺失时返回 404 + ErrorDetail(coverage_dataset_missing)。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from flow_api.api.routes import metric_library
from flow_api.api.routes.metric_library import _coverage_payload
from flow_api.main import create_app


def _client() -> TestClient:
    # 全量应用：启动时注册 durable AuditWriter（§6 fail closed，裸路由会 503）
    return TestClient(create_app())


def setup_function() -> None:
    _coverage_payload.cache_clear()


def test_coverage_endpoint_returns_full_matrix() -> None:
    response = _client().get("/api/v1/metric-library/coverage")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == "flow.p5_metric_coverage.v1"
    assert body["synthetic"] is False
    assert body["caliber_notes"], "口径说明必须随数据集下发"
    assert len(body["snapshots"]) == 15
    assert len(body["metrics"]) == 40

    snapshot_keys = {f"{s['company']} {s['period']}" for s in body["snapshots"]}
    for metric in body["metrics"]:
        assert set(metric["cells"]) == snapshot_keys
        for cell in metric["cells"].values():
            assert "display" in cell and "missing" in cell
            # 可计算与缺口互斥：有 display 则无 missing，反之亦然
            assert (cell["display"] is None) != (cell["missing"] is None)


def test_coverage_endpoint_damai_dataset_is_synthetic_and_honest() -> None:
    response = _client().get("/api/v1/metric-library/coverage?dataset=damai")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == "flow.damai_demo_metric_coverage.v1"
    assert body["synthetic"] is True, "大麦矩阵必须带 synthetic 标识"
    assert {s["company"] for s in body["snapshots"]} == {"damai_syn"}
    assert {s["period"] for s in body["snapshots"]} == {"FY2025", "FY2026"}
    assert len(body["metrics"]) == 40

    snapshot_keys = {f"{s['company']} {s['period']}" for s in body["snapshots"]}
    missing_cells = 0
    for metric in body["metrics"]:
        assert set(metric["cells"]) == snapshot_keys
        for cell in metric["cells"].values():
            assert (cell["display"] is None) != (cell["missing"] is None)
            if cell["missing"] is not None:
                missing_cells += 1
                assert cell["missing"].startswith(("bs.", "is.", "cf.", "mpm.")), (
                    "缺口必须是结构化取数原因，不是文案"
                )
    assert missing_cells > 0, "覆盖矩阵必须如实暴露缺口（不得全绿冒充）"
    for snapshot in body["snapshots"]:
        assert 0 < snapshot["computable"] < snapshot["total"]


def test_coverage_endpoint_rejects_unknown_dataset() -> None:
    response = _client().get("/api/v1/metric-library/coverage?dataset=bogus")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "coverage_dataset_unknown"


def test_coverage_endpoint_404_when_dataset_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(metric_library, "CONFIG_ROOT", f"/{tmp_path.name}/none")
    _coverage_payload.cache_clear()
    response = _client().get("/api/v1/metric-library/coverage")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "coverage_dataset_missing"
    response = _client().get("/api/v1/metric-library/coverage?dataset=damai")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "coverage_dataset_missing"
