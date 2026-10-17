"""批次 C-2：资产负债 / 营运资金模块页 API 测试。

前提：DAMAI.SYN 两期披露财报已导入、归一化并发布（ damai loader 语义）。
断言：
- 200 + KPI 值来自披露事实（总资产 FY2023 = 71,850,931 千元 → 71,850.931 百万）；
- 恒等口径：CCC = DSO + DIO − DPO（模块内计算一致）；
- 无来源块如实缺省（债务期限拆分、应收账龄、多主体排名）；
- 未发布报表环境 → 404 module_statements_not_published。
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from flow_api.api.routes.cockpit import get_cockpit_session
from flow_api.enterprise.models import AnalysisCycle
from flow_api.infrastructure.models.analytics import Finding, MetricSnapshot, Period
from flow_api.infrastructure.models.cockpit import ActionItem
from flow_api.infrastructure.models.intake import AnalysisBatch, ImportVersion
from flow_api.infrastructure.models.statement import StatementReport
from flow_api.settings import get_settings

CFO = "cockpit-cfo-a"
_ENTERPRISE = "00000000-0000-0000-0000-00000000d001"
REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (ActionItem, Finding, MetricSnapshot, ImportVersion, AnalysisBatch):
        session.execute(text(f"DELETE FROM {table.__tablename__}"))
    session.execute(text("DELETE FROM statement_normalized_item"))
    session.execute(text("DELETE FROM statement_report"))
    session.execute(text("DELETE FROM analysis_cycle"))
    session.add(
        AnalysisCycle(enterprise_id=uuid.UUID(_ENTERPRISE), period_key="2023-03")
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _import_and_publish(db_session: Session, fy: str) -> None:
    from pathlib import Path as _Path

    import yaml

    from flow_api.statements.importer import import_statement_report
    from flow_api.statements.normalization import normalize_report

    statement_path = _Path(REPO_ROOT) / f"fixtures/damai/statements/damai_{fy.lower()}.yaml"
    payload = yaml.safe_load(statement_path.read_text(encoding="utf-8"))
    report = import_statement_report(
        db_session,
        company_name="大麦物流",
        stock_code="DAMAI.SYN",
        report_kind="年报",
        period_label=fy,
        payload=payload,
        source_ref=f"fixtures/damai/statements/damai_{fy.lower()}.yaml",
        source_sha256="0" * 64,
    )
    db_session.commit()
    normalize_report(db_session, report)
    report.status = "published"
    db_session.commit()


@pytest.fixture()
def api_client(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    import os

    from fastapi.testclient import TestClient

    from flow_api.main import create_app

    _import_and_publish(db_session, "FY2022")
    _import_and_publish(db_session, "FY2023")
    # 模块快照上下文：任一批次即可（snapshot_id 只作追溯标识）
    db_session.add(
        MetricSnapshot(
            batch_id=_seed_batch(db_session),
            import_version_id=_seed_import(db_session),
            as_of_period_id=_seed_period(db_session),
            version=1,
            status="published",
            engine_version="test",
            definition_set_id="test",
            definition_set_hash="a" * 64,
            fingerprint="b" * 64,
        )
    )
    db_session.commit()
    os.environ["FLOW_DEV_ACTOR_ID"] = CFO
    get_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_cockpit_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    os.environ["FLOW_DEV_ACTOR_ID"] = "flow-dev-bp"
    get_settings.cache_clear()


def _seed_batch(db_session: Session) -> object:
    batch = AnalysisBatch(
        name="模块测试批次",
        created_by=CFO,
        module_kind="public",
        fact_context_version=1,
    )
    db_session.add(batch)
    db_session.flush()
    return batch.id


def _seed_import(db_session: Session) -> object:
    version = ImportVersion(
        batch_id=db_session.scalar(
            select(AnalysisBatch.id).order_by(AnalysisBatch.created_at.desc()).limit(1)
        ),
        sequence=1,
    )
    db_session.add(version)
    db_session.flush()
    return version.id


def _seed_period(db_session: Session) -> object:
    period = db_session.scalar(select(Period).where(Period.month_key == 202301))
    if period is None:
        period = Period(month_key=202301, year=2023, quarter=1, month=1)
        db_session.add(period)
        db_session.flush()
    return period.id


def test_balance_sheet_module_kpis_from_disclosed_facts(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/cockpit/modules/balance-sheet")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module"] == "balance-sheet"
    assert body["period"] == "FY2023"
    by_name = {kpi["name"]: kpi for kpi in body["kpis"]}
    assert by_name["总资产"]["value"] == "71850.9310"
    assert by_name["总负债"]["status"] == "available"
    assert by_name["资产负债率"]["status"] == "available"
    # 结构图两期齐备
    assert body["charts"]["asset_structure"]["periods"] == ["FY2022", "FY2023"]
    # 期限拆分如实缺省
    assert any(
        block["code"] == "debt_maturity_split_not_disclosed"
        for block in body["unavailable"]
    )


def test_working_capital_ccc_identity(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/cockpit/modules/working-capital")
    assert response.status_code == 200, response.text
    body = response.json()
    formula = body["charts"]["ccc_formula"]
    assert formula["identity"] == "CCC = DSO + DIO − DPO"
    ccc = Decimal(formula["ccc"])
    dso, dio, dpo = (
        Decimal(formula["dso"]),
        Decimal(formula["dio"]),
        Decimal(formula["dpo"]),
    )
    assert (dso + dio - dpo).quantize(Decimal("0.0001")) == ccc
    assert any(
        block["code"] == "ar_aging_not_disclosed" for block in body["unavailable"]
    )


def test_profitability_module_reads_frozen_analysis_payload(
    api_client: TestClient, db_session: Session
) -> None:
    from flow_api.publishing.objective_freeze import freeze_objective_statement_report

    reports = list(
        db_session.scalars(
            select(StatementReport).where(StatementReport.stock_code == "DAMAI.SYN")
        )
    )
    for report in reports:
        freeze_objective_statement_report(db_session, report_id=report.id)
    db_session.commit()

    response = api_client.get("/api/v1/cockpit/profitability")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["module"] == "profitability"
    assert [period["period"] for period in body["periods"]] == ["FY2022", "FY2023"]
    current = body["periods"][-1]
    assert current["snapshot_id"]
    assert all(metric["snapshot_id"] == current["snapshot_id"] for metric in current["metrics"])
    assert all(metric["report_id"] == current["report_id"] for metric in current["metrics"])
    assert all(metric["status"] == "available" for metric in current["metrics"])
    assert current["consistency"]["status"] == "passed"


def test_modules_404_when_statements_not_published(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:

    from fastapi.testclient import TestClient

    from flow_api.main import create_app

    app = create_app()
    app.dependency_overrides[get_cockpit_session] = lambda: db_session
    monkeypatch.setenv("FLOW_DEV_ACTOR_ID", CFO)
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/cockpit/modules/balance-sheet")
            assert response.status_code == 404
            assert (
                response.json()["detail"]["code"] == "module_statements_not_published"
            )
    finally:
        get_settings.cache_clear()
