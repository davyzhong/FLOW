"""按 SQLite 定标整数单位校验比例和评分范围。

Revision ID: sqlite0003
Revises: sqlite0002
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "sqlite0003"
down_revision = "sqlite0002"
branch_labels = None
depends_on = None

_CHECKS = {
    "finding": (
        {"ck_finding_confidence_range"},
        {"ck_finding_confidence_range_sqlite": "confidence between 0 and 10000"},
    ),
    "finding_score_component": (
        {
            "ck_finding_score_normalized_range",
            "ck_finding_score_weight_range",
            "ck_finding_score_weighted_range",
        },
        {
            "ck_finding_score_normalized_range_sqlite": (
                "normalized_score between 0 and 100000000"
            ),
            "ck_finding_score_weight_range_sqlite": "weight between 0 and 1000000",
            "ck_finding_score_weighted_range_sqlite": (
                "weighted_score between 0 and 100000000"
            ),
        },
    ),
}


def upgrade() -> None:
    _replace_checks(_CHECKS)


def downgrade() -> None:
    _replace_checks(
        {
            "finding": (
                set(_CHECKS["finding"][1]),
                {"ck_finding_confidence_range": "confidence between 0 and 1"},
            ),
            "finding_score_component": (
                set(_CHECKS["finding_score_component"][1]),
                {
                    "ck_finding_score_normalized_range": "normalized_score between 0 and 100",
                    "ck_finding_score_weight_range": "weight between 0 and 1",
                    "ck_finding_score_weighted_range": "weighted_score between 0 and 100",
                },
            ),
        }
    )


def _replace_checks(changes: dict[str, tuple[set[str], dict[str, str]]]) -> None:
    for table, (remove_names, add_checks) in changes.items():
        existing = {
            item["name"]
            for item in sa.inspect(op.get_bind()).get_check_constraints(table)
            if item.get("name")
        }
        to_remove = remove_names & existing
        to_add = {name: sql for name, sql in add_checks.items() if name not in existing}
        if not to_remove and not to_add:
            continue
        with op.batch_alter_table(table, recreate="always") as batch:
            for name in sorted(to_remove):
                batch.drop_constraint(name, type_="check")
            for name, sql in to_add.items():
                batch.create_check_constraint(name, sql)
