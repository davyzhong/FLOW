"""R4 端到端：TestClient 走完整 API 面（模板下载→上传→概览→cockpit→删除）。"""
from __future__ import annotations

import io

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from openpyxl import Workbook

from flow_api.api.routes.importer import set_store
from flow_api.importer.store import ImportStore
from flow_api.main import create_app


@pytest.fixture()
def client() -> TestClient:
    from sqlalchemy.pool import StaticPool

    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    set_store(ImportStore(engine))
    app = create_app()
    return TestClient(app)


def _workbook_bytes(unbalanced: bool = False) -> bytes:
    workbook = Workbook()
    ws = workbook.active
    ws.title = "科目余额表"
    ws.append(["会计期间", "科目编码", "科目名称", "科目类别", "方向",
               "期初余额", "本期借方发生额", "本期贷方发生额", "期末余额"])
    closing = "12000"
    opposite = "55555" if unbalanced else "12000"
    ws.append(["2025-01", "1001", "库存现金", "资产", "借", "10000", "0", "0", closing])
    ws.append(["2025-01", "2001", "短期借款", "负债", "贷", "10000", "0", "0", opposite])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()



def test_e2e_template_download(client: TestClient) -> None:
    response = client.get("/api/v1/importer/template/trial_balance")
    assert response.status_code == 200
    assert response.content[:2] == b"PK"


def test_e2e_upload_cockpit_overview_delete(client: TestClient) -> None:
    response = client.post(
        "/api/v1/importer/dataset?name=E2E 账套",
        files={"file": ("e2e.xlsx", _workbook_bytes())},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    dataset_id = body["dataset_id"]
    assert body["trial_balance_rows"] == 2

    overview = client.get(f"/api/v1/importer/dataset/{dataset_id}/overview").json()
    assert overview["total_assets"] == "12000"
    assert overview["identity_check"] == "0"

    cockpit = client.get(f"/api/v1/importer/dataset/{dataset_id}/cockpit").json()
    kpis = {kpi["code"]: kpi["value"] for kpi in cockpit["kpi"]}
    assert kpis["total_assets"] == "12000"
    assert cockpit["identity_check"]["passed"] is True

    balances = client.get(f"/api/v1/importer/dataset/{dataset_id}/balances").json()
    assert len(balances["rows"]) == 2

    deleted = client.delete(f"/api/v1/importer/dataset/{dataset_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/importer/dataset/{dataset_id}/overview").status_code == 404


def test_e2e_unbalanced_rejected_with_row_errors(client: TestClient) -> None:
    response = client.post(
        "/api/v1/importer/dataset",
        files={"file": ("bad.xlsx", _workbook_bytes(unbalanced=True))},
    )
    body = response.json()
    assert body["ok"] is False
    assert any("期末借贷不平衡" in error["message"] for error in body["errors"])


def test_e2e_dataset_list(client: TestClient) -> None:
    client.post(
        "/api/v1/importer/dataset?name=清单账套",
        files={"file": ("list.xlsx", _workbook_bytes())},
    )
    datasets = client.get("/api/v1/importer/dataset").json()["datasets"]
    assert len(datasets) == 1
    assert datasets[0]["name"] == "清单账套"
