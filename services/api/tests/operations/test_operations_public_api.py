"""公开经营期间 API：季度数据无需伪造空财报即可被前端读取。"""

from fastapi.testclient import TestClient

from flow_api.main import app


def test_lists_real_public_operating_periods() -> None:
    response = TestClient(app).get("/api/v1/operations/public-periods")

    assert response.status_code == 200
    cainiao = [
        item for item in response.json()["periods"] if item["stock_code"] == "CAINIAO"
    ]
    assert {item["period_label"] for item in cainiao} >= {
        "FY2023",
        "Q1FY2023",
        "Q1FY2024",
    }


def test_gets_quarter_overview_without_statement_report() -> None:
    response = TestClient(app).get(
        "/api/v1/operations/public/CAINIAO/Q1FY2024"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report_id"] == "operating:CAINIAO:Q1FY2024"
    metrics = {
        metric["entry_id"]: metric
        for theme in body["themes"]
        for metric in theme["metrics"]
    }
    assert metrics["international_parcels"]["value"] == "439"
    assert metrics["international_parcels"]["assurance"] == "unaudited"


def test_unknown_public_period_is_typed_404() -> None:
    response = TestClient(app).get(
        "/api/v1/operations/public/CAINIAO/Q2FY2024"
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "operating_period_not_found"
