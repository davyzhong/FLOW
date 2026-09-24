"""S01 集成测试：0026 安全迁移（RoleBinding / AuditEvent）实际 upgrade + 触发器实测。"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session


@pytest.fixture
def session() -> Session:
    from flow_api.infrastructure.db import get_session_factory

    return get_session_factory()()


def test_migration_head_is_0030(session: Session) -> None:
    result = session.execute(text("SELECT version_num FROM alembic_version"))
    version = result.scalar()
    assert version == "0030_page_anchor_vocabulary", f"迁移头不是 0030: {version}"


def test_role_binding_table_exists(session: Session) -> None:
    result = session.execute(
        text("SELECT count(*) FROM information_schema.tables WHERE table_name = 'role_binding'")
    )
    assert result.scalar() == 1


def test_audit_event_table_exists(session: Session) -> None:
    result = session.execute(
        text("SELECT count(*) FROM information_schema.tables WHERE table_name = 'audit_event'")
    )
    assert result.scalar() == 1


def test_audit_event_no_update_trigger(session: Session) -> None:
    result = session.execute(
        text(
            "SELECT count(*) FROM pg_trigger "
            "WHERE tgrelid = 'audit_event'::regclass AND tgname LIKE '%no_update%'"
        )
    )
    assert result.scalar() >= 1, "audit_event 缺少防 UPDATE 触发器"


def test_audit_event_no_delete_trigger(session: Session) -> None:
    result = session.execute(
        text(
            "SELECT count(*) FROM pg_trigger "
            "WHERE tgrelid = 'audit_event'::regclass AND tgname LIKE '%no_delete%'"
        )
    )
    assert result.scalar() >= 1, "audit_event 缺少防 DELETE 触发器"


def test_audit_event_insert_allowed(session: Session) -> None:
    session.execute(
        text(
            "INSERT INTO audit_event (event_type, correlation_id, actor_id, resource_scope, "
            "resource_type, resource_id, decision, reason_code, request_id, "
            "retention_class, retain_until) "
            "VALUES ('security.review', 'corr-test', 'actor-test', 'public', "
            "'test_resource', 'res-1', 'allow', 'test', 'req-1', 'standard', "
            "now() + interval '365 days')"
        )
    )
    session.commit()


def test_audit_event_update_blocked(session: Session) -> None:
    session.execute(
        text(
            "INSERT INTO audit_event (event_type, correlation_id, actor_id, resource_scope, "
            "resource_type, resource_id, decision, reason_code, request_id, "
            "retention_class, retain_until) "
            "VALUES ('security.review', 'corr-upd', 'actor', 'public', 'r', 'r1', "
            "'allow', 'test', 'req-2', 'standard', now() + interval '365 days')"
        )
    )
    session.commit()
    with pytest.raises(DBAPIError):
        session.execute(
            text("UPDATE audit_event SET decision = 'deny' WHERE correlation_id = 'corr-upd'")
        )
        session.commit()


def test_audit_event_delete_blocked(session: Session) -> None:
    session.execute(
        text(
            "INSERT INTO audit_event (event_type, correlation_id, actor_id, resource_scope, "
            "resource_type, resource_id, decision, reason_code, request_id, "
            "retention_class, retain_until) "
            "VALUES ('security.review', 'corr-del', 'actor', 'public', 'r', 'r2', "
            "'allow', 'test', 'req-3', 'standard', now() + interval '365 days')"
        )
    )
    session.commit()
    with pytest.raises(DBAPIError):
        session.execute(text("DELETE FROM audit_event WHERE correlation_id = 'corr-del'"))
        session.commit()
