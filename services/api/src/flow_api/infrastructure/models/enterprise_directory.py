"""企业组织目录、岗位与合成/业务成员信息。"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from flow_api.infrastructure.models.base import Base
from flow_api.infrastructure.models.canonical import CanonicalIdentityMixin


class EnterpriseOrgUnit(CanonicalIdentityMixin, Base):
    __tablename__ = "enterprise_org_unit"
    __table_args__ = (
        UniqueConstraint("enterprise_id", "code", name="uq_enterprise_org_unit_code"),
        UniqueConstraint("id", "enterprise_id", name="uq_enterprise_org_unit_id_enterprise"),
        ForeignKeyConstraint(
            ["parent_id", "enterprise_id"],
            ["enterprise_org_unit.id", "enterprise_org_unit.enterprise_id"],
            name="fk_enterprise_org_unit_parent_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "unit_type IN ('department', 'business_unit', 'team')",
            name="ck_enterprise_org_unit_type",
        ),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_enterprise_org_unit_status"),
    )

    enterprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("enterprise.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )


class EnterprisePosition(CanonicalIdentityMixin, Base):
    __tablename__ = "enterprise_position"
    __table_args__ = (
        UniqueConstraint("enterprise_id", "code", name="uq_enterprise_position_code"),
        UniqueConstraint("id", "enterprise_id", name="uq_enterprise_position_id_enterprise"),
        ForeignKeyConstraint(
            ["org_unit_id", "enterprise_id"],
            ["enterprise_org_unit.id", "enterprise_org_unit.enterprise_id"],
            name="fk_enterprise_position_org_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_enterprise_position_status"),
    )

    enterprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("enterprise.id", ondelete="RESTRICT"), nullable=False
    )
    org_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_family: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class EnterpriseMember(CanonicalIdentityMixin, Base):
    __tablename__ = "enterprise_member"
    __table_args__ = (
        UniqueConstraint("enterprise_id", "actor_id", name="uq_enterprise_member_actor"),
        UniqueConstraint("enterprise_id", "employee_code", name="uq_enterprise_member_employee"),
        ForeignKeyConstraint(
            ["org_unit_id", "enterprise_id"],
            ["enterprise_org_unit.id", "enterprise_org_unit.enterprise_id"],
            name="fk_enterprise_member_org_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["position_id", "enterprise_id"],
            ["enterprise_position.id", "enterprise_position.enterprise_id"],
            name="fk_enterprise_member_position_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["supervisor_actor_id", "enterprise_id"],
            ["enterprise_member.actor_id", "enterprise_member.enterprise_id"],
            name="fk_enterprise_member_supervisor_tenant",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "identity_kind IN ('human', 'ai', 'service')", name="ck_enterprise_member_identity_kind"
        ),
        CheckConstraint("status IN ('active', 'inactive')", name="ck_enterprise_member_status"),
        CheckConstraint(
            "identity_metadata ->> 'synthetic' = 'true'",
            name="ck_enterprise_member_synthetic",
        ),
    )

    enterprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("enterprise.id", ondelete="RESTRICT"), nullable=False
    )
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(32))
    org_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    position_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    supervisor_actor_id: Mapped[str | None] = mapped_column(String(128))
    identity_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    identity_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


__all__ = ["EnterpriseMember", "EnterpriseOrgUnit", "EnterprisePosition"]
