"""按 SQLite 定标整数单位校验 Finding 总分范围。

Revision ID: sqlite0004
Revises: sqlite0003
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "sqlite0004"
down_revision = "sqlite0003"
branch_labels = None
depends_on = None

_OLD_CHECK = "ck_finding_total_score_range"
_SQLITE_CHECK = "ck_finding_total_score_range_sqlite"


def upgrade() -> None:
    names = {
        row["name"]
        for row in sa.inspect(op.get_bind()).get_check_constraints("finding")
        if row.get("name")
    }
    remove_old = _OLD_CHECK in names
    add_sqlite = _SQLITE_CHECK not in names
    if not remove_old and not add_sqlite:
        return

    with op.batch_alter_table("finding", recreate="always") as batch:
        if remove_old:
            batch.drop_constraint(_OLD_CHECK, type_="check")
        if add_sqlite:
            batch.create_check_constraint(
                _SQLITE_CHECK,
                "total_score is null or total_score between 0 and 100000000",
            )


def downgrade() -> None:
    names = {
        row["name"]
        for row in sa.inspect(op.get_bind()).get_check_constraints("finding")
        if row.get("name")
    }
    if _SQLITE_CHECK not in names:
        return

    with op.batch_alter_table("finding", recreate="always") as batch:
        batch.drop_constraint(_SQLITE_CHECK, type_="check")
        batch.create_check_constraint(
            _OLD_CHECK,
            "total_score is null or total_score between 0 and 100",
        )
