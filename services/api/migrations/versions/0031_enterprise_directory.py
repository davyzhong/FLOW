"""Add tenant-scoped enterprise org units, positions and members."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0031_enterprise_directory"
down_revision: str | None = "0030_page_anchor_vocabulary"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "enterprise_org_unit",
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
        sa.Column("enterprise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit_type", sa.String(32), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column(
            "attributes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_enterprise_org_unit"),
        sa.ForeignKeyConstraint(
            ["enterprise_id"],
            ["enterprise.id"],
            name="fk_enterprise_org_unit_enterprise_id_enterprise",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("enterprise_id", "code", name="uq_enterprise_org_unit_code"),
        sa.UniqueConstraint("id", "enterprise_id", name="uq_enterprise_org_unit_id_enterprise"),
        sa.CheckConstraint(
            "unit_type IN ('department', 'business_unit', 'team')",
            name="ck_enterprise_org_unit_type",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')", name="ck_enterprise_org_unit_status"
        ),
    )
    op.create_foreign_key(
        "fk_enterprise_org_unit_parent_tenant",
        "enterprise_org_unit",
        "enterprise_org_unit",
        ["parent_id", "enterprise_id"],
        ["id", "enterprise_id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "enterprise_position",
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
        sa.Column("enterprise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("job_family", sa.String(128), nullable=False),
        sa.Column("level", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id", name="pk_enterprise_position"),
        sa.ForeignKeyConstraint(
            ["enterprise_id"],
            ["enterprise.id"],
            name="fk_enterprise_position_enterprise_id_enterprise",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["org_unit_id", "enterprise_id"],
            ["enterprise_org_unit.id", "enterprise_org_unit.enterprise_id"],
            name="fk_enterprise_position_org_tenant",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("enterprise_id", "code", name="uq_enterprise_position_code"),
        sa.UniqueConstraint("id", "enterprise_id", name="uq_enterprise_position_id_enterprise"),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')", name="ck_enterprise_position_status"
        ),
    )
    op.create_table(
        "enterprise_member",
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
        sa.Column("enterprise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("employee_code", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("org_unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supervisor_actor_id", sa.String(128), nullable=True),
        sa.Column("identity_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("identity_kind", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.PrimaryKeyConstraint("id", name="pk_enterprise_member"),
        sa.ForeignKeyConstraint(
            ["enterprise_id"],
            ["enterprise.id"],
            name="fk_enterprise_member_enterprise_id_enterprise",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["org_unit_id", "enterprise_id"],
            ["enterprise_org_unit.id", "enterprise_org_unit.enterprise_id"],
            name="fk_enterprise_member_org_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["position_id", "enterprise_id"],
            ["enterprise_position.id", "enterprise_position.enterprise_id"],
            name="fk_enterprise_member_position_tenant",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["supervisor_actor_id", "enterprise_id"],
            ["enterprise_member.actor_id", "enterprise_member.enterprise_id"],
            name="fk_enterprise_member_supervisor_tenant",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("enterprise_id", "actor_id", name="uq_enterprise_member_actor"),
        sa.UniqueConstraint("enterprise_id", "employee_code", name="uq_enterprise_member_employee"),
        sa.CheckConstraint(
            "identity_kind IN ('human', 'ai', 'service')", name="ck_enterprise_member_identity_kind"
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_enterprise_member_status"),
        sa.CheckConstraint(
            "identity_metadata ->> 'synthetic' = 'true'", name="ck_enterprise_member_synthetic"
        ),
    )
    op.create_index(
        "ix_enterprise_org_unit_enterprise_id", "enterprise_org_unit", ["enterprise_id"]
    )
    op.create_index(
        "ix_enterprise_position_enterprise_id", "enterprise_position", ["enterprise_id"]
    )
    op.create_index("ix_enterprise_member_enterprise_id", "enterprise_member", ["enterprise_id"])
    op.create_index("ix_enterprise_member_actor_id", "enterprise_member", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_enterprise_member_actor_id", table_name="enterprise_member")
    op.drop_index("ix_enterprise_member_enterprise_id", table_name="enterprise_member")
    op.drop_index("ix_enterprise_position_enterprise_id", table_name="enterprise_position")
    op.drop_index("ix_enterprise_org_unit_enterprise_id", table_name="enterprise_org_unit")
    op.drop_table("enterprise_member")
    op.drop_table("enterprise_position")
    op.drop_table("enterprise_org_unit")
