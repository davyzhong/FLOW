#!/usr/bin/env python3
"""Build and validate the versioned synthetic enterprise data package."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/enterprise/damai-logistics/v1"
SOURCE = ROOT / "fixtures/damai"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def permissions() -> list[dict]:
    sys.path.insert(0, str(ROOT / "services/api/src"))
    from flow_api.security.authorization import (
        Action,
        _AI_ANALYST_ALLOW,
        _AI_CFO_ALLOW,
        _ANALYST_FORBIDDEN_OVERRIDE,
        _FINANCE_BP_ALLOW,
        _RULE_OWNER_ALLOW,
        _SERVICE_ACCOUNT_ALLOW,
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
        {"role_code": role, "action": action.value, "expected": "allow", "source": "flow_api.security.authorization", "synthetic": True}
        for role, actions in role_actions.items()
        for action in sorted(actions, key=lambda item: item.value)
    ]


def validate_organization() -> None:
    org_dir = PACKAGE / "organization"
    departments = read_jsonl(org_dir / "departments.jsonl")
    positions = read_jsonl(org_dir / "positions.jsonl")
    roles = read_jsonl(org_dir / "roles.jsonl")
    users = read_jsonl(org_dir / "users.jsonl")
    errors: list[str] = []
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
        if row.get("supervisor_actor_id") and row["supervisor_actor_id"] not in {u["actor_id"] for u in users}:
            errors.append(f"用户上级不存在: {row['actor_id']}")
        if not row.get("synthetic"):
            errors.append(f"用户非合成: {row['actor_id']}")
        if row.get("email") and not row["email"].endswith(".example.invalid"):
            errors.append(f"非保留邮箱域: {row['actor_id']}")
    if errors:
        raise SystemExit("组织数据校验失败:\n- " + "\n- ".join(errors))


def build() -> dict:
    if not SOURCE.is_dir():
        raise SystemExit(f"业务源目录不存在: {SOURCE}")
    business = PACKAGE / "business"
    business.mkdir(parents=True, exist_ok=True)
    for source_dir in ("canonical", "statements", "operations", "forecast", "workbooks"):
        shutil.copytree(SOURCE / source_dir, business / source_dir, dirs_exist_ok=True)
    write_jsonl(PACKAGE / "organization/permissions.jsonl", permissions())
    validate_organization()

    files: dict[str, dict[str, object]] = {}
    for path in sorted(p for p in PACKAGE.rglob("*") if p.is_file() and p.name != "manifest.json"):
        data = path.read_bytes()
        key = path.relative_to(PACKAGE).as_posix()
        entry: dict[str, object] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        if path.suffix == ".jsonl":
            entry["rows"] = sum(1 for line in data.splitlines() if line.strip())
        files[key] = entry
    manifest = {
        "package_id": "damai-logistics",
        "package_version": "1.0.0",
        "enterprise_code": "DAMAI_LOGISTICS",
        "enterprise_name": "大麦物流集团",
        "synthetic": True,
        "contract_version": "flow.enterprise-package.v1",
        "modules": {"organization": "1.0.0", "business": "1.0.0"},
        "system_dependencies": {"rbac_source": "services/api/src/flow_api/security/authorization.py", "business_source": "fixtures/damai"},
        "source_manifest_sha256": hashlib.sha256((SOURCE / "manifest.json").read_bytes()).hexdigest(),
        "files": files,
    }
    (PACKAGE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify() -> dict:
    manifest_path = PACKAGE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("synthetic") is not True:
        raise SystemExit("拒绝非 synthetic 企业包")
    validate_organization()
    errors = []
    for key, expected in manifest["files"].items():
        path = PACKAGE / key
        if not path.is_file():
            errors.append(f"缺失文件: {key}")
            continue
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected["sha256"]:
            errors.append(f"SHA256 不符: {key}")
        if "rows" in expected and sum(1 for line in content.splitlines() if line.strip()) != expected["rows"]:
            errors.append(f"行数不符: {key}")
    if errors:
        raise SystemExit("数据包校验失败:\n- " + "\n- ".join(errors))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    args = parser.parse_args()
    manifest = build() if args.action == "build" else verify()
    print(f"数据包 {manifest['package_id']} v{manifest['package_version']}: {len(manifest['files'])} 个文件校验通过")
    print(f"组织样本: {len(read_jsonl(PACKAGE / 'organization/departments.jsonl'))} 部门/单元, {len(read_jsonl(PACKAGE / 'organization/positions.jsonl'))} 岗位, {len(read_jsonl(PACKAGE / 'organization/users.jsonl'))} 身份, {len(read_jsonl(PACKAGE / 'organization/permissions.jsonl'))} 权限映射")


if __name__ == "__main__":
    main()
