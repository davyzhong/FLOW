"""Task B1：大麦 seed 事务化与幂等化契约测试（红灯先行）。

- seed 起点先过数据包不变量门禁（validate_damai_package invalid → 拒绝落库）；
- AnalysisBatch 显式绑定截止月 2026-08 的 AnalysisCycle，不依赖「全库最早周期」；
- 装载器只在顶层提交：三类故障注入（不变量 / 第二份财报发布 / 工作簿 publish）
  均断言回滚后零部分数据；
- 二次 seed 全对象计数不增长（batch/source/snapshot/run/report/normalized）。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from integration.intake_service_support import clean
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from flow_api.fixtures.damai import loader as damai_loader
from flow_api.infrastructure.models.analytics import (
    AnalysisRun,
    MetricSnapshot,
    MetricValue,
)
from flow_api.infrastructure.models.intake import AnalysisBatch
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings
from flow_api.statements.review import ReviewService

REPO_ROOT = Path(__file__).resolve().parents[4]

_COUNT_TABLES = (
    "statement_normalized_item",
    "statement_line_item",
    "statement_report",
    "metric_value",
    "metric_snapshot",
    "analysis_run",
    "import_version",
    "source_file",
    "stored_object",
    "analysis_batch",
)


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    clean(session)  # canonical 事实/维度 + intake 链全清（须先于 batch 删除，FK RESTRICT）
    for table in (
        MetricValue,
        AnalysisRun,
        MetricSnapshot,
        AnalysisBatch,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    session.commit()
    yield session
    session.close()
    engine.dispose()


def _counts(session: Session) -> dict[str, int]:
    return {
        table: session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in _COUNT_TABLES
    }


def test_seed_binds_batch_to_2026_08_analysis_cycle(db_session: Session) -> None:
    receipt = damai_loader.seed_damai_demo(db_session)
    db_session.commit()

    row = db_session.execute(
        text(
            "SELECT c.period_key, c.status FROM analysis_batch b"
            " JOIN analysis_cycle c ON c.id = b.analysis_cycle_id"
            " WHERE b.id = :bid"
        ),
        {"bid": receipt["analytics"]["batch_id"]},
    ).one()
    assert row.period_key == "2026-08", (
        "大麦批次必须绑定截止月 2026-08 的 AnalysisCycle（不得依赖全库最早周期）"
    )
    assert row.status in ("open", "frozen", "closed")


def test_seed_rejects_invalid_package_before_any_write(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """不变量注入：数据包门禁 invalid 时 seed 必须拒写任何对象。"""

    monkeypatch.setattr(
        damai_loader,
        "validate_damai_package",
        lambda package: {"valid": False, "invariant_codes": ["injected_failure"]},
    )
    with pytest.raises(RuntimeError, match="injected_failure"):
        damai_loader.seed_damai_demo(db_session)
    db_session.rollback()
    assert set(_counts(db_session).values()) == {0}, "不变量失败不得留部分数据"


def test_seed_rolls_back_when_second_statement_publish_fails(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """第二份财报发布失败：第一份财报也不得残留（顶层提交语义）。"""

    calls = {"count": 0}
    original_publish = ReviewService.publish

    def fail_on_second(self: ReviewService, report_id, *, operator: str):  # noqa: ANN001
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("injected_second_statement_failure")
        return original_publish(self, report_id, operator=operator)

    monkeypatch.setattr(ReviewService, "publish", fail_on_second)
    with pytest.raises(RuntimeError, match="injected_second_statement_failure"):
        damai_loader.seed_damai_demo(db_session)
    db_session.rollback()
    assert set(_counts(db_session).values()) == {0}, "发布失败不得留部分数据"


def test_seed_rolls_back_when_intake_publish_fails(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """工作簿 publish 注入失败：batch/source/财报一律不得残留。"""

    from flow_api.intake.service import IntakeService

    def fail_publish(self: IntakeService, version_id):  # noqa: ANN001
        raise RuntimeError("injected_intake_publish_failure")

    monkeypatch.setattr(IntakeService, "publish_import", fail_publish)
    with pytest.raises(RuntimeError, match="injected_intake_publish_failure"):
        damai_loader.seed_damai_demo(db_session)
    db_session.rollback()
    assert set(_counts(db_session).values()) == {0}, "导入失败不得留部分数据"


def test_second_seed_does_not_grow_any_object_counts(db_session: Session) -> None:
    damai_loader.seed_damai_demo(db_session)
    db_session.commit()
    first = _counts(db_session)
    assert first["statement_report"] == 2
    assert first["analysis_batch"] == 1
    assert first["metric_snapshot"] == 12
    assert first["analysis_run"] == 1
    assert first["source_file"] == 1
    assert first["stored_object"] == 1

    damai_loader.seed_damai_demo(db_session)
    db_session.commit()
    second = _counts(db_session)
    assert second == first, f"二次 seed 计数必须零增长：{first} → {second}"
