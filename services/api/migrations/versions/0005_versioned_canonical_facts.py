"""version canonical facts without overwriting prior imports

Revision ID: 0005_versioned_facts
Revises: 0004_intake_audit
Create Date: 2026-08-30 20:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_versioned_facts"
down_revision: str | None = "0004_intake_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FACT_TABLES = (
    "fact_operating_actual",
    "fact_financial_actual",
    "fact_budget",
    "fact_ar_collection",
)


def upgrade() -> None:
    op.add_column(
        "quality_issue",
        sa.Column("evidence", sa.Text(), server_default="", nullable=False),
    )
    op.add_column(
        "quality_issue",
        sa.Column("repair_suggestion", sa.Text(), server_default="", nullable=False),
    )
    for table in FACT_TABLES:
        op.add_column(table, sa.Column("business_record_id", sa.UUID(), nullable=True))
        op.execute(sa.text(f"UPDATE {table} SET business_record_id = id"))
        op.alter_column(table, "business_record_id", nullable=False)
        op.create_unique_constraint(
            f"uq_{table}_version_business_record",
            table,
            ["import_version_id", "business_record_id"],
        )

    op.drop_constraint("uq_operating_actual_grain", "fact_operating_actual", type_="unique")
    op.create_unique_constraint(
        "uq_operating_actual_grain",
        "fact_operating_actual",
        [
            "import_version_id",
            "period_id",
            "organization_id",
            "customer_id",
            "logistics_product_id",
            "region_id",
        ],
    )
    op.drop_constraint("uq_financial_actual_grain", "fact_financial_actual", type_="unique")
    op.create_unique_constraint(
        "uq_financial_actual_grain",
        "fact_financial_actual",
        ["import_version_id", "period_id", "organization_id", "management_account_id"],
    )
    op.drop_index("uq_fact_budget_grain", table_name="fact_budget")
    op.create_index(
        "uq_fact_budget_grain",
        "fact_budget",
        [
            "import_version_id",
            "period_id",
            "organization_id",
            "customer_segment_id",
            "logistics_product_id",
            "management_account_id",
            "scenario_version_id",
            "metric_code",
        ],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
    op.drop_index("uq_fact_ar_collection_grain", table_name="fact_ar_collection")
    op.create_index(
        "uq_fact_ar_collection_grain",
        "fact_ar_collection",
        [
            "import_version_id",
            "period_id",
            "customer_id",
            "invoice_number",
            "aging_bucket",
        ],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_index("uq_fact_ar_collection_grain", table_name="fact_ar_collection")
    op.create_index(
        "uq_fact_ar_collection_grain",
        "fact_ar_collection",
        ["period_id", "customer_id", "invoice_number", "aging_bucket"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
    op.drop_index("uq_fact_budget_grain", table_name="fact_budget")
    op.create_index(
        "uq_fact_budget_grain",
        "fact_budget",
        [
            "period_id",
            "organization_id",
            "customer_segment_id",
            "logistics_product_id",
            "management_account_id",
            "scenario_version_id",
            "metric_code",
        ],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
    op.drop_constraint("uq_financial_actual_grain", "fact_financial_actual", type_="unique")
    op.create_unique_constraint(
        "uq_financial_actual_grain",
        "fact_financial_actual",
        ["period_id", "organization_id", "management_account_id"],
    )
    op.drop_constraint("uq_operating_actual_grain", "fact_operating_actual", type_="unique")
    op.create_unique_constraint(
        "uq_operating_actual_grain",
        "fact_operating_actual",
        [
            "period_id",
            "organization_id",
            "customer_id",
            "logistics_product_id",
            "region_id",
        ],
    )
    for table in reversed(FACT_TABLES):
        op.drop_constraint(f"uq_{table}_version_business_record", table, type_="unique")
        op.drop_column(table, "business_record_id")
    op.drop_column("quality_issue", "repair_suggestion")
    op.drop_column("quality_issue", "evidence")
