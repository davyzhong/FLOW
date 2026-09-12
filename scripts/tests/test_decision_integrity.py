"""Task 5 (M1.3) tests: D001-D051 decision integrity (plan Task 5 Step 1)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.documentation.metadata import parse_frontmatter

REPO = Path(__file__).resolve().parent.parent.parent
DECISIONS_DIR = REPO / "docs/10_governance/decisions"
INDEX = REPO / "docs/10_governance/DECISION_INDEX.md"


class DecisionIntegrityTests(unittest.TestCase):
    def test_d001_through_d051_present_exactly_once(self) -> None:
        files = sorted(DECISIONS_DIR.glob("D*.md")) if DECISIONS_DIR.exists() else []
        ids = [f.name.split("--")[0] for f in files]
        expected = [f"D{n:03d}" for n in range(1, 52)]
        self.assertEqual(ids, expected, f"missing={set(expected)-set(ids)} extra={set(ids)-set(expected)}")

    def test_each_decision_has_compliant_frontmatter(self) -> None:
        if not DECISIONS_DIR.exists():
            self.skipTest("decisions not yet split")
        for f in sorted(DECISIONS_DIR.glob("D*.md")):
            with self.subTest(decision=f.name):
                meta = parse_frontmatter(f.read_text(encoding="utf-8"))
                self.assertIsNotNone(meta, f.name)
                self.assertTrue(meta.get("doc_id", "").startswith("FLOW-DECISION-"))
                self.assertEqual(meta.get("doc_type"), "decision")
                self.assertIn(meta.get("status"),
                              {"proposed", "accepted", "amended", "superseded", "retired", "rejected"})
                self.assertIn("decided_at", meta)
                self.assertIn("authority", meta)

    def test_index_rows_cover_all_decisions(self) -> None:
        if not INDEX.exists():
            self.skipTest("index not yet built")
        text = INDEX.read_text(encoding="utf-8")
        for n in range(1, 52):
            self.assertIn(f"D{n:03d}", text)

    def test_superseded_relations_resolve(self) -> None:
        if not DECISIONS_DIR.exists():
            self.skipTest("decisions not yet split")
        metas = {}
        for f in sorted(DECISIONS_DIR.glob("D*.md")):
            meta = parse_frontmatter(f.read_text(encoding="utf-8"))
            metas[meta.get("doc_id", "")] = meta
        for doc_id, meta in metas.items():
            for ref_field in ("supersedes", "superseded_by"):
                for ref in re.findall(r"FLOW-DECISION-D\d+", meta.get(ref_field, "") or ""):
                    self.assertIn(ref, metas, f"{doc_id} {ref_field} -> {ref} unresolved")

    def test_legacy_log_is_compatible_superseded(self) -> None:
        legacy = REPO / "docs/knowledge-base/04_decisions/DECISION_LOG.md"
        meta = parse_frontmatter(legacy.read_text(encoding="utf-8"))
        self.assertIsNotNone(meta)
        self.assertEqual(meta.get("status"), "superseded")
        body = legacy.read_text(encoding="utf-8")
        self.assertIn("DECISION_INDEX.md", body)


if __name__ == "__main__":
    unittest.main()
