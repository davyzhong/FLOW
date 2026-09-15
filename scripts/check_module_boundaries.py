#!/usr/bin/env python3
"""R3 module-boundaries-v2：全树 ownership + 禁止导入 AST 扫描。

合同（config/modules/ownership_v1.yaml v2）：
1. 解析顺序：managed_files 显式登记 > glob_rules 按序 first-match；
2. services/api/src/flow_api 全树每个 .py 必须解析到唯一 owner（unowned 即错）；
3. `import_rules` 声明 owner 对禁止导入： forbid_owner 拥有的文件 import 到
   import_owner 拥有的模块即违规（AST Import/ImportFrom 全量扫描）；
4. 退出码：0 = 通过；1 = 发现违规；2 = 配置错误。--json 输出机器可读结果。

用法：python3 scripts/check_module_boundaries.py [--manifest PATH] [--json]
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_DEFAULT = Path(__file__).resolve().parents[1]
MANIFEST_DEFAULT = REPO_DEFAULT / "config/modules/ownership_v1.yaml"
TREE_ROOT_DEFAULT = REPO_DEFAULT / "services/api/src/flow_api"

FLOW_PACKAGE = "flow_api"


@dataclass
class Report:
    unowned: list[str] = field(default_factory=list)
    import_violations: list[dict[str, str]] = field(default_factory=list)
    config_errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.unowned or self.import_violations or self.config_errors)


def load_manifest(path: Path) -> dict[str, Any]:
    import yaml

    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or "managed_files" not in manifest:
        raise ValueError(f"manifest 缺少 managed_files：{path}")
    if not isinstance(manifest.get("glob_rules", []), list):
        raise ValueError(f"glob_rules 必须是列表：{path}")
    return manifest


def resolve_owner(rel_path: str, manifest: dict[str, Any]) -> str | None:
    """显式登记优先，glob 按声明顺序 first-match。"""

    entries = manifest.get("managed_files", [])
    if isinstance(entries, list):
        for entry in entries:
            entry_dict: dict[str, Any] = entry
            if entry_dict.get("path") == rel_path:
                owner = entry_dict.get("owner")
                return str(owner) if owner is not None else None
    for rule in manifest.get("glob_rules", []):
        rule_dict: dict[str, Any] = rule
        if fnmatch.fnmatch(rel_path, str(rule_dict.get("pattern", ""))):
            owner = rule_dict.get("owner")
            return str(owner) if owner is not None else None
    return None


def _flow_imports(file: Path) -> list[str]:
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"))
    except SyntaxError as error:
        raise ValueError(f"AST 解析失败 {file}: {error}") from error
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _module_to_rel(module: str) -> str | None:
    """flow_api.x.y → services/api/src/flow_api/x/y(.py|/__init__.py)。"""

    if module != FLOW_PACKAGE and not module.startswith(FLOW_PACKAGE + "."):
        return None
    parts = module.split(".")[1:]
    if not parts:
        return "services/api/src/flow_api/__init__.py"
    return "services/api/src/flow_api/" + "/".join(parts) + ".py"


def scan(tree_root: Path, manifest: dict[str, Any]) -> Report:
    report = Report()
    tree_prefix = tree_root.resolve().as_posix()
    files = sorted(p for p in tree_root.rglob("*.py") if p.is_file())
    rel_owner: dict[str, str] = {}

    for file in files:
        rel = "services/api/src/" + str(file.relative_to(tree_root.parent))
        owner = resolve_owner(rel, manifest)
        if owner is None:
            report.unowned.append(rel)
            continue
        rel_owner[rel] = owner

    rules = manifest.get("import_rules", [])
    for file in files:
        rel = "services/api/src/" + str(file.relative_to(tree_root.parent))
        owner = rel_owner.get(rel)
        if owner is None:
            continue
        for module in _flow_imports(file):
            target_rel = _module_to_rel(module)
            if target_rel is None or target_rel == rel:
                continue
            target_owner = rel_owner.get(target_rel)
            if target_owner is None:
                continue
            for rule in rules:
                if rule.get("forbid_owner") == owner and rule.get("import_owner") == target_owner:
                    report.import_violations.append(
                        {
                            "file": rel,
                            "file_owner": owner,
                            "import": module,
                            "import_owner": target_owner,
                            "rule": f"{owner} 禁止导入 {target_owner}",
                        }
                    )
    del tree_prefix
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--tree", type=Path, default=TREE_ROOT_DEFAULT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except Exception as error:  # noqa: BLE001
        print(f"config error: {error}", file=sys.stderr)
        return 2
    report = scan(args.tree, manifest)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "unowned": report.unowned,
                    "import_violations": report.import_violations,
                    "config_errors": report.config_errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for rel in report.unowned:
            print(f"UNOWNED {rel}")
        for violation in report.import_violations:
            print(
                f"FORBIDDEN IMPORT {violation['file']} ({violation['file_owner']})"
                f" -> {violation['import']} ({violation['import_owner']})"
            )
        total = len(report.unowned) + len(report.import_violations)
        print(f"module-boundaries-v2: {'PASS' if report.ok else 'FAIL'} ({total} violations)")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
