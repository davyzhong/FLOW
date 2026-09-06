"""指标库治理（C04）：metric_governance_event 审计事件表。

只增不改；记录草稿/验证/生效/退役动作的操作者、理由与差异。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_metric_governance"
down_revision: str | None = "0017_build_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metric_governance_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dictionary_id", sa.String(length=128), nullable=False),
        sa.Column("collection", sa.String(length=32), nullable=False),
        sa.Column("metric_code", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("operator", sa.String(length=128), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "action in ('draft', 'activate', 'retire')",
            name="ck_metric_governance_action",
        ),
    )
    op.create_index(
        "ix_metric_governance_entry",
        "metric_governance_event",
        ["dictionary_id", "collection", "metric_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_metric_governance_entry", table_name="metric_governance_event")
    op.drop_table("metric_governance_event")
