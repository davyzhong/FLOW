"""Task 4 slice-2a：大麦装载器分析链 DB 集成测试。

- 工作簿导入（IntakeService 全链：attach→mapping→validate→publish）；
- 12 个月指标快照（202509..202608，flow_v1_metrics 目录）；
- 最新快照的 AnalysisRun published；
- 二次 seed 幂等：batch/快照/run 身份不增长。
（Finding 状态机推进、三类冻结 receipt 与事务回滚注入在 slice-2b。）
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from integration.intake_service_support import clean
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from flow_api.fixtures.damai.loader import seed_damai_demo
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


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    for table in (
        MetricValue,
        MetricSnapshot,
        AnalysisRun,
        AnalysisBatch,
        StatementNormalizedItem,
        StatementLineItem,
        StatementReport,
    ):
        session.execute(delete(table))
    clean(session)  # canonical 事实/维度 + intake 链全清，保证从零 seed
    yield session
    session.close()
    engine.dispose()


def test_seed_builds_snapshots_and_analysis_run(db_session: Session) -> None:
    receipt = seed_damai_demo(db_session)

    analytics = receipt["analytics"]
    assert len(analytics["metric_snapshot_ids"]) == 12
    assert analytics["months"][0] == 202509
    assert analytics["months"][-1] == 202608
    assert analytics["analysis_run_status"] == "published"

    snapshot_count = db_session.execute(
        text("SELECT count(*) FROM metric_snapshot WHERE status = 'published'")
    ).scalar_one()
    assert snapshot_count == 12

    value_count = db_session.execute(
        text("SELECT count(*) FROM metric_value")
    ).scalar_one()
    assert value_count > 0, "快照必须带指标值"


def test_seed_analytics_is_idempotent(db_session: Session) -> None:
    first = seed_damai_demo(db_session)
    second = seed_damai_demo(db_session)

    assert second["analytics"]["batch_id"] == first["analytics"]["batch_id"]
    assert second["analytics"]["metric_snapshot_ids"] == (
        first["analytics"]["metric_snapshot_ids"]
    )
    assert second["analytics"]["analysis_run_id"] == first["analytics"]["analysis_run_id"]

    snapshot_rows = db_session.execute(
        text("SELECT count(*) FROM metric_snapshot WHERE status = 'published'")
    ).scalar_one()
    assert snapshot_rows == 12, "重复 seed 不得新建快照"
    run_rows = db_session.execute(
        text("SELECT count(*) FROM analysis_run WHERE status = 'published'")
    ).scalar_one()
    assert run_rows == 1, "重复 seed 不得新建 AnalysisRun"
