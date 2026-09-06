"""规范化、取数映射与修订版本（B03）测试。

- 原始值可还原：归一化不改动 statement_line_item 原始行；
- 重复导入幂等：同身份同内容报表 id 不变；同身份不同内容（重述）递增版本、旧版保留；
- 归一化幂等与修订分离：同一映射版本重建一致，新映射版本并存可查询；
- 组合映射生成合成行并留痕；未映射行如实保留。
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import (
    load_alias_map,
    normalize_report,
    normalized_items,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SF_YAML = REPO_ROOT / "docs/implementation/p5/sf_2026q1_statements.yaml"

IMPORT_KWARGS = {
    "company_name": "顺丰控股",
    "stock_code": "002352.SZ",
    "report_kind": "一季报",
    "period_label": "2026Q1",
}


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


def _import_sf(session: Session) -> StatementReport:
    payload = yaml.safe_load(SF_YAML.read_text())
    return import_statement_report(
        session,
        **IMPORT_KWARGS,
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="a" * 64,
    )


def test_reimport_is_idempotent_and_restatement_versions(db_session: Session) -> None:
    first = _import_sf(db_session)
    assert first.version == 1
    first_id = first.id
    first_items = len(first.items)

    again = _import_sf(db_session)
    assert again.id == first_id
    assert again.version == 1
    assert len(again.items) == first_items

    payload = yaml.safe_load(SF_YAML.read_text())
    payload["statements"]["合并资产负债表"][0]["期末余额"] = 12345
    restated = import_statement_report(
        db_session,
        **IMPORT_KWARGS,
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="b" * 64,
    )
    assert restated.id != first_id
    assert restated.version == 2
    original = db_session.get(StatementReport, first_id)
    assert original is not None and len(original.items) == first_items
    versions = db_session.scalars(
        select(StatementReport.version).where(
            StatementReport.stock_code == "002352.SZ",
            StatementReport.period_label == "2026Q1",
        )
    ).all()
    assert sorted(versions) == [1, 2]


def test_normalize_resolves_sums_traces_and_preserves_original(db_session: Session) -> None:
    report = _import_sf(db_session)
    alias_map = load_alias_map(REPO_ROOT / "config/statements/item_alias_map_v0.yaml")
    original_rows = [
        (i.statement_type, i.item_name, i.value_end, i.value_current) for i in report.items
    ]

    summary = normalize_report(db_session, report, alias_map=alias_map)
    assert summary.resolved > 0
    assert summary.synthetic >= 1

    rows = normalized_items(db_session, report.id, mapping_version="v0")
    by_id = {row.item_id: row for row in rows if row.item_id}
    assert by_id["bs.total_assets"].value_end == Decimal("213797231.0000")
    assert by_id["is.revenue"].value_current == Decimal("74142121.0000")

    synthetic = next(row for row in rows if row.item_id == "bs.short_debt")
    assert synthetic.trace["kind"] == "sum"
    assert set(synthetic.trace["parts"]) == {"一年内到期的非流动负债", "短期借款"}

    after = [
        (i.statement_type, i.item_name, i.value_end, i.value_current) for i in report.items
    ]
    assert after == original_rows, "归一化不得改动原始行"


def test_normalize_idempotent_and_mapping_versions_coexist(db_session: Session) -> None:
    report = _import_sf(db_session)
    first = normalize_report(db_session, report)
    count_v0 = db_session.scalar(select(func.count()).select_from(StatementNormalizedItem))

    second = normalize_report(db_session, report)
    assert (second.resolved, second.unresolved, second.synthetic) == (
        first.resolved,
        first.unresolved,
        first.synthetic,
    )
    assert db_session.scalar(select(func.count()).select_from(StatementNormalizedItem)) == count_v0

    normalize_report(db_session, report, mapping_version="v0-test-2")
    total = db_session.scalar(select(func.count()).select_from(StatementNormalizedItem))
    assert total == 2 * count_v0
    assert len(normalized_items(db_session, report.id, mapping_version="v0")) == count_v0
    assert len(normalized_items(db_session, report.id, mapping_version="v0-test-2")) == count_v0


def test_unmapped_company_items_kept_unresolved(db_session: Session) -> None:
    payload = {
        "unit": "人民币元",
        "statements": {
            "合并资产负债表": [
                {"item": "货币资金", "期末余额": 100, "期初余额": 90},
                {"item": "某未收录科目", "期末余额": 5, "期初余额": 4},
            ]
        },
    }
    report = import_statement_report(
        db_session,
        company_name="圆通速递",
        stock_code="600233",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/yto_600233/YTO_2026_Q1_report.pdf",
    )
    summary = normalize_report(db_session, report)
    assert summary.resolved == 0
    assert summary.unresolved == 2
    assert set(summary.unresolved_items) == {"货币资金", "某未收录科目"}
