"""T10：statement 溯源列（B3）+ 重述 supersedes 链（B4）。

- `statement_line_item.page_number` / `page_anchor`：数据点级溯源定位
  （源 PDF 页码与锚定模式 strong/weak，由 T09-L1 答案集在导入时写入）；
- `statement_report.supersedes_id`：重述版本显式指向被取代版本
  （导入器内容 hash 变化新建版本时回填）；旧版行项目完整保留。
- downgrade 完整还原。
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "0029_statement_provenance"
down_revision: str | None = "0028_publication_four_stage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "statement_line_item",
        sa.Column("page_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "statement_line_item",
        sa.Column("page_anchor", sa.String(length=16), nullable=True),
    )
    op.create_check_constraint(
        "ck_statement_line_item_page_anchor",
        "statement_line_item",
        "page_anchor IS NULL OR page_anchor IN ('strong', 'weak')",
    )
    op.add_column(
        "statement_report",
        sa.Column("supersedes_id", PG_UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_statement_report_supersedes",
        "statement_report",
        "statement_report",
        ["supersedes_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_statement_report_supersedes", "statement_report", type_="foreignkey")
    op.drop_column("statement_report", "supersedes_id")
    op.drop_constraint(
        "ck_statement_line_item_page_anchor", "statement_line_item", type_="check"
    )
    op.drop_column("statement_line_item", "page_anchor")
    op.drop_column("statement_line_item", "page_number")
