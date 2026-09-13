"""企业空间与月度分析周期：enterprise / analysis_cycle 表与批次合法组合矩阵。

规格：docs/40_specs/financial-facts/financial-facts-contract-v2.md（approved）§4。
- 只加不改：不触碰 frozen_view 与任何历史事实值；
- 存量 analysis_batch 经 server_default 回填 legacy/1/cycle NULL；
- 合法组合由单一 CHECK 承载：legacy/1/cycle NULL、public/1|2/cycle NULL、
  internal/2/cycle NOT NULL，其余全部拒绝。

Revision ID: 0025_enterprise_cycle
Revises: 0024_operations_publication
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025_enterprise_cycle"
down_revision: str | None = "0024_operations_publication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


COMBO_CHECK = (
    "(module_kind = 'legacy' AND fact_context_version = 1 AND analysis_cycle_id IS NULL)"
    " OR (module_kind = 'public' AND fact_context_version IN (1, 2)"
    " AND analysis_cycle_id IS NULL)"
    " OR (module_kind = 'internal' AND fact_context_version = 2"
    " AND analysis_cycle_id IS NOT NULL)"
)


def upgrade() -> None:
    op.create_table(
        "enterprise",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("code", sa.String(128), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.create_table(
        "analysis_cycle",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("enterprise_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_key", sa.String(7), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.ForeignKeyConstraint(
            ["enterprise_id"], ["enterprise.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "enterprise_id", "period_key", name="uq_analysis_cycle_enterprise_period"
        ),
        sa.CheckConstraint(
            r"period_key ~ '^\d{4}-(0[1-9]|1[0-2])$'", name="ck_analysis_cycle_period_key"
        ),
        sa.CheckConstraint(
            "status in ('open', 'frozen', 'closed')", name="ck_analysis_cycle_status"
        ),
    )

    op.add_column(
        "analysis_batch",
        sa.Column("analysis_cycle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "analysis_batch",
        sa.Column("module_kind", sa.String(32), nullable=False, server_default="legacy"),
    )
    op.add_column(
        "analysis_batch",
        sa.Column(
            "fact_context_version", sa.Integer(), nullable=False, server_default="1"
        ),
    )
    op.create_foreign_key(
        "fk_analysis_batch_cycle",
        "analysis_batch",
        "analysis_cycle",
        ["analysis_cycle_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_analysis_batch_module_combo", "analysis_batch", COMBO_CHECK
    )


def downgrade() -> None:
    op.drop_constraint("ck_analysis_batch_module_combo", "analysis_batch", type_="check")
    op.drop_constraint("fk_analysis_batch_cycle", "analysis_batch", type_="foreignkey")
    op.drop_column("analysis_batch", "fact_context_version")
    op.drop_column("analysis_batch", "module_kind")
    op.drop_column("analysis_batch", "analysis_cycle_id")
    op.drop_table("analysis_cycle")
    op.drop_table("enterprise")
