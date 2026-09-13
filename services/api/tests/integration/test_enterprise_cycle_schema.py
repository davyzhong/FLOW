"""企业空间与月度分析周期 schema 测试（S01 Task 5，TDD 红灯先行）。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）§4 合法组合矩阵。
- enterprise code 唯一；
- analysis_cycle 在 (enterprise_id, period_key) 唯一；
- analysis_batch 持久化 module_kind / fact_context_version / analysis_cycle_id；
- 合法组合仅 legacy/1/cycle NULL、public/1|2/cycle NULL、internal/2/cycle NOT NULL，
  其余由单一 CHECK 拒绝（ORM 与直接 SQL 双重验证）；
- 内部创建服务重复校验。
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from flow_api.enterprise.models import (
    AnalysisCycle,
    Enterprise,
    assert_legal_batch_combination,
    new_analysis_batch,
)
from flow_api.financial_facts_v2.models import ContractV2Violation
from flow_api.infrastructure.db import get_engine
from flow_api.infrastructure.models.intake import AnalysisBatch


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def session() -> Session:
    with Session(get_engine(), expire_on_commit=False) as database_session:
        yield database_session
        database_session.rollback()
        for model in (AnalysisBatch, AnalysisCycle, Enterprise):
            database_session.execute(delete(model))
        database_session.commit()


@pytest.fixture
def enterprise(session: Session) -> Enterprise:
    ent = Enterprise(code=f"ENT-{uuid4().hex[:8]}", name="某物流企业")
    session.add(ent)
    session.flush()
    return ent


@pytest.fixture
def cycle(session: Session, enterprise: Enterprise) -> AnalysisCycle:
    cyc = AnalysisCycle(enterprise_id=enterprise.id, period_key="2026-01")
    session.add(cyc)
    session.flush()
    return cyc


# --- enterprise / cycle 唯一性 ---

def test_enterprise_code_unique(session: Session, enterprise: Enterprise) -> None:
    session.add(Enterprise(code=enterprise.code, name="重名企业"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_cycle_unique_per_enterprise_period(
    session: Session, enterprise: Enterprise, cycle: AnalysisCycle
) -> None:
    session.add(AnalysisCycle(enterprise_id=enterprise.id, period_key=cycle.period_key))
    with pytest.raises(IntegrityError):
        session.flush()


def test_cycle_same_period_allowed_across_enterprises(
    session: Session, cycle: AnalysisCycle
) -> None:
    other = Enterprise(code=f"ENT-{uuid4().hex[:8]}", name="另一企业")
    session.add(other)
    session.flush()
    session.add(AnalysisCycle(enterprise_id=other.id, period_key=cycle.period_key))
    session.flush()


def test_cycle_period_key_format_enforced(session: Session, enterprise: Enterprise) -> None:
    session.add(AnalysisCycle(enterprise_id=enterprise.id, period_key="2026-13"))
    with pytest.raises(IntegrityError):
        session.flush()


# --- 批次合法组合矩阵（ORM 层） ---

def test_legacy_batch_default_backfill(session: Session) -> None:
    """迁移前语义：不显式给出时回填 legacy/v1 且 cycle 为空。"""
    batch = AnalysisBatch(name=f"B-{uuid4().hex[:8]}")
    session.add(batch)
    session.flush()
    assert batch.module_kind == "legacy"
    assert batch.fact_context_version == 1
    assert batch.analysis_cycle_id is None


def test_public_batch_v1_v2_ok(session: Session) -> None:
    for version in (1, 2):
        session.add(
            AnalysisBatch(
                name=f"B-{uuid4().hex[:8]}",
                module_kind="public",
                fact_context_version=version,
            )
        )
    session.flush()


def test_internal_batch_v2_with_cycle_ok(session: Session, cycle: AnalysisCycle) -> None:
    session.add(
        AnalysisBatch(
            name=f"B-{uuid4().hex[:8]}",
            module_kind="internal",
            fact_context_version=2,
            analysis_cycle_id=cycle.id,
        )
    )
    session.flush()


@pytest.mark.parametrize(
    "module_kind,version,with_cycle",
    [
        ("internal", 1, True),   # internal/1 非法
        ("internal", 1, False),
        ("internal", 2, False),  # internal/2 缺 cycle 非法
        ("legacy", 2, False),    # legacy/2 非法
        ("legacy", 1, True),     # legacy 带 cycle 非法
        ("public", 1, True),     # public 带 cycle 非法
        ("public", 2, True),
        ("internal", 3, True),   # 未知版本
        ("unknown", 1, False),   # 未知 module_kind
    ],
)
def test_illegal_combinations_rejected_by_check(
    session: Session, cycle: AnalysisCycle, module_kind: str, version: int, with_cycle: bool
) -> None:
    session.add(
        AnalysisBatch(
            name=f"B-{uuid4().hex[:8]}",
            module_kind=module_kind,
            fact_context_version=version,
            analysis_cycle_id=cycle.id if with_cycle else None,
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


# --- 直接 SQL 绕过 ORM 也被单一 CHECK 拒绝 ---

@pytest.mark.parametrize(
    "module_kind,version,cycle_sql",
    [
        ("internal", 1, "NULL"),
        ("internal", 2, "NULL"),
        ("legacy", 2, "NULL"),
    ],
)
def test_illegal_combinations_rejected_by_raw_sql(
    session: Session, module_kind: str, version: int, cycle_sql: str
) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            sa.text(
                "INSERT INTO analysis_batch (id, created_at, name, status, module_kind,"
                " fact_context_version, analysis_cycle_id) VALUES"
                f" ('{uuid4()}', now(), 'raw-sql-probe', 'draft', :mk, :v, {cycle_sql})"
            ),
            {"mk": module_kind, "v": version},
        )
        session.flush()


# --- 内部创建服务重复校验 ---

def test_service_double_check_rejects_internal_without_cycle() -> None:
    with pytest.raises(ContractV2Violation):
        new_analysis_batch(
            name="x", module_kind="internal", fact_context_version=2, analysis_cycle_id=None
        )


def test_service_double_check_rejects_legacy_v2() -> None:
    with pytest.raises(ContractV2Violation):
        assert_legal_batch_combination("legacy", 2, None)


def test_service_creates_legal_internal_batch(cycle: AnalysisCycle) -> None:
    batch = new_analysis_batch(
        name="x",
        module_kind="internal",
        fact_context_version=2,
        analysis_cycle_id=cycle.id,
    )
    assert batch.module_kind == "internal"
    assert batch.analysis_cycle_id == cycle.id
