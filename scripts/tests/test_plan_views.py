"""U8 freeze gate: roadmap/work-item consistency and generated plan views."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.documentation.plan_views import check, render_views, write_views


def _work_item(root: Path, name: str, doc_id: str, title: str, status: str) -> None:
    path = root / "docs/50_plans/work_items" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"doc_id: {doc_id}",
                f"title: {title}",
                "doc_type: work-item",
                f"status: {status}",
                "version: 1.0",
                "created_at: 2026-09-13",
                "updated_at: 2026-09-13",
                "owner: FLOW",
                "depends_on: []",
                "acceptance_refs: [gate]",
                "---",
                "",
                f"# {title}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _roadmap(root: Path, rows: list[str]) -> None:
    path = root / "docs/50_plans/CURRENT_ROADMAP.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# roadmap\n\n| 顺序 | 工作包 | 状态 |\n|---|---|---|\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )


class PlanViewsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _work_item(self.root, "U08--production-readiness.md", "FLOW-WI-U08", "U08 生产就绪收口", "completed")
        _work_item(self.root, "S01--gate.md", "FLOW-WI-S01", "S01 战略门禁", "active")
        _roadmap(
            self.root,
            [
                "| 1 | [U08](work_items/U08--production-readiness.md) | **completed** |",
                "| 2 | [S01](work_items/S01--gate.md) | **active** |",
            ],
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_work_item_in_roadmap_fails(self) -> None:
        _roadmap(self.root, ["| 1 | [U08](work_items/U08--production-readiness.md) | **completed** |"])
        self.assertIn("missing from CURRENT_ROADMAP", " ".join(check(self.root)))

    def test_duplicate_work_item_in_roadmap_fails(self) -> None:
        row = "| 1 | [U08](work_items/U08--production-readiness.md) | **completed** |"
        _roadmap(self.root, [row, row, "| 2 | [S01](work_items/S01--gate.md) | **active** |"])
        self.assertIn("appears 2 times", " ".join(check(self.root)))

    def test_status_mismatch_fails(self) -> None:
        _roadmap(
            self.root,
            [
                "| 1 | [U08](work_items/U08--production-readiness.md) | **active** |",
                "| 2 | [S01](work_items/S01--gate.md) | **active** |",
            ],
        )
        self.assertIn("status mismatch", " ".join(check(self.root)))

    def test_views_are_deterministic_and_check_detects_drift(self) -> None:
        write_views(self.root)
        first = render_views(self.root)
        self.assertEqual(first, render_views(self.root))
        self.assertEqual(check(self.root), [])
        active = self.root / "docs/50_plans/views/active.md"
        active.write_text(active.read_text(encoding="utf-8") + "manual drift\n", encoding="utf-8")
        self.assertIn("generated view drift", " ".join(check(self.root)))


class PlanViewsIntegrationTests(unittest.TestCase):
    def test_docs_check_invokes_plan_view_gate(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "check_docs.py").read_text(encoding="utf-8")
        self.assertIn("_run_plan_views(root, errors)", source)


if __name__ == "__main__":
    unittest.main()
