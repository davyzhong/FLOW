"""事实复核与更正（B05）：statement_correction 审计表 + statement_report.status。

更正只增不改（审计链）；发布状态机 draft → published，
发布后报表行与更正均不可再变。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_statement_review"
down_revision: str | None = "0015_statement_normalization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "statement_report",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
    )
    op.create_check_constraint(
        "ck_statement_report_status", "statement_report", "status in ('draft', 'published')"
    )

    op.create_table(
        "statement_correction",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("statement_report.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("statement_type", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("column_key", sa.String(length=32), nullable=False),
        sa.Column("old_value", sa.Numeric(24, 4), nullable=True),
        sa.Column("new_value", sa.Numeric(24, 4), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("operator", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "column_key in ('value_end', 'value_begin', 'value_current', 'value_prior')",
            name="ck_statement_correction_column",
        ),
    )
    op.create_index(
        "ix_statement_correction_report",
        "statement_correction",
        ["report_id", "statement_type", "item_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_statement_correction_report", table_name="statement_correction")
    op.drop_table("statement_correction")
    op.drop_constraint("ck_statement_report_status", "statement_report")
    op.drop_column("statement_report", "status")
