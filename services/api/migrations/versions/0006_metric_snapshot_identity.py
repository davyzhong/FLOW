"""add governed metric snapshot identity and trace

Revision ID: 0006_metric_snapshot_identity
Revises: 0005_versioned_facts
Create Date: 2026-08-31 21:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_metric_snapshot_identity"
down_revision: str | None = "0005_versioned_facts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metric_definition_dependency",
        sa.Column("metric_definition_id", sa.UUID(), nullable=False),
        sa.Column("dependency_definition_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "metric_definition_id <> dependency_definition_id",
            name="ck_metric_definition_dependency_not_self",
        ),
        sa.CheckConstraint(
            "position > 0", name="ck_metric_definition_dependency_position_positive"
        ),
        sa.ForeignKeyConstraint(
            ["dependency_definition_id"], ["metric_definition.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["metric_definition_id"], ["metric_definition.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "metric_definition_id",
            "dependency_definition_id",
            name="uq_metric_definition_dependency_edge",
        ),
        sa.UniqueConstraint(
            "metric_definition_id",
            "position",
            name="uq_metric_definition_dependency_position",
        ),
    )

    op.drop_constraint(
        "uq_metric_snapshot_batch_version", "metric_snapshot", type_="unique"
    )
    op.add_column("metric_snapshot", sa.Column("import_version_id", sa.UUID()))
    op.add_column("metric_snapshot", sa.Column("as_of_period_id", sa.UUID()))
    op.add_column(
        "metric_snapshot",
        sa.Column(
            "definition_set_id",
            sa.String(length=128),
            server_default="legacy.metric.set",
            nullable=False,
        ),
    )
    op.add_column(
        "metric_snapshot",
        sa.Column(
            "definition_set_hash",
            sa.String(length=64),
            server_default="0" * 64,
            nullable=False,
        ),
    )
    op.add_column(
        "metric_snapshot",
        sa.Column(
            "fingerprint",
            sa.String(length=64),
            server_default="0" * 64,
            nullable=False,
        ),
    )
    op.add_column(
        "metric_snapshot",
        sa.Column(
            "status", sa.String(length=32), server_default="published", nullable=False
        ),
    )
    op.execute(
        sa.text(
            "UPDATE metric_snapshot ms SET import_version_id = "
            "(SELECT iv.id FROM import_version iv WHERE iv.batch_id = ms.batch_id "
            "ORDER BY iv.is_published DESC, iv.sequence DESC LIMIT 1)"
        )
    )
    op.execute(
        sa.text(
            "UPDATE metric_snapshot SET as_of_period_id = "
            "(SELECT id FROM dim_period ORDER BY month_key DESC LIMIT 1)"
        )
    )
    op.execute(
        sa.text(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM metric_snapshot "
            "WHERE import_version_id IS NULL OR as_of_period_id IS NULL) THEN "
            "RAISE EXCEPTION 'legacy metric snapshots require an import version and period'; "
            "END IF; END $$"
        )
    )
    op.alter_column("metric_snapshot", "import_version_id", nullable=False)
    op.alter_column("metric_snapshot", "as_of_period_id", nullable=False)
    op.alter_column("metric_snapshot", "status", server_default="building")
    op.create_unique_constraint(
        "uq_import_version_id_batch", "import_version", ["id", "batch_id"]
    )
    op.create_foreign_key(
        "fk_metric_snapshot_import_batch",
        "metric_snapshot",
        "import_version",
        ["import_version_id", "batch_id"],
        ["id", "batch_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_metric_snapshot_as_of_period",
        "metric_snapshot",
        "dim_period",
        ["as_of_period_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_metric_snapshot_status",
        "metric_snapshot",
        "status in ('building', 'published', 'failed')",
    )
    op.create_check_constraint(
        "ck_metric_snapshot_definition_hash_length",
        "metric_snapshot",
        "length(definition_set_hash) = 64",
    )
    op.create_check_constraint(
        "ck_metric_snapshot_fingerprint_length",
        "metric_snapshot",
        "length(fingerprint) = 64",
    )
    op.create_unique_constraint(
        "uq_metric_snapshot_identity_version",
        "metric_snapshot",
        ["batch_id", "import_version_id", "as_of_period_id", "version"],
    )

    op.add_column("metric_value", sa.Column("exact_value", sa.Text()))
    op.execute(sa.text("UPDATE metric_value SET exact_value = value::text"))
    op.alter_column("metric_value", "exact_value", nullable=False)
    op.add_column(
        "metric_value",
        sa.Column(
            "calculation_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("metric_value", "calculation_trace")
    op.drop_column("metric_value", "exact_value")
    op.drop_constraint(
        "uq_metric_snapshot_identity_version", "metric_snapshot", type_="unique"
    )
    op.drop_constraint(
        "ck_metric_snapshot_fingerprint_length", "metric_snapshot", type_="check"
    )
    op.drop_constraint(
        "ck_metric_snapshot_definition_hash_length", "metric_snapshot", type_="check"
    )
    op.drop_constraint("ck_metric_snapshot_status", "metric_snapshot", type_="check")
    op.drop_constraint(
        "fk_metric_snapshot_as_of_period", "metric_snapshot", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_metric_snapshot_import_batch", "metric_snapshot", type_="foreignkey"
    )
    op.drop_constraint("uq_import_version_id_batch", "import_version", type_="unique")
    op.drop_column("metric_snapshot", "status")
    op.drop_column("metric_snapshot", "fingerprint")
    op.drop_column("metric_snapshot", "definition_set_hash")
    op.drop_column("metric_snapshot", "definition_set_id")
    op.drop_column("metric_snapshot", "as_of_period_id")
    op.drop_column("metric_snapshot", "import_version_id")
    op.create_unique_constraint(
        "uq_metric_snapshot_batch_version", "metric_snapshot", ["batch_id", "version"]
    )
    op.drop_table("metric_definition_dependency")
