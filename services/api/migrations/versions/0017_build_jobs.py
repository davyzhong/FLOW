"""通用期间与可恢复编排（B06）：build_job 构建任务表。

构建任务持久化状态（queued/running/succeeded/failed）、期间清单与结果身份；
失败留痕可重试，部分失败不覆盖既有不可变快照。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_build_jobs"
down_revision: str | None = "0016_statement_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "build_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_batch.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("months", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "metric_snapshot_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status in ('queued', 'running', 'succeeded', 'failed')",
            name="ck_build_job_status",
        ),
    )
    op.create_index("ix_build_job_batch", "build_job", ["batch_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_build_job_batch", table_name="build_job")
    op.drop_table("build_job")
