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

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.api.routes import metric_library
from flow_api.api.routes.metric_library import _coverage_payload
from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport
from flow_api.main import create_app
from flow_api.settings import get_settings


def _client() -> TestClient:
    # 全量应用：启动时注册 durable AuditWriter（§6 fail closed，裸路由会 503）
    return TestClient(create_app())


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


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
    computable_by_period = {
        snapshot["period"]: snapshot["computable"] for snapshot in body["snapshots"]
    }
    assert computable_by_period == {"FY2025": 37, "FY2026": 40}


def test_coverage_endpoint_rejects_unknown_dataset() -> None:
    response = _client().get("/api/v1/metric-library/coverage?dataset=bogus")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "coverage_dataset_unknown"


@pytest.fixture
def seeded_statement_reports() -> Iterator[dict[tuple[str, str], str]]:
    """向测试库写入两份财报（顺丰 2026Q1 / 腾讯 2026Q2），验证列头 report_id 映射。

    先清空 statement_report 存量（其他测试模块可能遗留），用例结束恢复为空，
    保证全量套件任意执行顺序下映射断言确定性。
    """

    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    session.execute(delete(StatementLineItem))
    session.execute(delete(StatementReport))
    reports = [
        StatementReport(
            company_name="顺丰控股",
            stock_code="002352.SZ",
            report_kind="一季报",
            period_label="2026Q1",
            unit_note="人民币千元",
            source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        ),
        StatementReport(
            company_name="腾讯控股",
            stock_code="0700.HK",
            report_kind="中期业绩公告",
            period_label="2026Q2",
            unit_note="人民币百万元",
            source_ref="p5_samples/tencent_0700/Tencent_2026_Q2_results.pdf",
        ),
    ]
    session.add_all(reports)
    session.commit()
    mapping = {(r.stock_code, r.period_label): str(r.id) for r in reports}
    try:
        yield mapping
    finally:
        session.execute(delete(StatementLineItem))
        session.execute(delete(StatementReport))
        session.commit()
        session.close()
        engine.dispose()


def test_coverage_snapshots_map_report_id_when_statement_report_exists(
    seeded_statement_reports: dict[tuple[str, str], str],
) -> None:
    response = _client().get("/api/v1/metric-library/coverage")
    assert response.status_code == 200
    by_key = {(s["company"], s["period"]): s for s in response.json()["snapshots"]}

    sf = by_key[("sf_002352", "2026Q1")]
    assert sf["report_id"] == seeded_statement_reports[("002352.SZ", "2026Q1")]
    # 期间标签归一：覆盖矩阵「2Q2026」= 财报「2026Q2」（同一披露期间）
    tencent = by_key[("tencent_0700", "2Q2026")]
    assert tencent["report_id"] == seeded_statement_reports[("0700.HK", "2026Q2")]
    # 未导入对应财报的快照：report_id 为 None（诚实约束，前端不渲染链接）
    assert by_key[("alibaba_9988", "FY2019")]["report_id"] is None
    assert by_key[("jd_logistics_2618", "2026Q1")]["report_id"] is None


def test_coverage_damai_snapshots_never_map_report_id(
    seeded_statement_reports: dict[tuple[str, str], str],
) -> None:
    response = _client().get("/api/v1/metric-library/coverage?dataset=damai")
    assert response.status_code == 200
    # synthetic 数据集无对应真实财报，全部不映射（诚实约束）
    assert all(s["report_id"] is None for s in response.json()["snapshots"])


def test_coverage_endpoint_404_when_dataset_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(metric_library, "CONFIG_ROOT", f"/{tmp_path.name}/none")
    _coverage_payload.cache_clear()
    response = _client().get("/api/v1/metric-library/coverage")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "coverage_dataset_missing"
    response = _client().get("/api/v1/metric-library/coverage?dataset=damai")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "coverage_dataset_missing"
