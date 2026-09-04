"""Persist report rendering payloads without fabricating legacy history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_frozen_reports"
down_revision: str | None = "0009_copilot_interactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("report_snapshot", sa.Column("frozen_view", postgresql.JSONB(), nullable=True))
    op.execute("""
        CREATE FUNCTION protect_frozen_report() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.frozen_view IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN
                RAISE EXCEPTION 'frozen reports are immutable';
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER report_snapshot_immutable BEFORE UPDATE ON report_snapshot
        FOR EACH ROW EXECUTE FUNCTION protect_frozen_report()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER report_snapshot_immutable ON report_snapshot")
    op.execute("DROP FUNCTION protect_frozen_report()")
    op.drop_column("report_snapshot", "frozen_view")
