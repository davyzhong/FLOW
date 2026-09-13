"""指标库 P5 真实财报覆盖矩阵只读端点（GET /api/v1/metric-library/coverage）。

被测契约：
- 数据集存在时返回完整投影：15 个公司期间快照 × 40 个通用指标，逐格带 display/missing；
- 数据集缺失时返回 404 + ErrorDetail(coverage_dataset_missing)。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from flow_api.api.routes import metric_library
from flow_api.api.routes.metric_library import _coverage_payload, router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def setup_function() -> None:
    _coverage_payload.cache_clear()


def test_coverage_endpoint_returns_full_matrix() -> None:
    response = _client().get("/api/v1/metric-library/coverage")
    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == "flow.p5_metric_coverage.v1"
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


def test_coverage_endpoint_404_when_dataset_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(metric_library, "CONFIG_ROOT", f"/{tmp_path.name}/none")
    _coverage_payload.cache_clear()
    response = _client().get("/api/v1/metric-library/coverage")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "coverage_dataset_missing"
