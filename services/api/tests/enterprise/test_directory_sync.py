from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from flow_api.enterprise.models import Enterprise
from flow_api.infrastructure.models.enterprise_directory import (
    EnterpriseMember,
    EnterpriseOrgUnit,
    EnterprisePosition,
)
from flow_api.security.models import RoleBinding


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> None:
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def db_session():
    from flow_api.settings import get_settings

    engine = create_engine(get_settings().database_url)
    session = Session(engine, expire_on_commit=False)
    enterprise = session.scalar(select(Enterprise).where(Enterprise.code == "damai-logistics"))
    if enterprise is None:
        enterprise = Enterprise(id=uuid4(), code="damai-logistics", name="组织同步测试")
        session.add(enterprise)
        session.commit()
    enterprise_id = enterprise.id
    yield session, enterprise_id
    session.rollback()
    session.close()
    engine.dispose()


def test_sync_directory_is_idempotent_and_scoped(db_session) -> None:
    from flow_api.enterprise.directory import sync_enterprise_directory

    session, enterprise_id = db_session
    package = (
        Path(__file__).resolve().parents[4] / "data/enterprise/damai-logistics/v1/organization"
    )
    first = sync_enterprise_directory(session, enterprise_id, package)
    session.flush()
    second = sync_enterprise_directory(session, enterprise_id, package)
    session.flush()

    assert first == second
    assert (
        session.scalar(
            select(func.count())
            .select_from(EnterpriseOrgUnit)
            .where(EnterpriseOrgUnit.enterprise_id == enterprise_id)
        )
        == 8
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(EnterprisePosition)
            .where(EnterprisePosition.enterprise_id == enterprise_id)
        )
        == 8
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(EnterpriseMember)
            .where(EnterpriseMember.enterprise_id == enterprise_id)
        )
        == 8
    )
    expected_actors = {
        f"damai-logistics:{kind}:{suffix}"
        for kind, suffix in (
            ("usr", "gm-001"),
            ("usr", "fin-001"),
            ("usr", "fin-002"),
            ("usr", "analyst-001"),
            ("usr", "rule-001"),
            ("ai", "analyst-001"),
            ("ai", "cfo-001"),
            ("svc", "ingest-001"),
        )
    }
    bindings = session.scalars(
        select(RoleBinding).where(
            RoleBinding.enterprise_id == enterprise_id,
            RoleBinding.active.is_(True),
            RoleBinding.actor_id.in_(expected_actors),
        )
    ).all()
    assert len(bindings) == 8
    assert {row.actor_id for row in bindings} == expected_actors


def test_position_cannot_reference_another_enterprise_org(db_session) -> None:
    from sqlalchemy.exc import IntegrityError

    session, enterprise_id = db_session
    package = (
        Path(__file__).resolve().parents[4] / "data/enterprise/damai-logistics/v1/organization"
    )
    from flow_api.enterprise.directory import sync_enterprise_directory

    sync_enterprise_directory(session, enterprise_id, package)
    foreign_enterprise_id = uuid4()
    session.add(
        Enterprise(
            id=foreign_enterprise_id,
            code=f"org-foreign-{foreign_enterprise_id}",
            name="隔离边界测试",
        )
    )
    session.flush()
    unit = session.scalar(
        select(EnterpriseOrgUnit).where(EnterpriseOrgUnit.enterprise_id == enterprise_id)
    )
    assert unit is not None
    session.add(
        EnterprisePosition(
            enterprise_id=foreign_enterprise_id,
            org_unit_id=unit.id,
            code="CROSS-TENANT",
            title="越权岗位",
            job_family="test",
            level="test",
            status="active",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_stale_enterprise_identity_is_inactivated_and_binding_revoked(db_session) -> None:
    from flow_api.enterprise.directory import sync_enterprise_directory

    session, enterprise_id = db_session
    package = (
        Path(__file__).resolve().parents[4] / "data/enterprise/damai-logistics/v1/organization"
    )
    sync_enterprise_directory(session, enterprise_id, package)
    session.flush()

    removed_actor = "damai-logistics:usr:stale-999"
    unit = session.scalar(
        select(EnterpriseOrgUnit).where(EnterpriseOrgUnit.enterprise_id == enterprise_id)
    )
    position = session.scalar(
        select(EnterprisePosition).where(
            EnterprisePosition.enterprise_id == enterprise_id,
            EnterprisePosition.code == "POS-FIN-DIR",
        )
    )
    assert unit is not None and position is not None
    session.add(
        EnterpriseMember(
            enterprise_id=enterprise_id,
            actor_id=removed_actor,
            employee_code="STALE-999",
            display_name="过期身份",
            org_unit_id=unit.id,
            position_id=position.id,
            identity_metadata={"synthetic": True},
            identity_kind="human",
            status="active",
        )
    )
    session.add(
        RoleBinding(
            enterprise_id=enterprise_id,
            actor_id=removed_actor,
            role="analyst",
            is_service_account=False,
            active=True,
        )
    )
    session.flush()
    sync_enterprise_directory(session, enterprise_id, package)
    session.flush()

    member = session.scalar(
        select(EnterpriseMember).where(
            EnterpriseMember.enterprise_id == enterprise_id,
            EnterpriseMember.actor_id == removed_actor,
        )
    )
    binding = session.scalar(select(RoleBinding).where(RoleBinding.actor_id == removed_actor))
    assert member is not None and member.status == "inactive"
    assert binding is not None and binding.active is False and binding.revoked_at is not None
