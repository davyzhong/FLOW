"""规范化与修订版本（B03）：statement_report 版本化 + statement_normalized_item。

- statement_report 增加 version 与 content_sha256：同身份同内容幂等重建，
  同身份不同内容（重述）递增版本、旧版保留；
- statement_normalized_item：原始行 → 标准报表项目 item_id 的归一化结果，
  按 mapping_version 修订并存，原始行不受影响。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_statement_normalization"
down_revision: str | None = "0014_statement_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_statement_report_identity", "statement_report", type_="unique")
    op.add_column(
        "statement_report",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "statement_report",
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_statement_report_identity",
        "statement_report",
        ["stock_code", "period_label", "report_kind", "version"],
    )
    op.create_check_constraint(
        "ck_statement_report_version_positive", "statement_report", "version > 0"
    )

    op.create_table(
        "statement_normalized_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("statement_report.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mapping_version", sa.String(length=32), nullable=False),
        sa.Column("statement_type", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("item_id", sa.String(length=64), nullable=True),
        sa.Column("value_end", sa.Numeric(24, 4), nullable=True),
        sa.Column("value_begin", sa.Numeric(24, 4), nullable=True),
        sa.Column("value_current", sa.Numeric(24, 4), nullable=True),
        sa.Column("value_prior", sa.Numeric(24, 4), nullable=True),
        sa.Column(
            "trace",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "report_id",
            "mapping_version",
            "statement_type",
            "item_name",
            name="uq_statement_normalized_item",
        ),
    )
    op.create_index(
        "ix_statement_normalized_item_report",
        "statement_normalized_item",
        ["report_id", "mapping_version", "statement_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_statement_normalized_item_report", table_name="statement_normalized_item"
    )
    op.drop_table("statement_normalized_item")
    op.drop_constraint("uq_statement_report_identity", "statement_report", type_="unique")
    op.create_unique_constraint(
        "uq_statement_report_identity",
        "statement_report",
        ["stock_code", "period_label", "report_kind"],
    )
    op.drop_constraint("ck_statement_report_version_positive", "statement_report")
    op.drop_column("statement_report", "content_sha256")
    op.drop_column("statement_report", "version")
