"""归一化行唯一键加分组序号（U2/6.1 契约决策，用户已确认）。

港股 IFRS 披露存在合法同名行项目（借款/租赁负债等在流动、非流动分组下
各一行），「每报表行名唯一」假设不成立。唯一键加入 group_ordinal
（同名行按披露出现序 0,1,2…），保留披露原文分组语义，不合并原始行。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022_normalized_group_ordinal"
down_revision: str | None = "0021_build_job_fingerprint"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "statement_normalized_item",
        sa.Column(
            "group_ordinal",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.drop_constraint("uq_statement_normalized_item", "statement_normalized_item", type_="unique")
    op.create_unique_constraint(
        "uq_statement_normalized_item",
        "statement_normalized_item",
        ["report_id", "mapping_version", "statement_type", "group_ordinal", "item_name"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_statement_normalized_item", "statement_normalized_item", type_="unique")
    op.create_unique_constraint(
        "uq_statement_normalized_item",
        "statement_normalized_item",
        ["report_id", "mapping_version", "statement_type", "item_name"],
    )
    op.drop_column("statement_normalized_item", "group_ordinal")
