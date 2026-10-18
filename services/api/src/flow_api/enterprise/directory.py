"""Validate and load a versioned enterprise organization package."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from flow_api.enterprise.models import Enterprise
from flow_api.infrastructure.models.enterprise_directory import (
    EnterpriseMember,
    EnterpriseOrgUnit,
    EnterprisePosition,
)
from flow_api.security.models import RoleBinding


def _rows(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def _ensure_package_refs(
    org_dir: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    departments = _rows(org_dir / "departments.jsonl")
    positions = _rows(org_dir / "positions.jsonl")
    roles = _rows(org_dir / "roles.jsonl")
    users = _rows(org_dir / "users.jsonl")
    department_codes = {str(row["code"]) for row in departments}
    position_codes = {str(row["code"]) for row in positions}
    role_codes = {str(row["code"]) for row in roles}
    if len(department_codes) != len(departments) or len(position_codes) != len(positions):
        raise ValueError("组织包含重复部门或岗位 code")
    user_ids = {str(row["actor_id"]) for row in users}
    employee_codes = {str(row["employee_code"]) for row in users}
    if len(user_ids) != len(users) or len(employee_codes) != len(users):
        raise ValueError("组织包包含重复 actor_id 或 employee_code")
    for row in departments:
        parent = row.get("parent_code")
        if parent and str(parent) not in department_codes:
            raise ValueError(f"部门 {row['code']} 引用了不存在的上级 {parent}")
    for row in positions:
        if str(row["org_unit_code"]) not in department_codes:
            raise ValueError(f"岗位 {row['code']} 引用了不存在的组织单元")
    for row in users:
        actor = str(row["actor_id"])
        if not row.get("synthetic"):
            raise ValueError(f"拒绝导入非合成成员 {actor}")
        if (
            str(row["org_unit_code"]) not in department_codes
            or str(row["position_code"]) not in position_codes
        ):
            raise ValueError(f"成员 {actor} 引用了不存在的组织或岗位")
        if str(row["role_code"]) not in role_codes:
            raise ValueError(f"成员 {actor} 引用了不存在的角色")
        email = row.get("email")
        if email and not str(email).endswith(".example.invalid"):
            raise ValueError(f"成员 {actor} 的邮箱不属于保留域")
        supervisor = row.get("supervisor_actor_id")
        if supervisor and str(supervisor) not in user_ids:
            raise ValueError(f"成员 {actor} 引用了不存在的主管")
    return departments, positions, users


def _repository_root() -> Path:
    for root in (Path.cwd(), *Path.cwd().parents):
        if (root / "templates/excel/flow_v1_contract.yaml").is_file():
            return root
    raise FileNotFoundError("未找到 FLOW 仓库根目录")


def sync_enterprise_directory(
    session: Session, enterprise_id: UUID, organization_dir: Path
) -> dict[str, int]:
    """Validate package identities then execute generated SQL in the caller transaction."""
    enterprise = session.get(Enterprise, enterprise_id)
    if enterprise is None:
        raise ValueError(f"目标企业不存在: {enterprise_id}")
    root = _repository_root()
    expected_dir = root / "data/enterprise/damai-logistics/v2/organization"
    if organization_dir.resolve() != expected_dir.resolve():
        raise ValueError("组织 SQL 与输入目录不一致；请先通过数据包构建器重新生成发行文件")
    departments, positions, users = _ensure_package_refs(organization_dir)
    from flow_api.security.principal import Role

    role_kinds = {
        "human": {Role.FINANCE_BP.value, Role.ANALYST.value, Role.RULE_OWNER.value},
        "ai": {Role.AI_ANALYST.value, Role.AI_CFO.value},
        "service": {Role.SERVICE_ACCOUNT.value},
    }
    actor_ids = [str(row["actor_id"]) for row in users]
    for user in users:
        if str(user["role_code"]) not in role_kinds[str(user["identity_kind"])]:
            raise ValueError(f"成员角色与身份类型不匹配: {user['actor_id']}")
    bindings = session.scalars(
        select(RoleBinding).where(RoleBinding.actor_id.in_(actor_ids), RoleBinding.active.is_(True))
    ).all()
    conflicts = [row.actor_id for row in bindings if row.enterprise_id != enterprise_id]
    if conflicts:
        raise ValueError("模拟 actor 已绑定到其他企业，拒绝跨企业写入: " + ", ".join(conflicts))

    if session.get_bind().dialect.name == "sqlite":
        _sync_directory_rows(
            session,
            enterprise_id,
            departments=departments,
            positions=positions,
            users=users,
        )
    else:
        connection = session.connection()
        connection.execute(
            text("SELECT set_config('flow.enterprise_code', :code, true)"),
            {"code": enterprise.code},
        )
        sql_path = root / "data/enterprise/damai-logistics/v2/sql/10_organization.sql"
        for line in sql_path.read_text(encoding="utf-8").splitlines():
            statement = line.strip()
            if statement and not statement.startswith("--"):
                if not statement.endswith(";"):
                    raise RuntimeError("组织 seed SQL 每条语句都必须以分号结尾")
                connection.exec_driver_sql(statement[:-1])
    session.flush()
    return {"org_units": len(departments), "positions": len(positions), "members": len(users)}


def _sync_directory_rows(
    session: Session,
    enterprise_id: UUID,
    *,
    departments: list[dict[str, object]],
    positions: list[dict[str, object]],
    users: list[dict[str, object]],
) -> None:
    """通过 ORM 按包内 JSONL 对账组织数据，兼容 SQLite 与 PostgreSQL。"""

    units_by_code: dict[str, EnterpriseOrgUnit] = {}
    for row in departments:
        code = str(row["code"])
        parent_code = row.get("parent_code")
        parent_id = units_by_code[str(parent_code)].id if parent_code else None
        unit_type = "business_unit" if row["unit_type"] == "group" else str(row["unit_type"])
        unit = session.scalar(
            select(EnterpriseOrgUnit).where(
                EnterpriseOrgUnit.enterprise_id == enterprise_id,
                EnterpriseOrgUnit.code == code,
            )
        )
        if unit is None:
            unit = EnterpriseOrgUnit(
                enterprise_id=enterprise_id,
                code=code,
                name=str(row["name"]),
                unit_type=unit_type,
                parent_id=parent_id,
                status=str(row.get("status", "active")),
                attributes={"synthetic": True},
            )
            session.add(unit)
        else:
            unit.name = str(row["name"])
            unit.unit_type = unit_type
            unit.parent_id = parent_id
            unit.status = str(row.get("status", "active"))
            unit.attributes = {"synthetic": True}
        session.flush()
        units_by_code[code] = unit

    expected_unit_codes = set(units_by_code)
    for unit in session.scalars(
        select(EnterpriseOrgUnit).where(EnterpriseOrgUnit.enterprise_id == enterprise_id)
    ):
        if unit.code not in expected_unit_codes:
            unit.status = "inactive"

    positions_by_code: dict[str, EnterprisePosition] = {}
    for row in positions:
        code = str(row["code"])
        position = session.scalar(
            select(EnterprisePosition).where(
                EnterprisePosition.enterprise_id == enterprise_id,
                EnterprisePosition.code == code,
            )
        )
        fields = {
            "org_unit_id": units_by_code[str(row["org_unit_code"])].id,
            "title": str(row["title"]),
            "job_family": str(row["job_family"]),
            "level": str(row["level"]),
            "status": str(row.get("status", "active")),
        }
        if position is None:
            position = EnterprisePosition(enterprise_id=enterprise_id, code=code, **fields)
            session.add(position)
        else:
            for name, value in fields.items():
                setattr(position, name, value)
        session.flush()
        positions_by_code[code] = position

    expected_position_codes = set(positions_by_code)
    for position in session.scalars(
        select(EnterprisePosition).where(EnterprisePosition.enterprise_id == enterprise_id)
    ):
        if position.code not in expected_position_codes:
            position.status = "inactive"

    expected_actor_ids = {str(row["actor_id"]) for row in users}
    for row in users:
        actor_id = str(row["actor_id"])
        member = session.scalar(
            select(EnterpriseMember).where(
                EnterpriseMember.enterprise_id == enterprise_id,
                EnterpriseMember.actor_id == actor_id,
            )
        )
        fields = {
            "employee_code": str(row["employee_code"]),
            "display_name": str(row["display_name"]),
            "email": str(row["email"]) if row.get("email") else None,
            "phone": str(row["phone"]) if row.get("phone") else None,
            "org_unit_id": units_by_code[str(row["org_unit_code"])].id,
            "position_id": positions_by_code[str(row["position_code"])].id,
            "supervisor_actor_id": (
                str(row["supervisor_actor_id"]) if row.get("supervisor_actor_id") else None
            ),
            "identity_metadata": {"synthetic": True, "package": "damai-logistics/v1"},
            "identity_kind": str(row["identity_kind"]),
            "status": str(row.get("status", "active")),
        }
        if member is None:
            member = EnterpriseMember(enterprise_id=enterprise_id, actor_id=actor_id, **fields)
            session.add(member)
        else:
            for name, value in fields.items():
                setattr(member, name, value)
        session.flush()

        role = str(row["role_code"])
        is_service_account = row["identity_kind"] == "service"
        active_bindings = session.scalars(
            select(RoleBinding).where(
                RoleBinding.actor_id == actor_id,
                RoleBinding.active.is_(True),
            )
        ).all()
        matching = False
        for binding in active_bindings:
            if (
                binding.enterprise_id == enterprise_id
                and binding.role == role
                and binding.is_service_account is is_service_account
            ):
                matching = True
            else:
                binding.active = False
                binding.revoked_at = datetime.now(UTC)
        if not matching and row.get("status") == "active":
            session.add(
                RoleBinding(
                    actor_id=actor_id,
                    role=role,
                    enterprise_id=enterprise_id,
                    is_service_account=is_service_account,
                    active=True,
                )
            )
        session.flush()

    for member in session.scalars(
        select(EnterpriseMember).where(EnterpriseMember.enterprise_id == enterprise_id)
    ):
        if (
            member.actor_id.startswith("damai-logistics:")
            and member.actor_id not in expected_actor_ids
        ):
            member.status = "inactive"
    for binding in session.scalars(
        select(RoleBinding).where(
            RoleBinding.enterprise_id == enterprise_id,
            RoleBinding.active.is_(True),
        )
    ):
        if (
            binding.actor_id.startswith("damai-logistics:")
            and binding.actor_id not in expected_actor_ids
        ):
            binding.active = False
            binding.revoked_at = datetime.now(UTC)


__all__ = ["sync_enterprise_directory"]
