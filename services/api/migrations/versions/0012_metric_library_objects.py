"""指标库与会计基础对象落库（P3，D040/D047）。

五张表：
- metric_dictionary_entry  指标卡片（含口径裁决与依赖，depends 以数组存引用）
- accounting_standard      准则登记册
- accounting_subject       会计科目（版本化状态）
- entry_template           分录模板（行为 JSONB）
- statement_line_mapping   报表项目 ↔ 科目 ↔ 指标映射

设计约束：只读事实数据（来源为版本化 YAML 契约），变更走整版重导入
（dataset_version 幂等），不做行级 update；审计由导入记录承担。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_metric_library_objects"
down_revision: str | None = "0011_statement_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metric_dictionary_entry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dictionary_id", sa.String(length=64), nullable=False),
        sa.Column("collection", sa.String(length=32), nullable=False),
        sa.Column("metric_code", sa.String(length=96), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=32), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("formula_text", sa.String(length=512), nullable=False),
        sa.Column("formula", postgresql.JSONB(), nullable=False),
        sa.Column("unit", sa.String(length=32)),
        sa.Column("time_behavior", sa.String(length=32)),
        sa.Column("caliber", sa.Text()),
        sa.Column("default_caliber", sa.Text()),
        sa.Column("default_basis", sa.Text()),
        sa.Column("alternative_calibers", postgresql.JSONB()),
        sa.Column("source_cas", postgresql.JSONB()),
        sa.Column("source_ifrs", sa.Text()),
        sa.Column("depends_on", postgresql.JSONB()),
        sa.Column("decompositions", postgresql.JSONB()),
        sa.Column("aliases", postgresql.JSONB()),
        sa.Column("benchmark", sa.Text()),
        sa.Column("mpm", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reconciliation", sa.Text()),
        sa.Column("migrates_from", sa.String(length=255)),
        sa.Column("provenance", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "dictionary_id", "collection", "metric_code", "version",
            name="uq_metric_entry_identity",
        ),
        sa.CheckConstraint(
            "collection in ('general', 'logistics', 'operations')",
            name="ck_metric_entry_collection",
        ),
        sa.CheckConstraint(
            "status in ('draft', 'effective', 'retired')",
            name="ck_metric_entry_status",
        ),
    )

    op.create_table(
        "accounting_standard",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("standard_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("issuer", sa.String(length=128)),
        sa.Column("note", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("standard_id", name="uq_accounting_standard_id"),
    )

    op.create_table(
        "accounting_subject",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("balance_side", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("standard_ref", sa.Text()),
        sa.Column("code_note", sa.Text()),
        sa.Column("source_note", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("code", name="uq_accounting_subject_code"),
        sa.CheckConstraint(
            "status in ('current', 'added_2024', 'superseded')",
            name="ck_accounting_subject_status",
        ),
        sa.CheckConstraint(
            "category in ('资产', '负债', '共同', '所有者权益', '成本', '损益')",
            name="ck_accounting_subject_category",
        ),
    )

    op.create_table(
        "entry_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("template_id", sa.String(length=96), nullable=False),
        sa.Column("scenario", sa.String(length=255), nullable=False),
        sa.Column("business_context", sa.Text()),
        sa.Column("lines", postgresql.JSONB(), nullable=False),
        sa.Column("standard_ref", sa.Text()),
        sa.Column("related_metrics", postgresql.JSONB()),
        sa.Column("note", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("template_id", name="uq_entry_template_id"),
    )

    op.create_table(
        "statement_line_mapping",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", sa.String(length=96), nullable=False),
        sa.Column("cas_label", sa.String(length=255), nullable=False),
        sa.Column("ifrs_label", sa.Text()),
        sa.Column("subject_codes", postgresql.JSONB()),
        sa.Column("metric_codes", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("item_id", name="uq_statement_line_mapping_item"),
    )


def downgrade() -> None:
    op.drop_table("statement_line_mapping")
    op.drop_table("entry_template")
    op.drop_table("accounting_subject")
    op.drop_table("accounting_standard")
    op.drop_table("metric_dictionary_entry")
