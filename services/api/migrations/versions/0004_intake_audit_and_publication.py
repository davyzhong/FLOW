"""intake audit and publication lifecycle

Revision ID: 0004_intake_audit
Revises: 0003_analytics_and_publishing
Create Date: 2026-08-30 17:55:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_intake_audit"
down_revision: str | None = "0003_analytics_and_publishing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "mapping_version", sa.Column("mapping_hash", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "mapping_version",
        sa.Column(
            "confidence_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "mapping_version",
        sa.Column(
            "rationale_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_mapping_version_hash_length",
        "mapping_version",
        "mapping_hash is null or length(mapping_hash) = 64",
    )
    op.create_unique_constraint(
        "uq_mapping_version_batch_hash", "mapping_version", ["batch_id", "mapping_hash"]
    )

    op.add_column(
        "import_version",
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
    )
    op.create_check_constraint(
        "ck_import_version_status",
        "import_version",
        "status in ('draft', 'validating', 'blocked', 'ready', 'published')",
    )

    op.add_column(
        "source_record", sa.Column("transform_rule_id", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "source_record", sa.Column("transform_rule_version", sa.Integer(), nullable=True)
    )
    op.add_column("source_record", sa.Column("transform_reason", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_source_record_transform_rule_complete",
        "source_record",
        "(transform_rule_id is null and transform_rule_version is null) or "
        "(transform_rule_id is not null and transform_rule_version > 0)",
    )

    op.create_table(
        "warning_acknowledgement",
        sa.Column("quality_issue_id", sa.UUID(), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("length(btrim(actor)) > 0", name="ck_warning_ack_actor_nonempty"),
        sa.CheckConstraint("length(btrim(reason)) > 0", name="ck_warning_ack_reason_nonempty"),
        sa.ForeignKeyConstraint(
            ["quality_issue_id"], ["quality_issue.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quality_issue_id", name="uq_warning_ack_issue"),
    )
    op.execute(
        """
        create function flow_enforce_warning_acknowledgement()
        returns trigger as $$
        begin
          if not exists (
            select 1 from quality_issue
            where id = new.quality_issue_id and severity = 'warning'
          ) then
            raise exception 'only warning quality issues may be acknowledged';
          end if;
          return new;
        end;
        $$ language plpgsql
        """
    )
    op.execute(
        """
        create trigger trg_warning_acknowledgement_warning_only
        before insert or update on warning_acknowledgement
        for each row execute function flow_enforce_warning_acknowledgement()
        """
    )


def downgrade() -> None:
    op.execute(
        "drop trigger if exists trg_warning_acknowledgement_warning_only "
        "on warning_acknowledgement"
    )
    op.execute("drop function if exists flow_enforce_warning_acknowledgement()")
    op.drop_table("warning_acknowledgement")

    op.drop_constraint(
        "ck_source_record_transform_rule_complete", "source_record", type_="check"
    )
    op.drop_column("source_record", "transform_reason")
    op.drop_column("source_record", "transform_rule_version")
    op.drop_column("source_record", "transform_rule_id")

    op.drop_constraint("ck_import_version_status", "import_version", type_="check")
    op.drop_column("import_version", "status")

    op.drop_constraint("uq_mapping_version_batch_hash", "mapping_version", type_="unique")
    op.drop_constraint("ck_mapping_version_hash_length", "mapping_version", type_="check")
    op.drop_column("mapping_version", "rationale_summary")
    op.drop_column("mapping_version", "confidence_summary")
    op.drop_column("mapping_version", "mapping_hash")
