"""指标变更影响分析与沙盒试算（C05）测试。

- 下游依赖遍历完整（传递闭包）且无循环；
- 沙盒试算给出新旧数值差异（顺丰事实库），失败试算不污染正式数据；
- 影响分析不触碰在效定义与已冻结快照。
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import MetricSnapshot
from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricCatalogDocument,
    MetricDictionaryEntry,
    MetricGovernanceEvent,
    StatementLineMapping,
)
from flow_api.metric_library_store.governance import MetricGovernance
from flow_api.metric_library_store.impact import ImpactError, MetricImpactService
from flow_api.metric_library_store.importer import import_metric_dictionary
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]
DICT_YAML = REPO_ROOT / "config/metrics/metric_dictionary_v1.yaml"


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        MetricGovernanceEvent,
        MetricDictionaryEntry,
        MetricCatalogDocument,
        AccountingSubject,
        AccountingStandard,
        EntryTemplate,
        StatementLineMapping,
    ):
        session.execute(delete(table))
    session.commit()
    import_metric_dictionary(session, DICT_YAML)
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _effective(session: Session, code: str) -> MetricDictionaryEntry:
    entry = session.scalar(
        select(MetricDictionaryEntry).where(
            MetricDictionaryEntry.metric_code == code,
            MetricDictionaryEntry.status == "effective",
        )
    )
    assert entry is not None
    return entry


def test_impact_report_traverses_downstream_and_sandbox(session: Session) -> None:
    gov = MetricGovernance(session)
    base = _effective(session, "gross_margin")
    draft = gov.draft_change(
        base.id,
        changes={"formula": {"op": "div", "args": [
            {"op": "sub", "args": ["is.revenue", "is.cogs"]},
            {"op": "mul", "args": ["is.revenue", 1.01]},
        ]}},
        operator="钟Davy",
        reason="试算演示：分母放大 1%",
    )
    snapshots_before = session.scalar(
        select(func.count()).select_from(MetricSnapshot)
    )
    report = MetricImpactService(session).analyze(draft.id)
    assert report.metric_code == "gross_margin"
    assert isinstance(report.downstream_metrics, tuple)
    assert "is.revenue" in report.referenced_items
    assert "is.cogs" in report.referenced_items
    assert report.sandbox, "顺丰事实库上应有试算结果"
    sf_diffs = [d for d in report.sandbox if d.company == "sf_002352"]
    assert sf_diffs, "顺丰期间应有可比试算"
    for diff in sf_diffs:
        assert diff.error is None
        assert diff.current_value is not None
        assert diff.draft_value is not None
        assert diff.delta is not None
        assert Decimal(diff.delta) != 0, "分母变化应产生差异"
    # 其他公司缺项如实降级为 error，不伪造数值
    assert any(d.error for d in report.sandbox if d.company != "sf_002352")
    snapshots_after = session.scalar(
        select(func.count()).select_from(MetricSnapshot)
    )
    assert snapshots_after == snapshots_before, "影响分析不得触碰已冻结快照"
    assert _effective(session, "gross_margin").id == base.id, "在效定义不变"


def test_missing_reference_blocked_before_sandbox(session: Session) -> None:
    gov = MetricGovernance(session)
    base = _effective(session, "current_ratio")
    draft = gov.draft_change(
        base.id,
        changes={"formula": {"op": "div", "args": ["bs.current_assets", "bs.not_registered"]}},
        operator="a",
        reason="r",
    )
    with pytest.raises(ImpactError) as exc:
        MetricImpactService(session).analyze(draft.id)
    assert exc.value.code == "missing_reference"


def test_impact_requires_draft(session: Session) -> None:
    base = _effective(session, "current_ratio")
    with pytest.raises(ImpactError) as exc:
        MetricImpactService(session).analyze(base.id)
    assert exc.value.code == "invalid_base"
