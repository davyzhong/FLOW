from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_enterprise_data_package as package_builder


class EnterpriseDataPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.package = self.root / "package"
        self.package.mkdir()
        (self.package / "organization").mkdir()
        (self.package / "README.md").write_text("synthetic package\n", encoding="utf-8")
        self._write_jsonl(
            "organization/departments.jsonl",
            [
                {
                    "code": "DAMAI",
                    "name": "Synthetic Company",
                    "parent_code": None,
                    "unit_type": "group",
                    "synthetic": True,
                }
            ],
        )
        self._write_jsonl(
            "organization/positions.jsonl",
            [
                {
                    "code": "FIN",
                    "title": "Finance Partner",
                    "org_unit_code": "DAMAI",
                    "job_family": "finance",
                    "level": "professional",
                    "synthetic": True,
                }
            ],
        )
        self._write_jsonl(
            "organization/roles.jsonl",
            [
                {
                    "code": role,
                    "system_role": role,
                    "identity_kind": kind,
                    "synthetic": True,
                }
                for role, kind in (
                    ("finance_bp", "human"),
                    ("analyst", "human"),
                    ("rule_owner", "human"),
                    ("ai_analyst", "ai"),
                    ("ai_cfo", "ai"),
                    ("service_account", "service"),
                )
            ],
        )
        self._write_jsonl(
            "organization/users.jsonl",
            [
                {
                    "actor_id": "damai-logistics:usr:finance-001",
                    "employee_code": "DM-001",
                    "display_name": "Synthetic User",
                    "org_unit_code": "DAMAI",
                    "position_code": "FIN",
                    "role_code": "finance_bp",
                    "identity_kind": "human",
                    "synthetic": True,
                    "email": "finance@damai.example.invalid",
                }
            ],
        )
        self._write_jsonl("organization/permissions.jsonl", package_builder.permissions())
        sql_path = self.package / "sql/10_organization.sql"
        sql_path.parent.mkdir(parents=True)
        sql_path.write_text(
            package_builder._generate_organization_sql(self.package, "damai-logistics"),
            encoding="utf-8",
        )
        self._refresh_manifest()
        self._original_package = package_builder.PACKAGE
        package_builder.PACKAGE = self.package

    def tearDown(self) -> None:
        package_builder.PACKAGE = self._original_package
        self._tmp.cleanup()

    def _write_jsonl(self, relative_path: str, rows: list[dict]) -> None:
        path = self.package / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    def _refresh_manifest(self, **updates: object) -> None:
        files = {}
        for path in sorted(
            p for p in self.package.rglob("*") if p.is_file() and p.name != "manifest.json"
        ):
            content = path.read_bytes()
            entry: dict[str, object] = {
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
            }
            if path.suffix == ".jsonl":
                entry["rows"] = len(content.splitlines())
            files[path.relative_to(self.package).as_posix()] = entry
        manifest: dict[str, object] = {
            "package_id": "damai-logistics",
            "package_version": "1.0.0",
            "enterprise_code": "damai-logistics",
            "enterprise_name": "大麦物流集团",
            "synthetic": True,
            "contract_version": "flow.enterprise-package.v1",
            "modules": {"organization": "1.0.0", "business": "1.0.0"},
            "files": files,
            **updates,
        }
        (self.package / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True), encoding="utf-8"
        )

    def test_real_package_passes(self) -> None:
        package_builder.PACKAGE = ROOT / "data/enterprise/damai-logistics/v1"
        manifest = package_builder.verify()
        self.assertEqual(manifest["contract_version"], "flow.enterprise-package.v1")

    def test_rejects_unmanifested_file(self) -> None:
        (self.package / "untracked.txt").write_text("not covered\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            package_builder.verify()

    def test_rejects_manifest_path_traversal(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("outside package\n", encoding="utf-8")
        manifest_path = self.package / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["../outside.txt"] = {
            "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
            "bytes": outside.stat().st_size,
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(SystemExit):
            package_builder.verify()

    def test_rejects_unsupported_contract_version(self) -> None:
        self._refresh_manifest(contract_version="flow.enterprise-package.v99")
        with self.assertRaises(SystemExit):
            package_builder.verify()

    def test_rejects_organization_sql_out_of_sync_with_jsonl(self) -> None:
        sql_path = self.package / "sql/10_organization.sql"
        sql_path.write_text(sql_path.read_text(encoding="utf-8") + "-- drift\n", encoding="utf-8")
        self._refresh_manifest()
        with self.assertRaises(SystemExit):
            package_builder.verify()

    def test_rejects_credentials_in_identity_records(self) -> None:
        self._write_jsonl(
            "organization/users.jsonl",
            [
                {
                    "actor_id": "damai-logistics:usr:finance-001",
                    "employee_code": "DM-001",
                    "org_unit_code": "DAMAI",
                    "position_code": "FIN",
                    "role_code": "finance_bp",
                    "synthetic": True,
                    "password": "demo-only",
                }
            ],
        )
        self._refresh_manifest()
        with self.assertRaises(SystemExit):
            package_builder.verify()


if __name__ == "__main__":
    unittest.main()
