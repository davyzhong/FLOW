"""将 JSON 与定标 Decimal 范围约束升级为 SQLite 表达式。

Revision ID: sqlite0002
Revises: sqlite0001
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "sqlite0002"
down_revision = "sqlite0001"
branch_labels = None
depends_on = None

_OLD_CHECK = "ck_enterprise_member_synthetic"
_SQLITE_CHECK = "ck_enterprise_member_synthetic_sqlite"
_SQLITE_EXPRESSION = "json_extract(identity_metadata, '$.synthetic') = 1"


def upgrade() -> None:
    checks = {
        item["name"]: item["sqltext"]
        for item in sa.inspect(op.get_bind()).get_check_constraints("enterprise_member")
        if item.get("name")
    }
    remove_old = _OLD_CHECK in checks
    add_sqlite = _SQLITE_CHECK not in checks
    if not remove_old and not add_sqlite:
        return

    with op.batch_alter_table("enterprise_member", recreate="always") as batch:
        if remove_old:
            batch.drop_constraint(_OLD_CHECK, type_="check")
        if add_sqlite:
            batch.create_check_constraint(_SQLITE_CHECK, _SQLITE_EXPRESSION)


def downgrade() -> None:
    checks = {
        item["name"]
        for item in sa.inspect(op.get_bind()).get_check_constraints("enterprise_member")
        if item.get("name")
    }
    if _SQLITE_CHECK not in checks:
        return

    with op.batch_alter_table("enterprise_member", recreate="always") as batch:
        batch.drop_constraint(_SQLITE_CHECK, type_="check")
        batch.create_check_constraint(
            _OLD_CHECK,
            "identity_metadata ->> 'synthetic' = 'true'",
        )
