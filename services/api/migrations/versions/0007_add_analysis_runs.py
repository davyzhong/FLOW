"""add deterministic analysis runs and finding scores

Revision ID: 0007_add_analysis_runs
Revises: 0006_metric_snapshot_identity
Create Date: 2026-09-01 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_add_analysis_runs"
down_revision: str | None = "0006_metric_snapshot_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity_columns() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "analysis_run",
        sa.Column("metric_snapshot_id", sa.UUID(), nullable=False),
        sa.Column("import_version_id", sa.UUID(), nullable=False),
        sa.Column("policy_id", sa.String(length=128), nullable=False),
        sa.Column("policy_set_hash", sa.String(length=64), nullable=False),
        sa.Column("engine_version", sa.String(length=128), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="building", nullable=False),
        *_identity_columns(),
        sa.CheckConstraint(
            "length(fingerprint) = 64", name="ck_analysis_run_fingerprint_length"
        ),
        sa.CheckConstraint(
            "length(policy_set_hash) = 64", name="ck_analysis_run_policy_hash_length"
        ),
        sa.CheckConstraint(
            "status in ('building', 'published', 'failed')", name="ck_analysis_run_status"
        ),
        sa.ForeignKeyConstraint(
            ["import_version_id"], ["import_version.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["metric_snapshot_id"], ["metric_snapshot.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "metric_snapshot_id",
            "policy_set_hash",
            "engine_version",
            name="uq_analysis_run_identity",
        ),
    )
    op.create_table(
        "analysis_result",
        sa.Column("analysis_run_id", sa.UUID(), nullable=False),
        sa.Column("playbook_code", sa.String(length=128), nullable=False),
        sa.Column("playbook_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("comparison_basis", sa.String(length=32), nullable=False),
        sa.Column("impact_amount", sa.Numeric(precision=24, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column(
            "reconciliation_difference", sa.Numeric(precision=24, scale=4), nullable=False
        ),
        sa.Column(
            "reconciliation_tolerance", sa.Numeric(precision=24, scale=4), nullable=False
        ),
        sa.Column(
            "required_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "available_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "missing_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("source_record_count", sa.Integer(), nullable=False),
        sa.Column(
            "calculation_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("degradation_code", sa.String(length=64), nullable=True),
        sa.Column("degradation_message", sa.Text(), nullable=True),
        *_identity_columns(),
        sa.CheckConstraint(
            "comparison_basis in ('prior_year', 'budget')",
            name="ck_analysis_result_comparison_basis",
        ),
        sa.CheckConstraint(
            "playbook_version > 0", name="ck_analysis_result_version_positive"
        ),
        sa.CheckConstraint(
            "reconciliation_tolerance >= 0",
            name="ck_analysis_result_tolerance_nonnegative",
        ),
        sa.CheckConstraint(
            "source_record_count >= 0", name="ck_analysis_result_source_count_nonnegative"
        ),
        sa.CheckConstraint(
            "status in ('complete', 'degraded', 'not_applicable')",
            name="ck_analysis_result_status",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"], ["analysis_run.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_run_id",
            "playbook_code",
            "comparison_basis",
            name="uq_analysis_result_run_playbook_basis",
        ),
    )
    op.create_table(
        "analysis_driver",
        sa.Column("analysis_result_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("driver_code", sa.String(length=128), nullable=False),
        sa.Column("calculation_method", sa.Text(), nullable=True),
        sa.Column("contribution_amount", sa.Numeric(precision=24, scale=4), nullable=False),
        sa.Column("contribution_ratio", sa.Numeric(precision=16, scale=6), nullable=True),
        sa.Column(
            "calculation_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_identity_columns(),
        sa.CheckConstraint("position > 0", name="ck_analysis_driver_position_positive"),
        sa.ForeignKeyConstraint(
            ["analysis_result_id"], ["analysis_result.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_result_id", "position", name="uq_analysis_driver_order"
        ),
        sa.UniqueConstraint(
            "analysis_result_id", "driver_code", name="uq_analysis_driver_result_code"
        ),
    )

    op.add_column("finding", sa.Column("analysis_run_id", sa.UUID(), nullable=True))
    op.add_column("finding", sa.Column("analysis_result_id", sa.UUID(), nullable=True))
    op.add_column("finding", sa.Column("finding_type", sa.String(length=128), nullable=True))
    op.add_column("finding", sa.Column("fact_statement", sa.Text(), nullable=True))
    op.add_column("finding", sa.Column("comparison_basis", sa.String(length=32), nullable=True))
    op.add_column(
        "finding", sa.Column("total_score", sa.Numeric(precision=12, scale=6), nullable=True)
    )
    op.add_column("finding", sa.Column("policy_version", sa.String(length=128), nullable=True))
    op.add_column("finding", sa.Column("fingerprint", sa.String(length=64), nullable=True))
    op.add_column(
        "finding",
        sa.Column(
            "qualification_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_finding_analysis_run",
        "finding",
        "analysis_run",
        ["analysis_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_finding_analysis_result",
        "finding",
        "analysis_result",
        ["analysis_result_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_finding_total_score_range",
        "finding",
        "total_score is null or total_score between 0 and 100",
    )
    op.create_unique_constraint(
        "uq_finding_run_fingerprint", "finding", ["analysis_run_id", "fingerprint"]
    )

    op.create_table(
        "finding_score_component",
        sa.Column("finding_id", sa.UUID(), nullable=False),
        sa.Column("component_code", sa.String(length=64), nullable=False),
        sa.Column("raw_value", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.Column("normalized_score", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("weight", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("weighted_score", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column(
            "calculation_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        *_identity_columns(),
        sa.CheckConstraint(
            "normalized_score between 0 and 100",
            name="ck_finding_score_normalized_range",
        ),
        sa.CheckConstraint("weight between 0 and 1", name="ck_finding_score_weight_range"),
        sa.CheckConstraint(
            "weighted_score between 0 and 100", name="ck_finding_score_weighted_range"
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["finding.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "finding_id", "component_code", name="uq_finding_score_component_code"
        ),
    )

    op.add_column(
        "driver_contribution",
        sa.Column(
            "calculation_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.alter_column(
        "driver_contribution",
        "contribution_ratio",
        existing_type=sa.Numeric(precision=12, scale=4),
        type_=sa.Numeric(precision=16, scale=6),
        nullable=True,
    )
    op.drop_constraint("ck_evidence_object_type", "evidence", type_="check")
    op.alter_column(
        "evidence",
        "object_id",
        existing_type=sa.String(length=128),
        type_=sa.String(length=256),
        existing_nullable=False,
    )
    op.add_column("evidence", sa.Column("evidence_digest", sa.String(length=64)))
    op.add_column(
        "evidence",
        sa.Column(
            "verification_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_evidence_object_type",
        "evidence",
        "object_type in ('metric', 'finding', 'evidence', 'source_record', "
        "'analysis_run', 'analysis_result', 'canonical_record_set', 'lineage', 'invariant')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_evidence_object_type", "evidence", type_="check")
    op.drop_column("evidence", "verification_trace")
    op.drop_column("evidence", "evidence_digest")
    op.alter_column(
        "evidence",
        "object_id",
        existing_type=sa.String(length=256),
        type_=sa.String(length=128),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_evidence_object_type",
        "evidence",
        "object_type in ('metric', 'finding', 'evidence', 'source_record')",
    )
    op.alter_column(
        "driver_contribution",
        "contribution_ratio",
        existing_type=sa.Numeric(precision=16, scale=6),
        type_=sa.Numeric(precision=12, scale=4),
        nullable=False,
    )
    op.drop_column("driver_contribution", "calculation_trace")
    op.drop_table("finding_score_component")
    op.drop_constraint("uq_finding_run_fingerprint", "finding", type_="unique")
    op.drop_constraint("ck_finding_total_score_range", "finding", type_="check")
    op.drop_constraint("fk_finding_analysis_result", "finding", type_="foreignkey")
    op.drop_constraint("fk_finding_analysis_run", "finding", type_="foreignkey")
    op.drop_column("finding", "qualification_trace")
    op.drop_column("finding", "fingerprint")
    op.drop_column("finding", "policy_version")
    op.drop_column("finding", "total_score")
    op.drop_column("finding", "comparison_basis")
    op.drop_column("finding", "fact_statement")
    op.drop_column("finding", "finding_type")
    op.drop_column("finding", "analysis_result_id")
    op.drop_column("finding", "analysis_run_id")
    op.drop_table("analysis_driver")
    op.drop_table("analysis_result")
    op.drop_table("analysis_run")
