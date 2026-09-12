"""Task 3 (M1.1) tests: metadata contracts & cross-document integrity (design V1.1 §6.3).

纯 Python 校验：重复 doc_id；plan 引用未 approved spec；canonical 引用
不存在 release；非法状态；PROJECT_STATE current 重复；legacy-exempt
修改后仍绕过校验。
"""

from __future__ import annotations

import tempfile
import sys
import unittest
from pathlib import Path

from scripts.documentation.metadata import (
    CheckResult,
    check_repository,
    load_legacy_exemptions,
)


def write_doc(root: Path, rel: str, frontmatter: dict, body: str = "x\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    p.write_text("\n".join(lines) + f"\n\n{body}", encoding="utf-8")
    return p


def make_repo(tmp: Path) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


BASE_DOC = {
    "doc_id": "FLOW-X-001",
    "title": "sample",
    "doc_type": "design",
    "status": "approved",
    "version": "1.0",
    "created_at": "2026-09-12",
    "updated_at": "2026-09-12",
    "owner": "FLOW",
    "decision_refs": "[D001]",
    "knowledge_release": "pre-static-obsidian-2026-09-12T15:46+08:00",
}


class MetadataContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self._tmp.name))
        self._counter = 0

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def doc(self, **overrides) -> dict:
        self._counter += 1
        d = dict(BASE_DOC)
        d["doc_id"] = f"FLOW-X-{self._counter:03d}"
        d.update(overrides)
        return d

    def check(self) -> CheckResult:
        return check_repository(self.root)

    def test_valid_document_passes(self) -> None:
        write_doc(self.root, "docs/a.md", self.doc())
        result = self.check()
        self.assertEqual(result.errors, [])

    def test_duplicate_doc_id_fails(self) -> None:
        d = self.doc()
        write_doc(self.root, "docs/a.md", d)
        write_doc(self.root, "docs/b.md", dict(d))
        self.assertIn("duplicate doc_id", " ".join(self.check().errors))

    def test_plan_requires_approved_spec_upstream(self) -> None:
        spec = self.doc(doc_type="specification", status="draft")
        write_doc(self.root, "docs/spec.md", spec)
        write_doc(
            self.root,
            "docs/plan.md",
            self.doc(doc_type="plan", status="active", depends_on=f"[{spec['doc_id']}]",
                     acceptance_refs="[a]"),
        )
        errors = " ".join(self.check().errors)
        self.assertIn("not approved", errors)

    def test_canonical_knowledge_requires_existing_release(self) -> None:
        write_doc(
            self.root,
            "docs/card.md",
            self.doc(
                doc_type="knowledge-card",
                status="canonical",
                knowledge_release="flow-knowledge-2026-09-12.1",
                source_refs="[SRC-1]",
                authority_level="B",
                sensitivity="public",
            ),
        )
        self.assertIn("knowledge_release", " ".join(self.check().errors))

    def test_invalid_status_value_fails(self) -> None:
        write_doc(self.root, "docs/a.md", self.doc(status="bogus"))
        self.assertIn("status", " ".join(self.check().errors))

    def test_single_current_project_state_required(self) -> None:
        def state_doc():
            return self.doc(doc_type="state", title="PROJECT_STATE", status="current",
                            applies_to="repository")

        write_doc(self.root, "docs/00_start_here/PROJECT_STATE.md", state_doc())
        self.assertEqual(self.check().errors, [])
        write_doc(self.root, "docs/other/PROJECT_STATE.md", state_doc())
        errors = " ".join(self.check().errors)
        self.assertIn("PROJECT_STATE", errors)

    def test_modified_legacy_exempt_must_comply(self) -> None:
        legacy = self.root / "docs/legacy.md"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text("# legacy no frontmatter\n", encoding="utf-8")
        # 登记 exempt（带 hash 锁）
        import hashlib

        registered = hashlib.sha256(legacy.read_bytes()).hexdigest()
        exempt_file = self.root / "docs/10_governance/legacy-exemptions.tsv"
        exempt_file.parent.mkdir(parents=True, exist_ok=True)
        exempt_file.write_text(
            "path\tsha256\tdoc_id\n" f"docs/legacy.md\t{registered}\t-\n", encoding="utf-8"
        )
        # 未修改：通过
        self.assertEqual(self.check().errors, [])
        # 实质修改后：必须合规（无 frontmatter → 失败）
        legacy.write_text("# legacy changed\n", encoding="utf-8")
        errors = " ".join(self.check().errors)
        self.assertIn("legacy-exempt", errors)


class CheckDocsCliTests(unittest.TestCase):
    """Task 3 (M1.1)：scripts/check_docs.py 唯一入口与 phase fail-closed 行为。"""

    def test_single_entrypoint(self) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        self.assertTrue((root / "scripts/check_docs.py").is_file())
        self.assertFalse(
            (root / "scripts/documentation/check_docs.py").exists(),
            "旧 CLI 路径必须移除，scripts/check_docs.py 是唯一入口",
        )

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        import subprocess

        root = Path(__file__).resolve().parent.parent.parent
        return subprocess.run(
            [sys.executable, str(root / "scripts/check_docs.py"), *args],
            cwd=str(root), capture_output=True, text=True,
        )

    def test_phase_required(self) -> None:
        self.assertNotEqual(self._run().returncode, 0)
        self.assertNotEqual(self._run("--phase", "nope").returncode, 0)

    def test_phase_m1_runs(self) -> None:
        proc = self._run("--phase", "m1")
        self.assertIn("m1", proc.stdout + proc.stderr)

    def test_phase_m6_fails_closed_when_modules_missing(self) -> None:
        """links/reader_rubric 模块（M5/M6 交付）缺失时 m6 必须失败。"""
        proc = self._run("--phase", "m6")
        self.assertNotEqual(proc.returncode, 0)


class UniqueCurrentStateTests(unittest.TestCase):
    """Task 4 (M1.2)：全仓恰有一个 current state（对真实仓库断言）。"""

    def test_exactly_one_current_state(self) -> None:
        from scripts.documentation.metadata import iter_markdown, parse_frontmatter

        root = Path(__file__).resolve().parent.parent.parent
        current = []
        for entry in iter_markdown(root):
            path = entry[0] if isinstance(entry, tuple) else entry
            meta = parse_frontmatter(path.read_text(encoding="utf-8"))
            if meta and meta.get("doc_type") == "state" and meta.get("status") == "current":
                current.append((str(path.relative_to(root)), meta.get("doc_id")))
        self.assertEqual(current, [("docs/00_start_here/PROJECT_STATE.md", "FLOW-STATE-001")])

    def test_legacy_state_is_superseded(self) -> None:
        from scripts.documentation.metadata import parse_frontmatter

        root = Path(__file__).resolve().parent.parent.parent
        legacy = root / "docs/knowledge-base/00_start_here/PROJECT_STATE.md"
        meta = parse_frontmatter(legacy.read_text(encoding="utf-8"))
        self.assertEqual(meta.get("status"), "superseded")
        self.assertEqual(meta.get("superseded_by"), "FLOW-STATE-001")


if __name__ == "__main__":
    unittest.main()
