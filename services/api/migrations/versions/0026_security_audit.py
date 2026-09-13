"""S01 Task 2A：安全 schema — RoleBinding + AuditEvent + 拒 UPDATE/DELETE 触发器。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md（approved）。
- §3.1 RoleBinding 冻结字段（id/actor_id/role/enterprise_id/is_service_account/active/
  created_at/revoked_at）；partial unique constraint 保证每个 actor 最多一条 active；
  active=false 必须有 revoked_at，active=true 的 revoked_at 必须为空。
- §8.1 AuditEvent 字段（事件类型/actor/role/enterprise/scope/resource/action/decision/
  reason/correlation/request_id/model_boundary/artifact_refs/redacted_metadata/
  created_at/retention_class/retain_until）。
- §8.1 数据库 trigger 拒绝 AuditEvent UPDATE/DELETE。
- §10 down_revision = 0025_enterprise_cycle；只加不改。

非破坏性迁移；0024 基线 dump 必须可恢复，旧表字段不删不改。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0026_security_audit"
down_revision: str | None = "0025_enterprise_cycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -- §3.1 RoleBinding ---------------------------------------------------
    op.create_table(
        "role_binding",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "enterprise_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("is_service_account", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "role IN ('finance_bp','analyst','rule_owner','ai_analyst','ai_cfo','service_account')",
            name="ck_role_binding_role_enum",
        ),
        sa.CheckConstraint(
            "active = true AND revoked_at IS NULL OR active = false AND revoked_at IS NOT NULL",
            name="ck_role_binding_active_revoke_consistency",
        ),
    )
    # §3.1 partial unique：每个 actor 最多一条 active=true
    op.execute(
        "CREATE UNIQUE INDEX uq_role_binding_one_active_per_actor "
        "ON role_binding (actor_id) WHERE active = true"
    )
    op.create_index("ix_role_binding_enterprise_id", "role_binding", ["enterprise_id"])
    op.create_index("ix_role_binding_role", "role_binding", ["role"])

    # -- §8.1 AuditEvent ----------------------------------------------------
    op.create_table(
        "audit_event",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("actor_role", sa.String(length=32), nullable=True),
        sa.Column("enterprise_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_scope", sa.String(length=16), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=True),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("model_boundary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "artifact_refs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "redacted_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("retention_class", sa.String(length=32), nullable=False),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "decision IN ('allow','deny','error')", name="ck_audit_event_decision_enum"
        ),
        sa.CheckConstraint(
            "resource_scope IN ('public','enterprise')", name="ck_audit_event_resource_scope_enum"
        ),
    )
    op.create_index("ix_audit_event_actor_id", "audit_event", ["actor_id"])
    op.create_index("ix_audit_event_enterprise_id", "audit_event", ["enterprise_id"])
    op.create_index("ix_audit_event_correlation_id", "audit_event", ["correlation_id"])
    op.create_index("ix_audit_event_resource", "audit_event", ["resource_type", "resource_id"])
    op.create_index("ix_audit_event_retain_until", "audit_event", ["retain_until"])
    op.create_index("ix_audit_event_created_at", "audit_event", ["created_at"])

    # §8.1 数据库 trigger 拒绝 AuditEvent UPDATE/DELETE
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_event_reject_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_event is append-only (op=%, id=%)', TG_OP, COALESCE(OLD.id, NEW.id)
                USING ERRCODE = '42501';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_event_no_update
            BEFORE UPDATE ON audit_event
            FOR EACH ROW EXECUTE FUNCTION audit_event_reject_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_event_no_delete
            BEFORE DELETE ON audit_event
            FOR EACH ROW EXECUTE FUNCTION audit_event_reject_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_event_no_delete ON audit_event")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_event_no_update ON audit_event")
    op.execute("DROP FUNCTION IF EXISTS audit_event_reject_mutation()")
    op.drop_index("ix_audit_event_created_at", table_name="audit_event")
    op.drop_index("ix_audit_event_retain_until", table_name="audit_event")
    op.drop_index("ix_audit_event_resource", table_name="audit_event")
    op.drop_index("ix_audit_event_correlation_id", table_name="audit_event")
    op.drop_index("ix_audit_event_enterprise_id", table_name="audit_event")
    op.drop_index("ix_audit_event_actor_id", table_name="audit_event")
    op.drop_table("audit_event")

    op.drop_index("ix_role_binding_role", table_name="role_binding")
    op.drop_index("ix_role_binding_enterprise_id", table_name="role_binding")
    op.execute("DROP INDEX IF EXISTS uq_role_binding_one_active_per_actor")
    op.drop_table("role_binding")
