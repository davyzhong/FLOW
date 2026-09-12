"""指标库治理（C04）测试：草稿/验证/生效/退役 + 可靠审计。

- 草稿从在效定义派生新版本，不触碰在效定义；并发草稿 typed 拒绝；
- 非法 AST / 循环依赖 / 引用缺失阻止生效；
- 生效自动退役旧版，旧定义与旧快照不变；
- 每次动作留审计事件（操作者/理由/差异可查询）。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.metric_library import (
    AccountingStandard,
    AccountingSubject,
    EntryTemplate,
    MetricCatalogDocument,
    MetricDictionaryEntry,
    MetricGovernanceEvent,
    StatementLineMapping,
)
from flow_api.metric_library_store.governance import GovernanceError, MetricGovernance
from flow_api.metric_library_store.importer import import_metric_dictionary, resolve_dictionary_file
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]
DICT_YAML = resolve_dictionary_file(REPO_ROOT / "config/metrics")


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


def test_draft_activate_retire_lifecycle_with_audit(session: Session) -> None:
    gov = MetricGovernance(session)
    base = _effective(session, "current_ratio")
    original_formula = base.formula

    draft = gov.draft_change(
        base.id,
        changes={"benchmark": "经验参考约 2.2"},
        operator="钟Davy",
        reason="基准口径校准",
    )
    assert draft.version == base.version + 1
    assert draft.status == "draft"
    assert _effective(session, "current_ratio").id == base.id, "草稿期在效定义不变"

    activated = gov.activate(draft.id, operator="钟Davy", reason="评审通过")
    assert activated.status == "effective"
    assert _effective(session, "current_ratio").id == draft.id
    old = session.get(MetricDictionaryEntry, base.id)
    assert old is not None and old.status == "retired"
    assert old.formula == original_formula, "旧定义内容不变"

    events = gov.events("current_ratio")
    assert [e.action for e in events] == ["draft", "retire", "activate"]
    assert all(e.operator == "钟Davy" for e in events)
    assert events[0].diff == {"benchmark": "经验参考约 2.2"}

    retired = gov.retire(draft.id, operator="钟Davy", reason="演示退役")
    assert retired.status == "retired"


def test_concurrent_draft_rejected(session: Session) -> None:
    gov = MetricGovernance(session)
    base = _effective(session, "quick_ratio")
    gov.draft_change(base.id, changes={"benchmark": "x"}, operator="a", reason="r")
    with pytest.raises(GovernanceError) as exc:
        gov.draft_change(base.id, changes={"benchmark": "y"}, operator="b", reason="r")
    assert exc.value.code == "draft_conflict"


def test_illegal_ast_and_missing_reference_blocked(session: Session) -> None:
    gov = MetricGovernance(session)
    base = _effective(session, "gross_margin")

    bad_ops = gov.draft_change(
        base.id,
        changes={"formula": {"op": "median", "args": ["bs.total_assets"]}},
        operator="a",
        reason="r",
    )
    with pytest.raises(GovernanceError) as exc:
        gov.activate(bad_ops.id, operator="a", reason="r")
    assert exc.value.code == "invalid_formula_ast"
    gov.retire(bad_ops.id, operator="a", reason="废弃非法草稿")

    missing_ref = gov.draft_change(
        base.id,
        changes={"formula": {"op": "div", "args": ["bs.total_assets", "bs.not_registered"]}},
        operator="a",
        reason="r",
    )
    with pytest.raises(GovernanceError) as exc:
        gov.activate(missing_ref.id, operator="a", reason="r")
    assert exc.value.code == "missing_reference"
    assert _effective(session, "gross_margin").id == base.id, "被阻断的草稿不影响在效定义"


def test_circular_dependency_blocked(session: Session) -> None:
    gov = MetricGovernance(session)
    # current_ratio 公式引用报表项目；构造 current_ratio → quick_ratio → current_ratio 环
    base_a = _effective(session, "current_ratio")
    base_b = _effective(session, "quick_ratio")

    draft_b = gov.draft_change(
        base_b.id,
        changes={"formula": {"op": "identity", "args": ["current_ratio"]}},
        operator="a",
        reason="r",
    )
    gov.activate(draft_b.id, operator="a", reason="r")

    draft_a = gov.draft_change(
        base_a.id,
        changes={"formula": {"op": "identity", "args": ["quick_ratio"]}},
        operator="a",
        reason="r",
    )
    with pytest.raises(GovernanceError) as exc:
        gov.activate(draft_a.id, operator="a", reason="r")
    assert exc.value.code == "circular_dependency"


def test_draft_from_non_effective_rejected(session: Session) -> None:
    gov = MetricGovernance(session)
    base = _effective(session, "debt_asset_ratio")
    draft = gov.draft_change(base.id, changes={"benchmark": "x"}, operator="a", reason="r")
    with pytest.raises(GovernanceError) as exc:
        gov.draft_change(draft.id, changes={"benchmark": "y"}, operator="a", reason="r")
    assert exc.value.code == "invalid_base"
