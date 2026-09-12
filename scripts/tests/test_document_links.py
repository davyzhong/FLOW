"""Task 14 (M6.1) tests: link checker — broken links, root escape, allowlist."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.documentation.links import check_links


def make_repo(tmp: Path) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    (tmp / "docs").mkdir(exist_ok=True)
    (tmp / "docs/a.md").write_text("[ok](b.md) [img](img.png)\n", encoding="utf-8")
    (tmp / "docs/b.md").write_text("text\n", encoding="utf-8")
    (tmp / "docs/img.png").write_bytes(b"png")
    for rel in ("docs/a.md", "docs/b.md", "docs/img.png"):
        subprocess.run(["git", "add", rel], cwd=tmp, check=True)
    return tmp


class LinkCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_valid_links_pass(self) -> None:
        self.assertEqual(check_links(self.root), [])

    def test_broken_link_fails(self) -> None:
        p = self.root / "docs/a.md"
        p.write_text("[bad](missing.md)\n", encoding="utf-8")
        errors = check_links(self.root)
        self.assertTrue(any("broken" in e for e in errors))

    def test_root_escape_fails(self) -> None:
        p = self.root / "docs/a.md"
        p.write_text("[out](../../outside.md)\n", encoding="utf-8")
        errors = check_links(self.root)
        self.assertTrue(any("escapes" in e for e in errors))

    def test_http_links_not_blocking(self) -> None:
        p = self.root / "docs/a.md"
        p.write_text("[ext](https://example.com/x.md) [obs](obsidian://open?path=x)\n", encoding="utf-8")
        self.assertEqual(check_links(self.root), [])

    def test_allowlist_suppresses_registered_broken(self) -> None:
        p = self.root / "docs/a.md"
        p.write_text("[legacy](gone.md)\n", encoding="utf-8")
        al = self.root / "docs/10_governance/link-allowlist.tsv"
        al.parent.mkdir(parents=True, exist_ok=True)
        al.write_text("path\tpattern\treason\ndocs/a.md\t*\ttest\n", encoding="utf-8")
        subprocess.run(["git", "add", str(al)], cwd=self.root, check=True)
        self.assertEqual(check_links(self.root), [])


if __name__ == "__main__":
    unittest.main()
