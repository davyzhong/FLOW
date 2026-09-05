"""外部公开财报抽取数据落库：statement_report 与 statement_line_item。

数值列按披露原文列式存放（余额列式：期末/期初；发生额列式：本期/上期），
不换算单位；单位随 statement_report.unit_note 记录。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_statement_reports"
down_revision: str | None = "0010_frozen_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "statement_report",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("stock_code", sa.String(length=32), nullable=False),
        sa.Column("report_kind", sa.String(length=32), nullable=False),
        sa.Column("period_label", sa.String(length=64), nullable=False),
        sa.Column("unit_note", sa.String(length=64), nullable=False),
        sa.Column("source_ref", sa.String(length=512), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "stock_code",
            "period_label",
            "report_kind",
            name="uq_statement_report_identity",
        ),
    )
    op.create_table(
        "statement_line_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("statement_report.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("statement_type", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("value_end", sa.Numeric(24, 4), nullable=True),
        sa.Column("value_begin", sa.Numeric(24, 4), nullable=True),
        sa.Column("value_current", sa.Numeric(24, 4), nullable=True),
        sa.Column("value_prior", sa.Numeric(24, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_statement_line_item_report_stmt",
        "statement_line_item",
        ["report_id", "statement_type", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_statement_line_item_report_stmt", table_name="statement_line_item")
    op.drop_table("statement_line_item")
    op.drop_table("statement_report")
