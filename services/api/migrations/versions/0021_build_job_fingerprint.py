"""编排幂等键加版本指纹（review 修复）：build_job.fingerprint。

指标目录 + 分析政策的版本指纹；不带指纹的旧任务不再参与幂等回放。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021_build_job_fingerprint"
down_revision: str | None = "0020_objective_report_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "build_job",
        sa.Column("fingerprint", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("build_job", "fingerprint")
