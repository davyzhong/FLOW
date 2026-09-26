"""Build and validate the versioned synthetic enterprise data package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/enterprise/damai-logistics/v1"
SOURCE = ROOT / "fixtures/damai"


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def permissions() -> list[dict]:
    sys.path.insert(0, str(ROOT / "services/api/src"))
    from flow_api.security.authorization import (
        _AI_ANALYST_ALLOW,
        _AI_CFO_ALLOW,
        _ANALYST_FORBIDDEN_OVERRIDE,
        _FINANCE_BP_ALLOW,
        _RULE_OWNER_ALLOW,
        _SERVICE_ACCOUNT_ALLOW,
        Action,
    )

    all_actions = set(Action)
    role_actions = {
        "finance_bp": _FINANCE_BP_ALLOW,
        "analyst": all_actions - _ANALYST_FORBIDDEN_OVERRIDE,
        "rule_owner": _RULE_OWNER_ALLOW,
        "ai_analyst": _AI_ANALYST_ALLOW,
        "ai_cfo": _AI_CFO_ALLOW,
        "service_account": _SERVICE_ACCOUNT_ALLOW,
    }
    return [
        {
            "role_code": role,
            "action": action.value,
            "expected": "allow",
            "source": "flow_api.security.authorization",
            "synthetic": True,
        }
        for role, actions in role_actions.items()
        for action in sorted(actions, key=lambda item: item.value)
    ]


def validate_organization(
    package: Path = PACKAGE, enterprise_code: str = "damai-logistics"
) -> None:
    org_dir = package / "organization"
    departments = read_jsonl(org_dir / "departments.jsonl")
    positions = read_jsonl(org_dir / "positions.jsonl")
    roles = read_jsonl(org_dir / "roles.jsonl")
    users = read_jsonl(org_dir / "users.jsonl")
    errors: list[str] = []
    forbidden_identity_keys = {
        "password",
        "token",
        "secret",
        "credential",
        "api_key",
        "private_key",
        "national_id",
        "id_card",
        "ssn",
        "government_id",
    }

    def inspect_sensitive_fields(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in forbidden_identity_keys:
                    errors.append(f"身份记录包含禁止字段: {path}.{key}")
                inspect_sensitive_fields(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect_sensitive_fields(child, f"{path}[{index}]")

    for filename, rows in (
        ("departments.jsonl", departments),
        ("positions.jsonl", positions),
        ("roles.jsonl", roles),
        ("users.jsonl", users),
    ):
        for row in rows:
            inspect_sensitive_fields(row, f"{filename}:{row.get('code', row.get('actor_id', '?'))}")

    codes = {row["code"] for row in departments}
    role_codes = {row["code"] for row in roles}
    position_codes = {row["code"] for row in positions}
    actor_ids: set[str] = set()
    employee_codes: set[str] = set()
    for row in departments:
        if not row.get("synthetic"):
            errors.append(f"组织非合成: {row['code']}")
        if row.get("parent_code") and row["parent_code"] not in codes:
            errors.append(f"组织父级不存在: {row['code']}")
        if row.get("unit_type") not in {"group", "department", "business_unit", "team"}:
            errors.append(f"组织单元类型无效: {row['code']}")
    for row in positions:
        if row["org_unit_code"] not in codes:
            errors.append(f"岗位组织不存在: {row['code']}")
        if not row.get("synthetic"):
            errors.append(f"岗位非合成: {row['code']}")
    for row in users:
        for key, seen in (("actor_id", actor_ids), ("employee_code", employee_codes)):
            if row[key] in seen:
                errors.append(f"重复 {key}: {row[key]}")
            seen.add(row[key])
        if row["org_unit_code"] not in codes or row["position_code"] not in position_codes:
            errors.append(f"用户组织或岗位引用不存在: {row['actor_id']}")
        if row["role_code"] not in role_codes:
            errors.append(f"用户角色不存在: {row['actor_id']}")
        if row.get("supervisor_actor_id") and row["supervisor_actor_id"] not in {
            u["actor_id"] for u in users
        }:
            errors.append(f"用户上级不存在: {row['actor_id']}")
        if not row.get("synthetic"):
            errors.append(f"用户非合成: {row['actor_id']}")
        if not str(row["actor_id"]).startswith(f"{enterprise_code}:"):
            errors.append(f"用户 actor_id 未使用企业命名空间: {row['actor_id']}")
        if row.get("email") and not row["email"].endswith(".example.invalid"):
            errors.append(f"非保留邮箱域: {row['actor_id']}")
        if row.get("identity_kind") not in {"human", "ai", "service"}:
            errors.append(f"用户身份类型无效: {row['actor_id']}")
        role_definition = next(
            (role for role in roles if role.get("system_role") == row.get("role_code")), None
        )
        if role_definition and role_definition.get("identity_kind") != row.get("identity_kind"):
            errors.append(f"用户身份类型与系统角色不匹配: {row['actor_id']}")
    for row in roles:
        if not row.get("synthetic"):
            errors.append(f"角色记录非合成: {row['code']}")
        if row.get("system_role") not in {
            "finance_bp",
            "analyst",
            "rule_owner",
            "ai_analyst",
            "ai_cfo",
            "service_account",
        }:
            errors.append(f"未知系统角色: {row['code']}")
    permission_path = org_dir / "permissions.jsonl"
    if permission_path.exists():
        sys.path.insert(0, str(ROOT / "services/api/src"))
        from flow_api.security.authorization import Action

        role_codes = {str(row.get("system_role")) for row in roles}
        seen_permissions: set[tuple[str, str]] = set()
        known_actions = {action.value for action in Action}
        for row in read_jsonl(permission_path):
            pair = (str(row.get("role_code")), str(row.get("action")))
            if pair in seen_permissions:
                errors.append(f"重复权限映射: {pair[0]} / {pair[1]}")
            seen_permissions.add(pair)
            if pair[0] not in role_codes:
                errors.append(f"权限映射引用未知系统角色: {pair[0]}")
            if pair[1] not in known_actions:
                errors.append(f"权限映射引用未知 Action: {pair[1]}")
            if row.get("expected") != "allow" or row.get("synthetic") is not True:
                errors.append(f"权限映射必须是合成 allow 快照: {pair[0]} / {pair[1]}")
        expected_permissions = {
            (str(row["role_code"]), str(row["action"])) for row in permissions()
        }
        if seen_permissions != expected_permissions:
            missing = sorted(expected_permissions - seen_permissions)
            unexpected = sorted(seen_permissions - expected_permissions)
            if missing:
                errors.append(f"权限快照缺项: {missing[:8]}")
            if unexpected:
                errors.append(f"权限快照超出当前 RBAC: {unexpected[:8]}")
    business_orgs_path = package / "business/canonical/organizations.jsonl"
    if business_orgs_path.is_file():
        business_org_codes = {
            str(row["code"]) for row in read_jsonl(business_orgs_path)
        }
        missing_org_codes = sorted(business_org_codes - codes)
        if missing_org_codes:
            errors.append(
                "业务事实引用了组织包中不存在的 code: " + ", ".join(missing_org_codes)
            )
    if errors:
        raise SystemExit("组织数据校验失败:\n- " + "\n- ".join(errors))



def _sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return "'" + str(value).replace("'", "''") + "'"


def _topological(rows: list[dict], key: str, parent_key: str) -> list[dict]:
    pending = {str(row[key]): row for row in rows}
    ordered: list[dict] = []
    done: set[str] = set()
    while pending:
        ready = [
            row for row in pending.values()
            if row.get(parent_key) is None or str(row[parent_key]) in done
        ]
        if not ready:
            raise SystemExit(f"组织层级存在循环或无效上级: {sorted(pending)}")
        for row in ready:
            ordered.append(row)
            code = str(row[key])
            done.add(code)
            del pending[code]
    return ordered


def _generate_organization_sql(package: Path, enterprise_code: str) -> str:
    org = package / "organization"
    departments = _topological(read_jsonl(org / "departments.jsonl"), "code", "parent_code")
    positions = read_jsonl(org / "positions.jsonl")
    users = _topological(read_jsonl(org / "users.jsonl"), "actor_id", "supervisor_actor_id")
    lines = [
        "-- GENERATED from organization/*.jsonl by scripts/build_enterprise_data_package.py",
        "-- Run inside the initializer transaction after setting flow.enterprise_code",
    ]
    for row in departments:
        code = _sql_literal(row["code"])
        parent_join = ""
        parent_expr = "NULL"
        if row.get("parent_code"):
            parent_join = f" JOIN enterprise_org_unit parent ON parent.enterprise_id = e.id AND parent.code = {_sql_literal(row['parent_code'])}"
            parent_expr = "parent.id"
        unit_type = "business_unit" if row["unit_type"] == "group" else row["unit_type"]
        lines.append(
            "INSERT INTO enterprise_org_unit (enterprise_id, code, name, unit_type, parent_id, status, attributes) "
            f"SELECT e.id, {code}, {_sql_literal(row['name'])}, {_sql_literal(unit_type)}, {parent_expr}, 'active', '{{\"synthetic\": true}}'::jsonb "
            f"FROM enterprise e{parent_join} WHERE e.code = current_setting('flow.enterprise_code', true) "
            "ON CONFLICT (enterprise_id, code) DO UPDATE SET name = EXCLUDED.name, unit_type = EXCLUDED.unit_type, "
            "parent_id = EXCLUDED.parent_id, status = 'active', attributes = EXCLUDED.attributes;"
        )
    unit_codes = ", ".join(_sql_literal(row["code"]) for row in departments)
    lines.append(
        "UPDATE enterprise_org_unit SET status = 'inactive' WHERE enterprise_id = "
        "(SELECT id FROM enterprise WHERE code = current_setting('flow.enterprise_code', true)) "
        f"AND code NOT IN ({unit_codes});"
    )
    for row in positions:
        lines.append(
            "INSERT INTO enterprise_position (enterprise_id, org_unit_id, code, title, job_family, level, status) "
            f"SELECT e.id, o.id, {_sql_literal(row['code'])}, {_sql_literal(row['title'])}, "
            f"{_sql_literal(row['job_family'])}, {_sql_literal(row['level'])}, 'active' "
            "FROM enterprise e JOIN enterprise_org_unit o ON o.enterprise_id = e.id "
            f"AND o.code = {_sql_literal(row['org_unit_code'])} "
            "WHERE e.code = current_setting('flow.enterprise_code', true) "
            "ON CONFLICT (enterprise_id, code) DO UPDATE SET org_unit_id = EXCLUDED.org_unit_id, "
            "title = EXCLUDED.title, job_family = EXCLUDED.job_family, level = EXCLUDED.level, status = 'active';"
        )
    position_codes = ", ".join(_sql_literal(row["code"]) for row in positions)
    lines.append(
        "UPDATE enterprise_position SET status = 'inactive' WHERE enterprise_id = "
        "(SELECT id FROM enterprise WHERE code = current_setting('flow.enterprise_code', true)) "
        f"AND code NOT IN ({position_codes});"
    )
    for row in users:
        metadata = json.dumps({"synthetic": True, "package": "damai-logistics/v1"}, separators=(",", ":"))
        supervisor_join = ""
        supervisor_expr = "NULL"
        if row.get("supervisor_actor_id"):
            supervisor_join = f" JOIN enterprise_member supervisor ON supervisor.enterprise_id = e.id AND supervisor.actor_id = {_sql_literal(row['supervisor_actor_id'])}"
            supervisor_expr = "supervisor.actor_id"
        lines.append(
            "INSERT INTO enterprise_member (enterprise_id, actor_id, employee_code, display_name, email, phone, "
            "org_unit_id, position_id, supervisor_actor_id, identity_metadata, identity_kind, status) "
            f"SELECT e.id, {_sql_literal(row['actor_id'])}, {_sql_literal(row['employee_code'])}, {_sql_literal(row['display_name'])}, "
            f"{_sql_literal(row.get('email'))}, {_sql_literal(row.get('phone'))}, o.id, p.id, {supervisor_expr}, "
            f"{_sql_literal(metadata)}::jsonb, {_sql_literal(row['identity_kind'])}, 'active' "
            "FROM enterprise e JOIN enterprise_org_unit o ON o.enterprise_id = e.id "
            f"AND o.code = {_sql_literal(row['org_unit_code'])} "
            "JOIN enterprise_position p ON p.enterprise_id = e.id "
            f"AND p.code = {_sql_literal(row['position_code'])}{supervisor_join} "
            "WHERE e.code = current_setting('flow.enterprise_code', true) "
            "ON CONFLICT (enterprise_id, actor_id) DO UPDATE SET employee_code = EXCLUDED.employee_code, "
            "display_name = EXCLUDED.display_name, email = EXCLUDED.email, phone = EXCLUDED.phone, "
            "org_unit_id = EXCLUDED.org_unit_id, position_id = EXCLUDED.position_id, "
            "supervisor_actor_id = EXCLUDED.supervisor_actor_id, identity_metadata = EXCLUDED.identity_metadata, "
            "identity_kind = EXCLUDED.identity_kind, status = 'active';"
        )
        is_service = row["identity_kind"] == "service"
        lines.append(
            "UPDATE role_binding SET active = FALSE, revoked_at = now() "
            f"WHERE actor_id = {_sql_literal(row['actor_id'])} AND active IS TRUE "
            "AND enterprise_id = (SELECT id FROM enterprise WHERE code = current_setting('flow.enterprise_code', true)) "
            f"AND (role <> {_sql_literal(row['role_code'])} OR is_service_account <> {_sql_literal(is_service)});"
        )
        lines.append(
            "INSERT INTO role_binding (actor_id, role, enterprise_id, is_service_account, active) "
            f"SELECT {_sql_literal(row['actor_id'])}, {_sql_literal(row['role_code'])}, e.id, {_sql_literal(is_service)}, TRUE "
            "FROM enterprise e WHERE e.code = current_setting('flow.enterprise_code', true) "
            "AND NOT EXISTS (SELECT 1 FROM role_binding b WHERE b.actor_id = "
            f"{_sql_literal(row['actor_id'])} AND b.active IS TRUE);"
        )
    actor_ids = ", ".join(_sql_literal(row["actor_id"]) for row in users)
    lines.extend([
        (
            "UPDATE enterprise_member SET status = 'inactive' WHERE enterprise_id = "
            "(SELECT id FROM enterprise WHERE code = current_setting('flow.enterprise_code', true)) "
            f"AND actor_id NOT IN ({actor_ids});"
        ),
        (
            "UPDATE role_binding SET active = FALSE, revoked_at = now() WHERE active IS TRUE "
            "AND enterprise_id = (SELECT id FROM enterprise WHERE code = current_setting('flow.enterprise_code', true)) "
            f"AND left(actor_id, length({_sql_literal(enterprise_code + ':')})) = "
            f"{_sql_literal(enterprise_code + ':')} AND actor_id NOT IN ({actor_ids});"
        ),
    ])
    return "\n".join(lines) + "\n"

def build() -> dict:
    if not SOURCE.is_dir():
        raise SystemExit(f"业务源目录不存在: {SOURCE}")
    business = PACKAGE / "business"
    business.mkdir(parents=True, exist_ok=True)
    for source_dir in ("canonical", "statements", "operations", "forecast", "workbooks"):
        shutil.copytree(SOURCE / source_dir, business / source_dir, dirs_exist_ok=True)
    write_jsonl(PACKAGE / "organization/permissions.jsonl", permissions())
    validate_organization(PACKAGE)
    (PACKAGE / "sql/10_organization.sql").write_text(
        _generate_organization_sql(PACKAGE, "damai-logistics"), encoding="utf-8"
    )

    files: dict[str, dict[str, object]] = {}
    for path in sorted(
        p for p in PACKAGE.rglob("*") if p.is_file() and p != PACKAGE / "manifest.json"
    ):
        data = path.read_bytes()
        key = path.relative_to(PACKAGE).as_posix()
        entry: dict[str, object] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        if path.suffix == ".jsonl":
            entry["rows"] = sum(1 for line in data.splitlines() if line.strip())
        files[key] = entry
    manifest = {
        "package_id": "damai-logistics",
        "package_version": "1.0.0",
        "enterprise_code": "damai-logistics",
        "enterprise_name": "大麦物流集团",
        "synthetic": True,
        "contract_version": "flow.enterprise-package.v1",
        "modules": {"organization": "1.0.0", "business": "1.0.0"},
        "system_dependencies": {
            "rbac_source": "services/api/src/flow_api/security/authorization.py",
            "business_source": "fixtures/damai",
        },
        "source_manifest_sha256": hashlib.sha256(
            (SOURCE / "manifest.json").read_bytes()
        ).hexdigest(),
        "files": files,
    }
    (PACKAGE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def verify() -> dict:
    manifest_path = PACKAGE / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"manifest 无法读取: {exc}") from exc
    errors: list[str] = []
    if manifest.get("synthetic") is not True:
        errors.append("拒绝非 synthetic 企业包")
    if manifest.get("contract_version") != "flow.enterprise-package.v1":
        errors.append(f"不支持的企业包 contract_version: {manifest.get('contract_version')!r}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", str(manifest.get("package_id", ""))):
        errors.append("package_id 缺失或格式无效")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("package_version", ""))):
        errors.append("package_version 缺失或格式无效")
    enterprise_code = str(manifest.get("enterprise_code", ""))
    if not enterprise_code or enterprise_code != manifest.get("package_id"):
        errors.append("enterprise_code 必须存在且与 package_id 一致")
    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("manifest.files 必须是对象")
        files = {}
    expected_paths: set[str] = set()
    for key, expected in files.items():
        relative = PurePosixPath(str(key))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            errors.append(f"manifest 含越界文件路径: {key}")
            continue
        path = (PACKAGE / Path(*relative.parts)).resolve()
        try:
            path.relative_to(PACKAGE.resolve())
        except ValueError:
            errors.append(f"manifest 文件路径逃逸包目录: {key}")
            continue
        expected_paths.add(relative.as_posix())
        if not path.is_file():
            errors.append(f"缺失文件: {key}")
            continue
        content = path.read_bytes()
        if not isinstance(expected, dict):
            errors.append(f"manifest 文件条目格式无效: {key}")
            continue
        if hashlib.sha256(content).hexdigest() != expected.get("sha256"):
            errors.append(f"SHA256 不符: {key}")
        if len(content) != expected.get("bytes"):
            errors.append(f"字节数不符: {key}")
        if (
            "rows" in expected
            and sum(1 for line in content.splitlines() if line.strip()) != expected["rows"]
        ):
            errors.append(f"行数不符: {key}")
    actual_paths = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual_paths != expected_paths:
        for key in sorted(actual_paths - expected_paths):
            errors.append(f"文件未纳入 manifest: {key}")
        for key in sorted(expected_paths - actual_paths):
            errors.append(f"manifest 登记了不存在的文件: {key}")
    try:
        validate_organization(PACKAGE, enterprise_code)
        organization_sql = PACKAGE / "sql/10_organization.sql"
        if not organization_sql.is_file():
            errors.append("缺失生成的组织初始化 SQL: sql/10_organization.sql")
        elif organization_sql.read_text(encoding="utf-8") != _generate_organization_sql(
            PACKAGE, enterprise_code
        ):
            errors.append("组织初始化 SQL 与 organization/*.jsonl 不一致，请重新 build")
    except SystemExit as exc:
        errors.append(str(exc))
    if errors:
        raise SystemExit("数据包校验失败:\n- " + "\n- ".join(errors))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    args = parser.parse_args()
    manifest = build() if args.action == "build" else verify()
    print(
        f"数据包 {manifest['package_id']} v{manifest['package_version']}: "
        f"{len(manifest['files'])} 个文件校验通过"
    )
    organization_dir = PACKAGE / "organization"
    counts = {
        "部门/单元": len(read_jsonl(organization_dir / "departments.jsonl")),
        "岗位": len(read_jsonl(organization_dir / "positions.jsonl")),
        "身份": len(read_jsonl(organization_dir / "users.jsonl")),
        "权限映射": len(read_jsonl(organization_dir / "permissions.jsonl")),
    }
    print("组织样本: " + ", ".join(f"{count} {label}" for label, count in counts.items()))


if __name__ == "__main__":
    main()
