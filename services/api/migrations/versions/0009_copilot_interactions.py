"""add governed copilot interaction audit records

Revision ID: 0009_copilot_interactions
Revises: 0008_investigation_review
Create Date: 2026-09-02 04:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_copilot_interactions"
down_revision: str | None = "0008_investigation_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "copilot_interaction",
        sa.Column("finding_id", sa.UUID(), nullable=True),
        sa.Column("import_version_id", sa.UUID(), nullable=True),
        sa.Column("batch_id", sa.UUID(), nullable=True),
        sa.Column("use_case", sa.String(length=64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("template_version", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("context_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "request_references",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "response_payload",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column(
            "rejection_reasons",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["finding_id"], ["finding.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["import_version_id"], ["import_version.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"], ["analysis_batch.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "use_case in ('mapping_explanation', 'investigation_qa', 'report_outline')",
            name="ck_copilot_interaction_use_case",
        ),
        sa.CheckConstraint(
            "outcome in ('accepted', 'rejected')",
            name="ck_copilot_interaction_outcome",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("copilot_interaction")
