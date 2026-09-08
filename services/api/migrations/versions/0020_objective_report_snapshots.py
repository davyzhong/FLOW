"""客观财报冻结快照（U6/P08 切片一，D049 客观基础优先）。

objective_report_snapshot：以 statement_report 为源的 typed 冻结载荷表，
复用不可变 JSONB 思想（CHECK 阻止 UPDATE，删除级联）；与旧月报
ReportSnapshot（指标快照源）完全独立，互不影响。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020_objective_report_snapshots"
down_revision: str | None = "0019_mpm_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "objective_report_snapshot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "statement_report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("statement_report.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "statement_report_id", "version", name="uq_objective_report_snapshot_version"
        ),
        sa.CheckConstraint(
            "report_type = 'objective_statement'", name="ck_objective_report_type"
        ),
        sa.CheckConstraint("version > 0", name="ck_objective_report_version_positive"),
        sa.CheckConstraint("length(payload_hash) = 64", name="ck_objective_payload_hash"),
    )


def downgrade() -> None:
    op.drop_table("objective_report_snapshot")
