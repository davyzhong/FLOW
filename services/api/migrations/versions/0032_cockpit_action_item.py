"""Add cockpit action item (批次 B3：Finding 派生、审计确认闭环)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0032_cockpit_action_item"
down_revision: str | None = "0031_enterprise_directory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # V1.1.1：role_binding 的 role 枚举 CHECK 增加 'cfo'（安全规格 §14.2-1 连带）
    op.execute(
        "ALTER TABLE role_binding DROP CONSTRAINT ck_role_binding_role_enum"
    )
    op.execute(
        "ALTER TABLE role_binding ADD CONSTRAINT ck_role_binding_role_enum "
        "CHECK (role IN ('finance_bp','cfo','analyst','rule_owner',"
        "'ai_analyst','ai_cfo','service_account'))"
    )
    op.create_table(
        "cockpit_action_item",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("enterprise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["finding_id"], ["finding.id"], name="fk_action_item_finding"
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["metric_snapshot.id"], name="fk_action_item_snapshot"
        ),
        sa.CheckConstraint(
            "char_length(title) between 1 and 200", name="ck_action_item_title_len"
        ),
        comment=(
            "驾驶舱行动项（批次 B3）：Finding 派生、只读展示、"
            "确认动作仅写 durable AuditEvent（不改本行）"
        ),
    )
    op.create_index(
        "ix_action_item_enterprise_created",
        "cockpit_action_item",
        ["enterprise_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_action_item_enterprise_created", table_name="cockpit_action_item")
    op.drop_table("cockpit_action_item")
    # 先清 cfo 行：downgrade 恢复旧枚举 CHECK 时残留行会违约（downgrade 是
    # 破坏性契约，test_migrations 的 downgrade→upgrade 往返依赖可重放）
    op.execute("DELETE FROM role_binding WHERE role = 'cfo'")
    op.execute(
        "ALTER TABLE role_binding DROP CONSTRAINT ck_role_binding_role_enum"
    )
    op.execute(
        "ALTER TABLE role_binding ADD CONSTRAINT ck_role_binding_role_enum "
        "CHECK (role IN ('finance_bp','analyst','rule_owner',"
        "'ai_analyst','ai_cfo','service_account'))"
    )
