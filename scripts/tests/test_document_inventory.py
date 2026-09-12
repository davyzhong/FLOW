"""Task 1 (M0.1) tests: documentation inventory scanner boundaries.

计划 FLOW-DOC-MIGRATION-001 Task 1 Step 1 —— 固定扫描边界：
Git 跟踪文件为主清单；.git、缓存、构建产物不进入；
raw/original 会被识别为 immutable；每行至少包含
path、kind、mutmutability、consumer_count、sha256。
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from scripts.documentation.inventory import Row, build_inventory

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def make_fixture(tmp: Path) -> Path:
    """Build a minimal git repository fixture inside tmp and return its root."""
    tracked = {
        "docs/knowledge-base/01_conversations/raw/a.md": "raw session\n",
        "docs/knowledge-base/02_research/original/b.md": "original research\n",
        "docs/knowledge-base/03_assets/logistics_daily/c.png": "png",
        "docs/knowledge-base/05_design/approved/d.md": "approved snapshot\n",
        "docs/implementation/p5/data.yaml": "statements: 1\n",
        "docs/README.md": (
            "see docs/implementation/p5/data.yaml and "
            "docs/knowledge-base/02_research/original/b.md\n"
        ),
    }
    untracked = {
        "cache/build-artifact.txt": "not tracked\n",
        "untracked.md": "not tracked\n",
    }
    for rel, content in {**tracked, **untracked}.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    for rel in tracked:
        subprocess.run(["git", "add", rel], cwd=tmp, check=True)
    return tmp


class BuildInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.fixture_root = make_fixture(Path(self._tmp.name))
        self.rows = build_inventory(self.fixture_root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def by_path(self, rel: str) -> Row:
        for row in self.rows:
            if row.path == rel:
                return row
        raise AssertionError(f"missing row: {rel}")

    def test_inventory_marks_raw_and_original_as_immutable(self) -> None:
        immutable = {row.path for row in self.rows if row.mutability == "immutable"}
        self.assertIn("docs/knowledge-base/01_conversations/raw/a.md", immutable)
        self.assertIn("docs/knowledge-base/02_research/original/b.md", immutable)
        self.assertIn("docs/knowledge-base/03_assets/logistics_daily/c.png", immutable)
        self.assertIn("docs/knowledge-base/05_design/approved/d.md", immutable)

    def test_only_git_tracked_files_are_listed(self) -> None:
        paths = {row.path for row in self.rows}
        self.assertIn("docs/README.md", paths)
        self.assertNotIn("untracked.md", paths)
        self.assertNotIn("cache/build-artifact.txt", paths)
        self.assertFalse(any(p.startswith(".git/") for p in paths))

    def test_rows_have_required_fields(self) -> None:
        for row in self.rows:
            self.assertIsInstance(row.path, str)
            self.assertIsInstance(row.kind, str)
            self.assertIn(row.mutability, {"immutable", "mutable"})
            self.assertIsInstance(row.consumer_count, int)
            self.assertEqual(len(row.sha256), 64)
            self.assertGreaterEqual(row.size, 0)

    def test_consumer_references_are_counted(self) -> None:
        self.assertEqual(self.by_path("docs/implementation/p5/data.yaml").consumer_count, 1)
        self.assertEqual(
            self.by_path("docs/knowledge-base/02_research/original/b.md").consumer_count, 1
        )
        self.assertEqual(self.by_path("docs/README.md").consumer_count, 0)

    def test_kind_classification_by_extension(self) -> None:
        self.assertEqual(self.by_path("docs/README.md").kind, "markdown")
        self.assertEqual(self.by_path("docs/implementation/p5/data.yaml").kind, "yaml")
        self.assertEqual(self.by_path("docs/knowledge-base/03_assets/logistics_daily/c.png").kind, "image")

    def test_real_repo_immutable_constants_cover_current_roots(self) -> None:
        """计划 §0 的五个永久原位目录必须都在不可变常量内。"""
        from scripts.documentation.inventory import IMMUTABLE_ROOTS

        expected = {
            "docs/knowledge-base/01_conversations/raw/",
            "docs/knowledge-base/02_research/original/",
            "docs/knowledge-base/03_assets/logistics_daily/",
            "docs/knowledge-base/03_assets/external_reference/",
            "docs/knowledge-base/05_design/approved/",
        }
        self.assertEqual(set(IMMUTABLE_ROOTS), expected)


if __name__ == "__main__":
    unittest.main()
