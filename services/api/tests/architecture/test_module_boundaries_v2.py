"""R3 module-boundaries-v2 守护测试。

- 真实树必须 PASS（ownership 全覆盖 + import_rules 零违规）；
- 合成违规 fixture 必须让检查器变红（禁止导入 / unowned 文件），
  证明门禁不是恒绿摆设。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
CHECKER = REPO / "scripts/check_module_boundaries.py"
MANIFEST = REPO / "config/modules/ownership_v1.yaml"


def _run(manifest: Path, tree: Path) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--manifest", str(manifest), "--tree", str(tree), "--json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip().startswith("{")]
    payload = (
        json.loads(proc.stdout)
        if proc.stdout.strip().startswith("{")
        else json.loads("\n".join(lines))
    )
    return proc.returncode, payload


def test_real_tree_passes() -> None:
    code, payload = _run(MANIFEST, REPO / "services/api/src/flow_api")
    assert code == 0, json.dumps(payload, ensure_ascii=False, indent=2)
    assert payload["ok"] is True
    assert payload["unowned"] == []
    assert payload["import_violations"] == []


def test_forbidden_import_is_detected(tmp_path: Path) -> None:
    tree = tmp_path / "src" / "flow_api"
    (tree / "alpha").mkdir(parents=True)
    (tree / "beta").mkdir(parents=True)
    (tree / "alpha" / "__init__.py").write_text("")
    (tree / "beta" / "__init__.py").write_text("")
    # alpha（owner A）导入 beta（owner B）——规则禁止
    (tree / "alpha" / "consumer.py").write_text("import flow_api.beta.service\n")
    (tree / "beta" / "service.py").write_text("X = 1\n")

    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "version": "v2",
                "managed_files": [],
                "glob_rules": [
                    {"pattern": "services/api/src/flow_api/alpha/**", "owner": "owner_a"},
                    {"pattern": "services/api/src/flow_api/beta/**", "owner": "owner_b"},
                    {"pattern": "services/api/src/flow_api/**", "owner": "platform"},
                ],
                "import_rules": [
                    {"forbid_owner": "owner_a", "import_owner": "owner_b"},
                ],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    code, payload = _run(manifest, tree)
    assert code == 1, "禁止导入必须被检出（门禁必须能红）"
    violations = payload["import_violations"]
    assert len(violations) == 1
    assert violations[0]["file"].endswith("alpha/consumer.py")
    assert violations[0]["import_owner"] == "owner_b"


def test_unowned_file_is_detected(tmp_path: Path) -> None:
    tree = tmp_path / "src" / "flow_api" / "solo"
    tree.mkdir(parents=True)
    (tree / "orphan.py").write_text("Y = 2\n")

    manifest = tmp_path / "manifest.yaml"
    # 无 catch-all：orphan.py 无 owner
    manifest.write_text(
        yaml.safe_dump(
            {
                "version": "v2",
                "managed_files": [],
                "glob_rules": [
                    {"pattern": "services/api/src/flow_api/other/**", "owner": "owner_x"},
                ],
                "import_rules": [],
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    code, payload = _run(manifest, tree)
    assert code == 1, "unowned 文件必须被检出"
    assert any(rel.endswith("solo/orphan.py") for rel in payload["unowned"])


def test_manifest_registers_every_real_owner_domain() -> None:
    """关键职责域必须在 manifest 的 glob/显式登记中可达（防误删规则）。"""

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    owners = {rule.get("owner") for rule in manifest.get("glob_rules", [])}
    owners |= {entry.get("owner") for entry in manifest.get("managed_files", [])}
    for required in (
        "security",
        "publication-transaction",
        "public_analysis",
        "internal_workbench",
        "shared_core",
        "platform",
    ):
        assert required in owners, f"职责域 {required} 未在 manifest 登记"
    # Agent 代号不得回归
    assert not (owners & {"sol", "kimi", "glm-coordinator"}), "owner 不得使用 Agent 代号"
