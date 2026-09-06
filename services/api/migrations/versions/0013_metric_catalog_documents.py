"""引擎指标目录文档库内化（P4，D040-4）：metric_catalog_document。

存整个引擎目录载荷（与 YAML 同构的 JSONB 文档），经同一
MetricCatalog.model_validate 加载，definition_set_hash 由模型计算，
因此库内文档与 YAML 双源加载的哈希按构造一致（由一致性门禁守护）。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_metric_catalog_documents"
down_revision: str | None = "0012_metric_library_objects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metric_catalog_document",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("definition_set_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "definition_set_id", "version", name="uq_metric_catalog_document_version"
        ),
        sa.CheckConstraint(
            "status in ('effective', 'retired')",
            name="ck_metric_catalog_document_status",
        ),
        sa.CheckConstraint("version > 0", name="ck_metric_catalog_document_version_positive"),
    )


def downgrade() -> None:
    op.drop_table("metric_catalog_document")
