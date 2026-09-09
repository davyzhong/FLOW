"""O2 经营轨 L1 计算引擎测试（D050/OP 方法论）。

- 六主题返回：financial_report 主题消费 D01 条目出数；
  users_channels / revenue_structure 一律 not_applicable（typed 原因，OP-0）；
- 复用纪律：不另建口径——条目值与 D01 客观引擎逐条一致，杜邦带口径标注；
- 联动信号 ≤3、语义为提示复核（#11 财报可判部分）。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.operations.engine import build_operations_overview
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


def _seed(session: Session) -> Any:
    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="a" * 64,
    )
    report.status = "published"
    session.flush()
    normalize_report(session, report)
    return report


def test_six_themes_with_availability_layering(db_session: Session) -> None:
    report = _seed(db_session)
    overview = build_operations_overview(db_session, report_id=str(report.id))

    assert overview.catalog_id == "flow.analysis.objective_finance.v1"
    by_id = {theme.theme_id: theme for theme in overview.themes}
    assert set(by_id) == {
        "growth_quality",
        "revenue_structure",
        "cost_structure",
        "profit_quality",
        "users_channels",
        "operational_efficiency",
    }
    users = by_id["users_channels"]
    assert users.status == "not_applicable"
    assert users.reason == "internal_data_required"
    assert users.metrics == [], "L2 主题不得出任何数值"

    revenue_structure = by_id["revenue_structure"]
    assert revenue_structure.status == "not_applicable"
    assert revenue_structure.reason == "segment_disclosure_missing"


def test_financial_report_theme_metrics_carry_fact_card_fields(db_session: Session) -> None:
    """事实卡片四要素：值、比较基准（basis）、口径、来源引用；杜邦必须带口径标注。"""
    report = _seed(db_session)
    overview = build_operations_overview(db_session, report_id=str(report.id))
    profit = {t.theme_id: t for t in overview.themes}["profit_quality"]
    dupont = next(m for m in profit.metrics if m.entry_id == "dupont_three_factor")
    assert dupont.status == "computed"
    assert dupont.value is not None
    assert "净利润总额口径" in dupont.name or "净利润总额口径" in dupont.caliber_note, (
        "杜邦引用必须携带口径标注（U2/6.3 纪律）"
    )

    growth = {t.theme_id: t for t in overview.themes}["growth_quality"]
    revenue_yoy = next(m for m in growth.metrics if m.entry_id == "revenue_yoy")
    assert revenue_yoy.status == "computed"
    assert revenue_yoy.basis, "事实卡片必须带比较基准"


def test_management_watch_present_and_bounded(db_session: Session) -> None:
    report = _seed(db_session)
    overview = build_operations_overview(db_session, report_id=str(report.id))
    assert len(overview.management_watch) <= 3
    for item in overview.management_watch:
        assert set(item) >= {"code", "message", "direction"}


# ---- O2 slice-2：字典口径周转类求值 + 样本泛化 ----


def test_efficiency_theme_evaluates_dictionary_turnover_formulas(
    db_session: Session,
) -> None:
    """周转类指标按指标字典公式求值（avg=期初期末平均，同口径不出第二套）；
    财报事实齐备时 computed，缺口时 not_computable（typed），永不编造。"""
    report = _seed(db_session)
    overview = build_operations_overview(db_session, report_id=str(report.id))
    efficiency = {t.theme_id: t for t in overview.themes}["operational_efficiency"]
    codes = {m.entry_id: m for m in efficiency.metrics}
    assert {"current_ratio", "debt_asset_ratio", "inventory_turnover", "dso_days"} <= set(codes)
    for metric in efficiency.metrics:
        if metric.entry_id in {"current_ratio", "debt_asset_ratio"}:
            assert metric.source == "d01_entry", "已有 D01 条目复用，不重复求值"
        else:
            assert metric.source == "metric_dictionary"
        if metric.status == "computed":
            assert metric.value is not None and metric.basis
        else:
            assert metric.reason, f"{metric.entry_id} 不可算必须给 typed 原因"


def test_tencent_sample_generalizes(db_session: Session) -> None:
    """同引擎复用于港股 IFRS 样本：结构完整、分层语义一致、不抛错。"""
    import yaml as yaml_lib

    tencent_yaml = REPO_ROOT / "docs/implementation/p5/tencent_2026q2_statements.yaml"
    payload = yaml_lib.safe_load(tencent_yaml.read_text())
    report = import_statement_report(
        db_session,
        company_name="腾讯控股",
        stock_code="0700.HK",
        report_kind="二季报",
        period_label="2026Q2",
        payload=payload,
        source_ref="p5_samples/tencent_0700/Tencent_2026_Q2_results.pdf",
        source_sha256="t" * 64,
    )
    report.status = "published"
    db_session.flush()
    normalize_report(db_session, report)

    overview = build_operations_overview(db_session, report_id=str(report.id))
    by_id = {t.theme_id: t for t in overview.themes}
    assert len(by_id) == 6
    assert by_id["users_channels"].reason == "internal_data_required"
    computed = [
        m
        for t in overview.themes
        for m in t.metrics
        if m.status == "computed" and m.value is not None
    ]
    assert computed, "腾讯样本至少应有可算条目（如净现比/利润率类）"
