from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.wechat_kb.make_manifest import build


class ManifestBuildTest(unittest.TestCase):
    def test_generated_manifests_do_not_hash_themselves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            knowledge_base = Path(temporary_directory)
            manifest_directory = knowledge_base / "99_manifest"
            manifest_directory.mkdir()
            readme = knowledge_base / "README.md"
            readme.write_text("FLOW knowledge base\n", encoding="utf-8")
            (manifest_directory / "inventory.tsv").write_text("stale inventory\n", encoding="utf-8")
            (manifest_directory / "sha256sums.txt").write_text("stale hashes\n", encoding="utf-8")

            row_count, hash_count = build(knowledge_base)

            inventory = (manifest_directory / "inventory.tsv").read_text(encoding="utf-8")
            hashes = (manifest_directory / "sha256sums.txt").read_text(encoding="utf-8")
            expected_digest = hashlib.sha256(readme.read_bytes()).hexdigest()
            self.assertEqual((row_count, hash_count), (1, 1))
            self.assertNotIn("99_manifest/inventory.tsv", inventory)
            self.assertNotIn("99_manifest/sha256sums.txt", inventory)
            self.assertNotIn("99_manifest/inventory.tsv", hashes)
            self.assertNotIn("99_manifest/sha256sums.txt", hashes)
            self.assertIn(f"{expected_digest}  ./README.md", hashes)


if __name__ == "__main__":
    unittest.main()
