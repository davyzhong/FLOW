"""客观财务分析目录与引擎（D01）测试。

- 真实顺丰样本：归一化后同比/结构/杜邦可计算，结果携带基准、口径、引用；
- 数据不足：缺失项目显式 not_computable（typed 原因），不伪造数值；
- 分母为零 → zero_denominator；formula_ref 条目 → not_applicable（留给 D02）；
- 事实陈述不含主观因果用语。
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.analysis.objective import ObjectiveAnalysisService, ObjectiveStatus
from flow_api.infrastructure.models.statement import (
    StatementCorrection,
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        StatementCorrection,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _import_and_normalize(session: Session, payload: dict | None = None) -> StatementReport:
    data = payload or yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=data,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
    )
    normalize_report(session, report)
    return report


def test_sf_objective_analysis_computed_with_provenance(session: Session) -> None:
    report = _import_and_normalize(session)
    result = ObjectiveAnalysisService(session).analyze(report.id)
    by_id = {entry.entry_id: entry for entry in result.entries}

    revenue_yoy = by_id["revenue_yoy"]
    assert revenue_yoy.status == ObjectiveStatus.COMPUTED
    expected = Decimal("74142121") / Decimal("69849924") - 1
    assert abs(Decimal(revenue_yoy.value) - expected) < Decimal("0.000001")
    assert "is.revenue(cur)" in revenue_yoy.refs
    assert revenue_yoy.basis
    assert revenue_yoy.caliber_note

    structure = by_id["asset_structure"]
    assert structure.status == ObjectiveStatus.COMPUTED
    assert structure.parts, "结构条目应有分项"

    dupont = by_id["dupont_three_factor"]
    assert dupont.status == ObjectiveStatus.COMPUTED
    # U2/6.3 口径标注锁定：条目名与因子必须携带口径，防止与归母口径同名混淆
    assert "净利润总额口径" in dupont.name
    factors = {p["factor"]: p["value"] for p in dupont.parts}
    roe = Decimal(factors["roe(净利润总额口径·期末权益·未年化)"])
    product = (
        Decimal(factors["net_margin(净利润总额口径)"])
        * Decimal(factors["total_asset_turnover"])
        * Decimal(factors["equity_multiplier(期末权益)"])
    )
    assert abs(roe - product) < Decimal("0.000001"), "杜邦乘积必须闭合"


def test_missing_data_not_computable_not_fabricated(session: Session) -> None:
    payload = {
        "unit": "人民币千元",
        "statements": {
            "合并资产负债表": [
                {"item": "货币资金", "期末余额": 100, "期初余额": 90},
            ]
        },
    }
    report = _import_and_normalize(session, payload)
    result = ObjectiveAnalysisService(session).analyze(report.id)
    by_id = {entry.entry_id: entry for entry in result.entries}
    assert by_id["revenue_yoy"].status == ObjectiveStatus.NOT_COMPUTABLE
    assert by_id["revenue_yoy"].reason == "missing_operand"
    assert by_id["revenue_yoy"].value is None
    assert by_id["asset_structure"].status == ObjectiveStatus.NOT_COMPUTABLE


def test_zero_denominator_and_formula_ref_handling(session: Session) -> None:
    payload = {
        "unit": "人民币千元",
        "statements": {
            "合并利润表": [
                {"item": "一、营业总收入", "本期发生额": 100, "上期发生额": 0},
                {"item": "五、净利润（净亏损以“－”号填列）", "本期发生额": 10, "上期发生额": 5},
            ],
        },
    }
    report = _import_and_normalize(session, payload)
    result = ObjectiveAnalysisService(session).analyze(report.id)
    by_id = {entry.entry_id: entry for entry in result.entries}
    assert by_id["revenue_yoy"].status == ObjectiveStatus.NOT_COMPUTABLE
    assert by_id["revenue_yoy"].reason == "zero_denominator"
    # formula_ref 条目不在本服务重复计算（D02 统一快照承接）
    assert by_id["gross_margin"].status == ObjectiveStatus.NOT_APPLICABLE


def test_no_subjective_causal_language(session: Session) -> None:
    report = _import_and_normalize(session)
    result = ObjectiveAnalysisService(session).analyze(report.id)
    banned = ("因为", "由于", "竞争", "预计将会", "我们认为")
    for entry in result.entries:
        text = f"{entry.name}{entry.caliber_note}{entry.reason or ''}"
        assert not any(word in text for word in banned), (
            f"主观因果用语进入事实结果：{entry.entry_id}"
        )
