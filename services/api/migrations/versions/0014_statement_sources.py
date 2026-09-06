"""公开财报原始文件登记（B01）：statement_source 表。

内容寻址不可变存储；同一 sha256 重复上传幂等。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_statement_sources"
down_revision: str | None = "0013_metric_catalog_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "statement_source",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("text_chars", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("company_candidate", sa.String(length=255), nullable=True),
        sa.Column("stock_code_candidate", sa.String(length=32), nullable=True),
        sa.Column("period_candidate", sa.String(length=64), nullable=True),
        sa.Column("report_kind_candidate", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("sha256", name="uq_statement_source_sha256"),
        sa.UniqueConstraint("object_key", name="uq_statement_source_object_key"),
        sa.CheckConstraint("length(sha256) = 64", name="ck_statement_source_sha256_length"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_statement_source_size_nonnegative"),
        sa.CheckConstraint("page_count >= 1", name="ck_statement_source_page_count_positive"),
        sa.CheckConstraint("status in ('registered')", name="ck_statement_source_status"),
    )


def downgrade() -> None:
    op.drop_table("statement_source")
