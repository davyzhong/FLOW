"""U5/P06：客观报告资格合同测试（与主观 Finding 证据审批分离）。

契约：
- 客观报告冻结必须满足独立资格合同：财报已发布（用户批准的事实发布动作）、
  来源指纹完整、归一化行存在；缺一即拒绝且 typed 原因可解释；
- 未解析行不阻断冻结，但必须在载荷的 eligibility 节如实说明（缺失不补造）；
- 主观链旧门禁不放松：无 approved finding 的旧报告冻结依旧拒绝；
- 纯客观报告无任何 Finding 也能在事实发布后进入冻结（两条链互不绑架）。
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

from flow_api.infrastructure.models.publishing import ReportSnapshot
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.publishing.objective_freeze import (
    ObjectiveFreezeError,
    freeze_objective_statement_report,
)
from flow_api.publishing.service import freeze_report_snapshot
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
    for table in (
        ReportSnapshot,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _import_sf(
    session: Session, *, status: str = "draft", source_sha256: str | None = "a" * 64
) -> Any:
    payload: dict[str, Any] = yaml.safe_load(SF_YAML.read_text())
    report = import_statement_report(
        session,
        company_name="顺丰控股",
        stock_code="002352.SZ",
        report_kind="一季报",
        period_label="2026Q1",
        payload=payload,
        source_ref="p5_samples/sf_002352/SF_2026_Q1_report.pdf",
        source_sha256=source_sha256,
    )
    report.status = status
    session.flush()
    return report


def _normalize(session: Session, report: Any) -> None:
    normalize_report(session, report)
    session.flush()


def test_draft_report_cannot_freeze_publishing_unblocks(db_session: Session) -> None:
    """批准语义：draft（未发布=未批准）拒绝；发布后（用户批准的事实动作）可冻结。"""
    report = _import_sf(db_session, status="draft")
    _normalize(db_session, report)
    with pytest.raises(ObjectiveFreezeError) as error:
        freeze_objective_statement_report(db_session, report_id=report.id)
    assert error.value.code == "report_not_published"

    report.status = "published"
    db_session.flush()
    snapshot = freeze_objective_statement_report(db_session, report_id=report.id)
    assert snapshot.payload["source"]["company_name"] == "顺丰控股"


def test_freeze_requires_complete_source_fingerprint(db_session: Session) -> None:
    report = _import_sf(db_session, status="published", source_sha256=None)
    _normalize(db_session, report)
    with pytest.raises(ObjectiveFreezeError) as error:
        freeze_objective_statement_report(db_session, report_id=report.id)
    assert error.value.code == "source_incomplete"


def test_freeze_requires_normalized_rows(db_session: Session) -> None:
    report = _import_sf(db_session, status="published")
    # 不执行归一化 → 无归一化行
    with pytest.raises(ObjectiveFreezeError) as error:
        freeze_objective_statement_report(db_session, report_id=report.id)
    assert error.value.code == "objective_report_empty"


def test_payload_carries_unavailable_notes_for_unresolved_rows(
    db_session: Session,
) -> None:
    """未解析行不阻断冻结，但 eligibility 节必须如实说明（缺失不补造）。"""
    report = _import_sf(db_session, status="published")
    _normalize(db_session, report)
    snapshot = freeze_objective_statement_report(db_session, report_id=report.id)
    eligibility = snapshot.payload["eligibility"]
    assert eligibility["published"] is True
    assert isinstance(eligibility["unresolved_count"], int)
    assert isinstance(eligibility["unavailable_notes"], list)
    assert eligibility["statement_types"] == sorted(eligibility["statement_types"])


def test_legacy_subjective_gate_not_relaxed(db_session: Session) -> None:
    """旧主观链回归：无 approved finding 的旧报告冻结依旧拒绝，不因客观链放松。"""
    import uuid as uuid_module

    with pytest.raises(Exception) as error:
        freeze_report_snapshot(
            db_session, metric_snapshot_id=uuid_module.UUID(int=0)
        )
    assert "published metric snapshot" in str(error.value)
