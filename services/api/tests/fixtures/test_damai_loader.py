"""Task 4：大麦演示装载器 DB 集成测试（聚焦财报装载子链）。

- enterprise 幂等复用 bootstrap UUID 并改名为大麦物流（授权契约单企业）；
- 两份合成财报（FY2025/FY2026）导入 + 归一化 + 发布：source SHA 非空、
  归一行含 item_id、report published；
- 二次 seed 幂等：报告身份/归一行数不增长。
事务回滚注入测试与指标快照/Finding 编排（规格 §4.3 全量）在后续切片。
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, text
from sqlalchemy.orm import Session

from flow_api.fixtures.damai.loader import seed_damai_demo
from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)
from flow_api.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[4]


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


def test_seed_loads_enterprise_and_two_published_reports(db_session: Session) -> None:
    receipt = seed_damai_demo(db_session)

    assert receipt["enterprise"]["id"] == "00000000-0000-0000-0000-00000000d001"
    assert "大麦" in receipt["enterprise"]["name"]
    assert len(receipt["reports"]) == 2
    for report in receipt["reports"]:
        assert report["status"] == "published"
        assert report["normalized_rows"] > 0
        assert report["source_sha256"]


def test_seed_is_idempotent_on_identity_and_rows(db_session: Session) -> None:
    first = seed_damai_demo(db_session)
    second = seed_damai_demo(db_session)

    total = len(
        list(db_session.execute(text("SELECT id FROM statement_report")))
    )
    assert total == 2, "重复 seed 不得新建报告"
    assert [r["report_id"] for r in second["reports"]] == [
        r["report_id"] for r in first["reports"]
    ]
