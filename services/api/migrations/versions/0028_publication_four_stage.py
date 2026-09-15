"""S01 R2：publication_attempt 四阶段发布合同列（§7）。

- `publication_id`（UUID7 批次标识，幂等/重试/对账锚点）、`idempotency_key`、
  `source_payload_sha256`（冻结输入 hash）、`object_key` / `content_sha256` /
  `size_bytes` / `content_type`（产物对账）、`error_code`（§7.5 错误分类）；
- status CHECK 扩展 §7.1 枚举：pending / succeeded / render_failed / store_failed
  （保留 legacy queued/running/failed 值，不迁移旧行）；
- 唯一约束从 (parent, sequence) 收紧为 (parent, sequence, format)——同批次
  多 format 并存；
- downgrade 完整还原（新列删除 + 旧约束重建；含四阶段新值的行先清除）。
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

revision: str = "0028_publication_four_stage"
down_revision: str | None = "0027_security_contract_fix"
branch_labels = None
depends_on = None

_OLD_STATUS_CK = "ck_publication_attempt_status"
_NEW_VALUES = (
    "'queued', 'running', 'succeeded', 'failed', 'pending', 'render_failed', 'store_failed'"
)
_OLD_VALUES = "'queued', 'running', 'succeeded', 'failed'"


def upgrade() -> None:
    op.add_column(
        "publication_attempt",
        sa.Column("publication_id", PG_UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("source_payload_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("object_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("content_type", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "publication_attempt",
        sa.Column("error_code", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_publication_attempt_publication_id",
        "publication_attempt",
        ["publication_id"],
    )
    op.create_check_constraint(
        "ck_publication_attempt_source_hash",
        "publication_attempt",
        "source_payload_sha256 IS NULL OR length(source_payload_sha256) = 64",
    )

    # status CHECK 扩展（drop 旧、建新）
    op.drop_constraint(_OLD_STATUS_CK, "publication_attempt", type_="check")
    op.create_check_constraint(
        _OLD_STATUS_CK,
        "publication_attempt",
        f"status in ({_NEW_VALUES})",
    )

    # 唯一约束收紧为含 format（drop 旧、建新）
    op.drop_constraint(
        "uq_publication_attempt_report_sequence", "publication_attempt", type_="unique"
    )
    op.drop_constraint(
        "uq_publication_attempt_objective_sequence", "publication_attempt", type_="unique"
    )
    op.create_unique_constraint(
        "uq_publication_attempt_report_sequence_format",
        "publication_attempt",
        ["report_snapshot_id", "sequence", "format"],
    )
    op.create_unique_constraint(
        "uq_publication_attempt_objective_sequence_format",
        "publication_attempt",
        ["objective_report_snapshot_id", "sequence", "format"],
    )


def downgrade() -> None:
    # 含四阶段新状态的行无法满足旧 CHECK：按 append-only 证据纪律，downgrade
    # 场景（开发回滚）清除这些行，保留 legacy 值行。
    op.execute(
        "DELETE FROM publication_attempt WHERE status IN ('pending', 'render_failed', 'store_failed')"
    )

    op.drop_constraint(
        "uq_publication_attempt_report_sequence_format",
        "publication_attempt",
        type_="unique",
    )
    op.drop_constraint(
        "uq_publication_attempt_objective_sequence_format",
        "publication_attempt",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_publication_attempt_report_sequence",
        "publication_attempt",
        ["report_snapshot_id", "sequence"],
    )
    op.create_unique_constraint(
        "uq_publication_attempt_objective_sequence",
        "publication_attempt",
        ["objective_report_snapshot_id", "sequence"],
    )

    op.drop_constraint(_OLD_STATUS_CK, "publication_attempt", type_="check")
    op.create_check_constraint(
        _OLD_STATUS_CK,
        "publication_attempt",
        f"status in ({_OLD_VALUES})",
    )

    op.drop_constraint(
        "ck_publication_attempt_source_hash", "publication_attempt", type_="check"
    )
    op.drop_index("ix_publication_attempt_publication_id", table_name="publication_attempt")
    for column in (
        "error_code",
        "content_type",
        "size_bytes",
        "content_sha256",
        "object_key",
        "source_payload_sha256",
        "idempotency_key",
        "publication_id",
    ):
        op.drop_column("publication_attempt", column)
