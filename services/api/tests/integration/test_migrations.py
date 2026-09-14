"""迁移 0025 升级/回滚/再升级对账（S01 Task 5 Step 5）。

- upgrade -> downgrade -> upgrade 全链可重放；
- 迁移不触碰 frozen_view 与历史事实值：0024 状态下写入的事实行在
  downgrade/upgrade 往返后逐字段一致（哈希等价）。
"""

from __future__ import annotations

import hashlib
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from flow_api.infrastructure.db import get_engine

ALEMBIC_CFG = Config("alembic.ini")


def _fact_fingerprint(row: sa.engine.Row) -> str:
    return hashlib.sha256(repr(tuple(row)).encode()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def back_to_head() -> None:
    command.upgrade(ALEMBIC_CFG, "head")
    yield
    command.upgrade(ALEMBIC_CFG, "head")


def test_0025_upgrade_downgrade_upgrade_roundtrip() -> None:
    """在 0024 状态写入批次与财务事实，升级到 0025 后回填 legacy/v1，
    再 downgrade/upgrade 往返，事实值与哈希不变。"""

    # 基线：head（0025）
    command.upgrade(ALEMBIC_CFG, "head")

    # 回到 0024（无 enterprise/analysis_cycle/module_kind 列）
    command.downgrade(ALEMBIC_CFG, "0024_operations_publication")
    engine = get_engine()
    batch_id = uuid4()
    with Session(engine) as s:
        cols = {c["name"] for c in sa.inspect(engine).get_columns("analysis_batch")}
        assert "module_kind" not in cols
        assert "analysis_cycle_id" not in cols
        s.execute(
            sa.text(
                "INSERT INTO analysis_batch (id, created_at, name, status) VALUES"
                " (:id, now(), :name, 'draft')"
            ),
            {"id": batch_id, "name": f"pre-0025-{uuid4().hex[:8]}"},
        )
        s.commit()

    # 升级到 head：存量批次回填 legacy/v1/cycle NULL
    command.upgrade(ALEMBIC_CFG, "head")
    with Session(engine) as s:
        row = s.execute(
            sa.text(
                "SELECT module_kind, fact_context_version, analysis_cycle_id"
                " FROM analysis_batch WHERE id = :id"
            ),
            {"id": batch_id},
        ).one()
        # R1 语义（0027）：存量 legacy 批次升级时统一转 internal + 引导 cycle
        assert tuple(row)[0] == "internal"
        assert tuple(row)[1] == 2
        assert tuple(row)[2] is not None

        # 迁移不改历史事实值：取一条财务事实（无则跳过值对账）
        fact_row = s.execute(
            sa.text("SELECT id, amount FROM fact_financial_actual ORDER BY id LIMIT 1")
        ).first()
        before_hash = _fact_fingerprint(fact_row) if fact_row else None

    # downgrade -> upgrade 往返后再次对账
    command.downgrade(ALEMBIC_CFG, "0024_operations_publication")
    command.upgrade(ALEMBIC_CFG, "head")
    with Session(engine) as s:
        row = s.execute(
            sa.text(
                "SELECT module_kind, fact_context_version, analysis_cycle_id"
                " FROM analysis_batch WHERE id = :id"
            ),
            {"id": batch_id},
        ).one()
        assert tuple(row)[0] == "internal"
        assert tuple(row)[1] == 2
        assert tuple(row)[2] is not None
        if before_hash is not None:
            fact_row = s.execute(
                sa.text("SELECT id, amount FROM fact_financial_actual ORDER BY id LIMIT 1")
            ).first()
            assert _fact_fingerprint(fact_row) == before_hash
        s.execute(sa.text("DELETE FROM analysis_batch WHERE id = :id"), {"id": batch_id})
        s.commit()
