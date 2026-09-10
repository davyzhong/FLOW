"""经营轨六主题概览快照（O3 slice-2）：report_type 枚举扩展。

objective_report_snapshot 表的 CHECK 约束扩展允许 operations_overview
（六主题概览冻结载荷，版本序列与 objective_statement 相互独立）。
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0023_operations_overview"
down_revision: str | None = "0022_normalized_group_ordinal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "ck_objective_report_type", "objective_report_snapshot", type_="check"
    )
    op.create_check_constraint(
        "ck_objective_report_type",
        "objective_report_snapshot",
        "report_type in ('objective_statement', 'operations_overview')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_objective_report_type", "objective_report_snapshot", type_="check"
    )
    op.create_check_constraint(
        "ck_objective_report_type",
        "objective_report_snapshot",
        "report_type = 'objective_statement'",
    )
