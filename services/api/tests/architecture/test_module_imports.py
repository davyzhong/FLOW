"""S01 Task 7（模块边界）AST 导入守护测试。

规则（三 Agent 计划 Task 4 / 设计 §6 文件所有权）：
- 产品模块（public_analysis / internal_workbench）禁止互相导入；
- 产品模块只能通过 `flow_api.modules.registry` 访问 shared_core；
- shared_core 不得导入任何产品模块；
- ownership manifest 必须覆盖纳管目录下每个现存文件恰好一次。
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # services/api/tests/architecture -> 仓库根
MODULES = ROOT / "services/api/src/flow_api/modules"
OWNERSHIP = ROOT / "config/modules/ownership_v1.yaml"

PRODUCT_MODULES = {"public_analysis", "internal_workbench"}
ALL_MODULES = PRODUCT_MODULES | {"shared_core"}


def _tree(path: Path) -> ast.Module | None:
    if not path.is_file():
        return None
    return ast.parse(path.read_text(encoding="utf-8"))


def _flow_imports(tree: ast.Module) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _module_files(module: str) -> list[Path]:
    base = MODULES / module
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.py") if p.is_file())


def test_product_modules_do_not_import_each_other() -> None:
    for module in PRODUCT_MODULES:
        for file in _module_files(module):
            tree = _tree(file)
            assert tree is not None, file
            for imported in _flow_imports(tree):
                for other in PRODUCT_MODULES - {module}:
                    assert not imported.startswith(
                        f"flow_api.modules.{other}"
                    ), f"{file.name} 禁止导入产品模块 {other}（public↔internal 隔离）"


def test_shared_core_does_not_import_product_modules() -> None:
    for file in _module_files("shared_core"):
        tree = _tree(file)
        assert tree is not None, file
        for imported in _flow_imports(tree):
            for product in PRODUCT_MODULES:
                assert not imported.startswith(
                    f"flow_api.modules.{product}"
                ), f"shared_core/{file.name} 禁止导入产品模块 {product}"


def test_product_modules_access_shared_core_only_via_registry() -> None:
    for module in PRODUCT_MODULES:
        for file in _module_files(module):
            tree = _tree(file)
            assert tree is not None, file
            for imported in _flow_imports(tree):
                if imported.startswith("flow_api.modules.shared_core"):
                    assert imported == "flow_api.modules.registry", (
                        f"{file.name} 只能经 registry 访问 shared_core，发现 {imported}"
                    )


def test_ownership_manifest_covers_every_managed_file_exactly_once() -> None:
    import yaml

    manifest = yaml.safe_load(OWNERSHIP.read_text(encoding="utf-8"))
    assert manifest is not None, "ownership_v1.yaml 缺失"
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for entry in manifest.get("managed_files", []):
        path = entry["path"]
        if path in seen:
            duplicates.append(path)
        seen[path] = entry.get("owner", "")
    assert not duplicates, f"manifest 重复登记: {duplicates}"

    managed_dirs = [MODULES, ROOT / "services/api/src/flow_api/security"]
    missing: list[str] = []
    for base in managed_dirs:
        if not base.is_dir():
            continue
        for file in base.rglob("*.py"):
            if file.name == "__init__.py" and file.parent == base:
                continue
            rel = "services/api/src/flow_api/" + str(file.relative_to(base.parent))
            if rel not in seen:
                missing.append(rel)
    assert not missing, f"以下纳管文件未登记 owner: {missing}"


def test_registry_exposes_product_modules_with_contract_fixture() -> None:
    from flow_api.modules.registry import MODULES

    by_id = {m["id"]: m for m in MODULES}
    assert set(by_id) == {"public_analysis", "internal_workbench", "professional_governance"}
    assert "shared_core" not in by_id, "shared_core 不得出现在产品可见模块列表"
    assert by_id["public_analysis"]["status"] == "implemented"
    assert by_id["internal_workbench"]["status"] == "designed"
    assert by_id["professional_governance"]["status"] == "designed"
