"""SQLite 原型基线：以当前 ORM metadata 创建完整 schema。

Revision ID: sqlite0001
Revises:
"""
from __future__ import annotations

from alembic import op

from flow_api.infrastructure.models import Base

revision = "sqlite0001"
down_revision = None
branch_labels = ("sqlite",)
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
