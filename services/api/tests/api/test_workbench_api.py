"""U7 四问工作台 typed 端点契约测试。

GET /api/v1/analysis/workbench/{report_id}
- 200：四问结构 + 每问指标可用性与预计算值 + facts_available；
- 404 statement_report_not_found：未知报告；
- 可用性：缺上年同期（prev）时增长类指标 available=false，不编造。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.api.routes.objective_reports import get_objective_session
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.main import create_app
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (StatementNormalizedItem, StatementLineItem, StatementReport):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
async def client(db_session: Session) -> Iterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_objective_session] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


def _import(db_session: Session) -> Any:
    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        db_session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="a" * 64,
    )
    db_session.flush()
    normalize_report(db_session, report)
    return report


async def test_workbench_returns_four_questions(
    client: AsyncClient, db_session: Session
) -> None:
    report = _import(db_session)
    db_session.commit()
    response = await client.get(f"/api/v1/analysis/workbench/{report.id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert [q["key"] for q in body["questions"]] == ["growth", "profit", "capital", "cash"]
    assert body["report"]["company_name"] == "顺丰控股"
    # 事实核对：capital 域的资产负债率可算（归一化事实齐备）
    capital = next(q for q in body["questions"] if q["key"] == "capital")
    debt = next(m for m in capital["metrics"] if m["metric_code"] == "debt_asset_ratio")
    assert debt["available"] is True and debt["value"] == "0.4780"
    # 增长类指标：归一行携带上期对照（value_prior → __prev facts）→ 可算且为真实披露投影
    growth = next(q for q in body["questions"] if q["key"] == "growth")
    rev = next(m for m in growth["metrics"] if m["metric_code"] == "revenue_growth")
    assert rev["available"] is True and rev["value"] is not None
    # 管理关注（借鉴 #5）：≤3 条、条条带值带向
    watch = body["management_watch"]
    assert len(watch) <= 3
    for item in watch:
        assert set(item) >= {"code", "message", "direction"}


async def test_workbench_unknown_report_404(client: AsyncClient) -> None:
    from uuid import uuid4

    response = await client.get(f"/api/v1/analysis/workbench/{uuid4()}")
    assert response.status_code == 404


# ---- U7 收尾：管理关注（借鉴 #5：≤3 条、条条带值带向、无普适阈值、不断言因果） ----


def test_facts_carry_prior_values_for_growth() -> None:
    """修复：归一行的上期值必须进入 facts（{item}__prev），增长类指标不再永远不可用。"""
    from decimal import Decimal

    from flow_api.analysis.workbench import _facts_from_rows

    class _Row:
        def __init__(self, item_id: str, current: Any, prior: Any) -> None:
            self.item_id = item_id
            self.value_current = current
            self.value_prior = prior
            self.value_end = None
            self.value_begin = None

    rows = [
        _Row("is.revenue", Decimal("100"), Decimal("90")),
        _Row("bs.total_assets", Decimal("500"), Decimal("480")),
    ]
    facts = _facts_from_rows(rows)  # type: ignore[arg-type]
    assert facts["is.revenue"] == Decimal("100")
    assert facts["is.revenue__prev"] == Decimal("90"), "上期值必须以 __prev 键保留"
    assert facts["bs.total_assets__prev"] == Decimal("480")


def test_management_watch_output_contract() -> None:
    """管理关注 ≤3 条；每条含 code/message/direction；message 携带数值；纯函数确定性。"""
    from decimal import Decimal

    from flow_api.analysis.workbench import management_watch

    facts = {
        "is.revenue": Decimal("100"),
        "is.revenue__prev": Decimal("120"),  # 收入下降
        "cf.ocf": Decimal("30"),
        "is.net_profit": Decimal("50"),  # 净现比 0.6 < 1
        "bs.ar": Decimal("40"),
        "bs.ar__prev": Decimal("20"),  # 应收 +100%
        "is.revenue__prev_alt": None,
    }
    watch = management_watch(facts)
    assert len(watch) <= 3, "管理关注最多 3 条（借鉴 #5）"
    for item in watch:
        assert set(item) >= {"code", "message", "direction"}
        assert item["direction"] in {"negative", "warning"}
        assert any(ch.isdigit() for ch in item["message"]), "每条必须携带数值"
    codes = [item["code"] for item in watch]
    assert "revenue_decline" in codes
    assert "cash_content_below_one" in codes
    assert "ar_outpacing_revenue" in codes
    # 确定性：同输入同输出
    assert management_watch(facts) == watch


def test_management_watch_empty_when_no_signals() -> None:
    """无命中信号时返回空列表，不硬凑、不输出正面表扬。"""
    from decimal import Decimal

    from flow_api.analysis.workbench import management_watch

    facts = {
        "is.revenue": Decimal("110"),
        "is.revenue__prev": Decimal("100"),  # 收入增长
        "cf.ocf": Decimal("120"),
        "is.net_profit": Decimal("50"),  # 净现比 2.4 > 1
        "bs.ar": Decimal("10"),
        "bs.ar__prev": Decimal("12"),  # 应收下降
    }
    assert management_watch(facts) == []


def test_management_watch_handles_missing_facts_gracefully() -> None:
    """缺口径时不报错、不编造：相关规则跳过。"""
    from decimal import Decimal

    from flow_api.analysis.workbench import management_watch

    assert management_watch({}) == []
    watch = management_watch({"is.revenue": Decimal("100")})  # 无 prev、无其他
    assert watch == []
