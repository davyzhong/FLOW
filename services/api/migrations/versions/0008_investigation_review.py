"""extend review decisions with evidence-level outcomes

Revision ID: 0008_investigation_review
Revises: 0007_add_analysis_runs
Create Date: 2026-09-02 01:30:00

The downgrade intentionally performs no data cleanup: if evidence-level review
decisions exist, recreating the original constraint fails loudly, which is the
correct outcome for downgrading a live investigation history.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_investigation_review"
down_revision: str | None = "0007_add_analysis_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_DECISIONS = "decision in ('submitted', 'approved', 'rejected', 'returned')"
NEW_DECISIONS = (
    "decision in ('submitted', 'approved', 'rejected', 'returned', "
    "'evidence_verified', 'evidence_rejected')"
)


def upgrade() -> None:
    with op.batch_alter_table("review_event") as batch:
        batch.drop_constraint("ck_review_event_decision", type_="check")
        batch.create_check_constraint("ck_review_event_decision", sa.text(NEW_DECISIONS))


def downgrade() -> None:
    with op.batch_alter_table("review_event") as batch:
        batch.drop_constraint("ck_review_event_decision", type_="check")
        batch.create_check_constraint("ck_review_event_decision", sa.text(OLD_DECISIONS))
