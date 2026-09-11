"""经营报告发布：修正快照版本键并复用统一 PublicationAttempt。

Revision ID: 0024_operations_publication
Revises: 0023_operations_overview
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024_operations_publication"
down_revision: str | None = "0023_operations_overview"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 财务客观报告与经营报告拥有独立的 v1/v2... 版本序列。
    op.drop_constraint(
        "uq_objective_report_snapshot_version",
        "objective_report_snapshot",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_objective_report_snapshot_type_version",
        "objective_report_snapshot",
        ["statement_report_id", "report_type", "version"],
    )

    # 同一 append-only 发布尝试表同时服务管理月报和客观/经营报告；恰有一个父快照。
    op.alter_column("publication_attempt", "report_snapshot_id", nullable=True)
    op.add_column(
        "publication_attempt",
        sa.Column("objective_report_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_publication_attempt_objective_snapshot",
        "publication_attempt",
        "objective_report_snapshot",
        ["objective_report_snapshot_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_publication_attempt_objective_sequence",
        "publication_attempt",
        ["objective_report_snapshot_id", "sequence"],
    )
    op.create_check_constraint(
        "ck_publication_attempt_single_parent",
        "publication_attempt",
        "num_nonnulls(report_snapshot_id, objective_report_snapshot_id) = 1",
    )


def downgrade() -> None:
    # 旧结构无法表达经营快照及其发布历史；先移除本迁移新增的数据形态，
    # 否则恢复 report_snapshot_id NOT NULL / 旧唯一键会在有真实数据时失败。
    op.execute(
        "DELETE FROM publication_attempt "
        "WHERE objective_report_snapshot_id IS NOT NULL"
    )
    op.drop_constraint("ck_publication_attempt_single_parent", "publication_attempt", type_="check")
    op.drop_constraint(
        "uq_publication_attempt_objective_sequence",
        "publication_attempt",
        type_="unique",
    )
    op.drop_constraint(
        "fk_publication_attempt_objective_snapshot",
        "publication_attempt",
        type_="foreignkey",
    )
    op.drop_column("publication_attempt", "objective_report_snapshot_id")
    op.alter_column("publication_attempt", "report_snapshot_id", nullable=False)

    op.execute(
        "DELETE FROM objective_report_snapshot "
        "WHERE report_type <> 'objective_statement'"
    )
    op.drop_constraint(
        "uq_objective_report_snapshot_type_version",
        "objective_report_snapshot",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_objective_report_snapshot_version",
        "objective_report_snapshot",
        ["statement_report_id", "version"],
    )
