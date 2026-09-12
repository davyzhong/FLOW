"""Task 1 (M0.1) tests: deterministic KB manifest generation (plan Step 6).

kb_manifest.py --write 生成 99_manifest/inventory.tsv 与 sha256sums.txt，
两份 manifest 排除自身，路径按 UTF-8 字节排序；--check 在临时目录重建
并逐字节比较（inventory.tsv 的 mtime 列在 fresh clone 不可复现，豁免），
同时校验每个 SHA-256。
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.documentation.kb_manifest import check as manifest_check
from scripts.documentation.kb_manifest import write as manifest_write

INV_HEADER = "relative_path\tsize_bytes\tmodified_time\tmime_type"


def make_fixture(tmp: Path) -> Path:
    files = {
        "docs/knowledge-base/README.md": "# kb\n",
        "docs/knowledge-base/02_research/研究笔记.md": "中文内容\n",
        "docs/knowledge-base/03_assets/a.png": "\x89PNG\r\n\x1a\nfake",
        "docs/knowledge-base/01_conversations/raw/raw-session.md": "raw\n",
        "README.md": "repo readme\n",
    }
    for rel, body in files.items():
        p = tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body.encode("utf-8"))
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "fixture"],
        cwd=tmp, check=True,
    )
    return tmp


class KbManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_fixture(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_write_produces_sorted_exclusive_manifests(self) -> None:
        manifest_write(self.root)
        inv = self.root / "docs/knowledge-base/99_manifest/inventory.tsv"
        sums = self.root / "docs/knowledge-base/99_manifest/sha256sums.txt"
        lines = inv.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], INV_HEADER)
        paths = [ln.split("\t")[0] for ln in lines[1:]]
        self.assertEqual(paths, sorted(paths))  # UTF-8 字节序
        self.assertNotIn("99_manifest/inventory.tsv", paths)
        self.assertNotIn("99_manifest/sha256sums.txt", paths)
        self.assertIn("README.md", paths)  # 知识库根下的文件（相对 KB 目录）
        raw = "01_conversations/raw/raw-session.md"
        self.assertIn(raw, paths)
        # sha256sums 行格式：<sha>  ./<path>
        for ln in sums.read_text(encoding="utf-8").splitlines():
            self.assertRegex(ln, r"^[0-9a-f]{64}  \./")

    def test_check_passes_after_write(self) -> None:
        manifest_write(self.root)
        self.assertTrue(manifest_check(self.root))

    def test_check_passes_on_touch_without_content_change(self) -> None:
        """mtime 列豁免：touch 不改内容，check 必须仍通过。"""
        import os

        manifest_write(self.root)
        p = self.root / "docs/knowledge-base/README.md"
        os.utime(p, (p.stat().st_atime + 5000, p.stat().st_mtime + 5000))
        self.assertTrue(manifest_check(self.root))

    def test_check_fails_after_content_change(self) -> None:
        manifest_write(self.root)
        p = self.root / "docs/knowledge-base/README.md"
        p.write_text("# changed\n", encoding="utf-8")
        with self.assertRaises(AssertionError):
            manifest_check(self.root)

    def test_check_fails_on_missing_file(self) -> None:
        manifest_write(self.root)
        (self.root / "docs/knowledge-base/02_research/研究笔记.md").unlink()
        with self.assertRaises(AssertionError):
            manifest_check(self.root)

    def test_write_is_deterministic(self) -> None:
        manifest_write(self.root)
        inv = self.root / "docs/knowledge-base/99_manifest/inventory.tsv"
        sums = self.root / "docs/knowledge-base/99_manifest/sha256sums.txt"
        first = (inv.read_bytes(), sums.read_bytes())
        manifest_write(self.root)
        second = (inv.read_bytes(), sums.read_bytes())
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
