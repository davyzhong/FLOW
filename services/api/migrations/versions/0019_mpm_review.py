"""P01：指标库 MPM 结构化判定字段（mpm_review）。

前向默认 NULL = 未核验（历史条目不伪造已核验状态）；v2 起随订正写入。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_mpm_review"
down_revision: str | None = "0018_metric_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "metric_dictionary_entry",
        sa.Column("mpm_review", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("metric_dictionary_entry", "mpm_review")
