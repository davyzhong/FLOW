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
from flow_api.operations.engine import _segment_revenue_theme, build_operations_overview
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


# ---- O2 slice-2 续：菜鸟（CAINIAO）样本接入——物流企业，经营轨重点样本 ----


def test_cainiao_sample_core_calibers_compute(db_session: Session) -> None:
    """菜鸟 FY2023：核心口径（收入/毛利/净利/现金流）出数；IFRS 明细行如实保留。"""
    import yaml as yaml_lib

    cainiao_yaml = REPO_ROOT / "docs/implementation/p5/cainiao_2023fy_statements.yaml"
    payload = yaml_lib.safe_load(cainiao_yaml.read_text())
    report = import_statement_report(
        db_session,
        company_name="菜鸟集团",
        stock_code="CAINIAO",
        report_kind="年报",
        period_label="FY2023",
        payload=payload,
        source_ref="p5_samples/cainiao/cainiao_2023fy.pdf",
        source_sha256="c" * 64,
    )
    report.status = "published"
    db_session.flush()
    normalize_report(db_session, report)

    overview = build_operations_overview(db_session, report_id=str(report.id))
    by_id = {t.theme_id: t for t in overview.themes}

    profit = {m.entry_id: m for m in by_id["profit_quality"].metrics}
    gross = profit["gross_margin"]
    assert gross.status == "computed" and gross.value is not None, "毛利可算（菜鸟有毛利行）"
    net = profit["net_margin"]
    assert net.status == "computed" and net.value is not None

    growth = {m.entry_id: m for m in by_id["growth_quality"].metrics}
    revenue_yoy = growth["revenue_yoy"]
    assert revenue_yoy.status == "computed", "本期/上期两列齐备，同比可算"

    efficiency = {m.entry_id: m for m in by_id["operational_efficiency"].metrics}
    current = efficiency["current_ratio"]
    assert current.status == "computed", "流动资产/流动负债合计行齐备"

    volume = {m.entry_id: m for m in by_id["growth_quality"].metrics}[
        "international_parcels"
    ]
    assert volume.value == "1519"
    assert "FY2022" in volume.basis and "1679" in volume.basis
    assert volume.source == "operating_fact"
    assert volume.period_label == "FY2023"
    assert volume.source_page == "22" and len(volume.source_sha256) == 64

    adjusted = {m.entry_id: m for m in by_id["profit_quality"].metrics}
    assert adjusted["adjusted_ebitda"].value == "2873"
    assert adjusted["adjusted_net_profit_margin"].value == "0.004"

    structure = {m.entry_id: m for m in by_id["revenue_structure"].metrics}
    assert structure["business_line_share.international_logistics"].value == "0.474"
    assert structure["business_line_share.china_logistics"].value == "0.462"
    assert structure["business_line_share.technology_and_other_services"].value == "0.064"


def test_cainiao_historical_report_never_reads_future_segment_periods() -> None:
    """FY2023 只能读取 FY2023 与 FY2022；不得拿数据集末尾 FY2025 代替。"""
    series = yaml.safe_load(
        (REPO_ROOT / "docs/implementation/p5/cainiao_segment_series.yaml").read_text()
    )

    theme = _segment_revenue_theme(series, selected_period="FY2023")

    rendered = " ".join(
        " ".join((metric.name, metric.basis, metric.caliber_note))
        for metric in theme.metrics
    )
    assert "FY2023" in rendered and "FY2022" in rendered
    assert "FY2024" not in rendered and "FY2025" not in rendered


def test_segment_series_does_not_mix_annual_data_into_quarter() -> None:
    series = yaml.safe_load(
        (REPO_ROOT / "docs/implementation/p5/cainiao_segment_series.yaml").read_text()
    )

    theme = _segment_revenue_theme(series, selected_period="Q1FY2024")

    assert theme.status == "not_applicable"
    assert theme.reason == "segment_period_not_available"
    assert theme.metrics == []


def test_cainiao_unresolved_rows_preserved(db_session: Session) -> None:
    """IFRS 明细行（投融资活动等 80 行）无标准 item_id，如实保留不编造。"""
    import yaml as yaml_lib

    from flow_api.infrastructure.models.statement import StatementNormalizedItem

    cainiao_yaml = REPO_ROOT / "docs/implementation/p5/cainiao_2023fy_statements.yaml"
    payload = yaml_lib.safe_load(cainiao_yaml.read_text())
    report = import_statement_report(
        db_session,
        company_name="菜鸟集团",
        stock_code="CAINIAO",
        report_kind="年报",
        period_label="FY2023",
        payload=payload,
        source_ref="p5_samples/cainiao/cainiao_2023fy.pdf",
        source_sha256="c" * 64,
    )
    normalize_report(db_session, report)
    unresolved = (
        db_session.query(StatementNormalizedItem)
        .filter(
            StatementNormalizedItem.report_id == report.id,
            StatementNormalizedItem.item_id.is_(None),
        )
        .count()
    )
    assert unresolved > 50, "未解析行必须如实保留（缺失不补造）"


# ---- 阿里巴巴（9988.HK，US GAAP）样本接入——8 份年报抽取（4f4dbfb 脚本） ----


def _import_alibaba(session: Session, fy: int = 2026) -> Any:
    import yaml as yaml_lib

    alibaba_yaml = REPO_ROOT / f"docs/implementation/p5/alibaba_{fy}fy_statements.yaml"
    payload = yaml_lib.safe_load(alibaba_yaml.read_text())
    report = import_statement_report(
        session,
        company_name="阿里巴巴集团",
        stock_code="9988.HK",
        report_kind="年报",
        period_label=f"FY{fy}",
        payload=payload,
        source_ref=f"p5_samples/alibaba_9988/BABA_FY{fy}_annual_results.pdf",
        source_sha256="b" * 64,
    )
    report.status = "published"
    session.flush()
    normalize_report(session, report)
    return report


def test_alibaba_sample_core_calibers_compute(db_session: Session) -> None:
    """阿里（US GAAP）核心口径出数：收入/净利/杜邦/毛利率（fact_direct）。"""
    report = _import_alibaba(db_session, fy=2026)
    overview = build_operations_overview(db_session, report_id=str(report.id))
    by_id = {t.theme_id: t for t in overview.themes}

    profit = {m.entry_id: m for m in by_id["profit_quality"].metrics}
    net = profit["net_margin"]
    assert net.status == "computed" and net.value is not None, "US GAAP 净利率可算"
    dupont = profit["dupont_three_factor"]
    assert dupont.status == "computed" and dupont.value is not None
    assert "净利润总额口径" in dupont.name, "杜邦条目名必须携带口径标注（U2/6.3）"

    growth = {m.entry_id: m for m in by_id["growth_quality"].metrics}
    revenue_growth = growth["revenue_growth"]
    assert revenue_growth.status == "computed" and revenue_growth.value is not None, (
        "年报含本期+上期年度列，收入增长可算"
    )


def test_alibaba_revenue_structure_theme(db_session: Session) -> None:
    """阿里归一化行含收入但无分部拆分；分部系列挂菜鸟（CAINIAO）不混入阿里。"""
    report = _import_alibaba(db_session, fy=2026)
    overview = build_operations_overview(db_session, report_id=str(report.id))
    revenue_structure = {t.theme_id: t for t in overview.themes}["revenue_structure"]
    # 阿里报告不注入菜鸟分部系列：公司键隔离
    assert revenue_structure.status == "not_applicable"
    assert revenue_structure.reason == "segment_disclosure_missing"
