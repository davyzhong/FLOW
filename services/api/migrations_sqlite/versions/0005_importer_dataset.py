"""R2：导入数据集存储（科目余额 + 利润表，与演示数据隔离）。

Revision ID: sqlite0005
Revises: sqlite0004
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "sqlite0005"
down_revision = "sqlite0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_dataset",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("source_filename", sa.String(512), nullable=False),
    )
    op.create_table(
        "import_trial_balance_row",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("account_code", sa.String(64), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("account_category", sa.String(16), nullable=False),
        sa.Column("direction", sa.String(2), nullable=False),
        sa.Column("opening_balance", sa.String(64), nullable=False),
        sa.Column("debit_amount", sa.String(64), nullable=False),
        sa.Column("credit_amount", sa.String(64), nullable=False),
        sa.Column("closing_balance", sa.String(64), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
    )
    op.create_table(
        "import_income_statement_row",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("item", sa.String(255), nullable=False),
        sa.Column("current_amount", sa.String(64), nullable=False),
        sa.Column("ytd_amount", sa.String(64), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_import_tb_dataset", "import_trial_balance_row", ["dataset_id"]
    )
    op.create_index(
        "ix_import_is_dataset", "import_income_statement_row", ["dataset_id"]
    )


def downgrade() -> None:
    op.drop_table("import_income_statement_row")
    op.drop_table("import_trial_balance_row")
    op.drop_table("import_dataset")
