"""U3/P04 第一切片：主题快照投影契约测试（TDD 先行）。

契约：
- 投影 = 同一快照身份（report_id + mapping_version）下的预计算条目值 +
  每条目的来源定位（item_id → 归一化行 → 原件 SHA）+ 口径版本；前端只格式化；
- 跨身份拼接被拒绝：比较基线等补充行若来自其他 report/version，
  抛 typed 错误 snapshot_identity_mismatch；
- 投影不可变：构建后修改源归一化行，已构建投影的值不变（D02：旧分析不变）。
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
from flow_api.settings import get_settings
from flow_api.statements.importer import import_statement_report
from flow_api.statements.normalization import normalize_report
from flow_api.statements.projection import (
    ProjectionError,
    SnapshotIdentity,
    build_topic_projection,
)

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


def _import_sf(db_session: Session) -> Any:
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
    return report


def _import_sf_foreign_copy(db_session: Session) -> Any:
    """另一份独立导入的 SF 报告（不同期间标签 → 不同 report_id），作外来身份。

    不用 JDL：其归一化撞 uq_statement_normalized_item（U2/6.1 已登记的契约缺陷，
    待唯一键契约决策），与本切片无关。
    """

    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        db_session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2025Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256="c" * 64,
    )
    db_session.flush()
    return report


def test_projection_carries_identity_values_and_provenance(db_session: Session) -> None:
    report = _import_sf(db_session)
    normalize_report(db_session, report)
    identity = SnapshotIdentity(report_id=str(report.id), mapping_version="v1")

    projection = build_topic_projection(db_session, identity)
    assert projection.identity == identity
    assert projection.catalog_id  # 来自客观分析目录

    computed = [e for e in projection.entries if e.status == "computed"]
    assert computed, "顺丰归一化后应有可计算条目"
    # 来源定位：条目 provenance 指向归一化行与原件哈希
    sample = next(e for e in computed if e.provenance)
    point = sample.provenance[0]
    assert point.item_id and point.statement_type
    assert point.source_sha256 == "a" * 64
    # 预计算值为精确十进制字符串（前端只格式化不重算）
    assert sample.value is None or isinstance(sample.value, str)


def test_cross_identity_rows_are_rejected(db_session: Session) -> None:
    sf = _import_sf(db_session)
    normalize_report(db_session, sf)
    foreign_report = _import_sf_foreign_copy(db_session)  # 外来身份的归一化行

    from flow_api.infrastructure.models.statement import StatementNormalizedItem

    normalize_report(db_session, foreign_report)
    foreign = (
        db_session.query(StatementNormalizedItem)
        .filter(StatementNormalizedItem.report_id == foreign_report.id)
        .all()
    )
    assert foreign, "外来报告的归一化行应存在"

    identity = SnapshotIdentity(report_id=str(sf.id), mapping_version="v1")
    with pytest.raises(ProjectionError) as excinfo:
        build_topic_projection(db_session, identity, baseline_rows=foreign)
    assert excinfo.value.code == "snapshot_identity_mismatch"


def test_projection_is_immutable_after_source_change(db_session: Session) -> None:
    report = _import_sf(db_session)
    normalize_report(db_session, report)
    identity = SnapshotIdentity(report_id=str(report.id), mapping_version="v1")

    projection = build_topic_projection(db_session, identity)
    before = {e.entry_id: e.value for e in projection.entries}

    # 修改源归一化行（模拟修正）——已构建投影不得变化
    from flow_api.infrastructure.models.statement import StatementNormalizedItem

    row = db_session.query(StatementNormalizedItem).filter(
        StatementNormalizedItem.report_id == report.id,
        StatementNormalizedItem.item_id == "is.revenue",
    ).first()
    row.value_current = 1
    db_session.flush()

    after = {e.entry_id: e.value for e in projection.entries}
    assert after == before, "旧投影必须不受源行后续修改影响"
