"""S01 Task 2: approved-spec gate tests (require_approved_specs).

门禁合同（S01 计划 Task 2 Step 5 / Task 3–8 共同 Step 0）：
  - 三个精确 doc_id 必须在 docs/ 下各定位到唯一 markdown 文件；
  - 每份规格 frontmatter status 必须为 approved（draft/review 均失败）；
  - SPEC_INDEX.md 必须存在该文件权威路径对应的行，且行内 status 为 approved；
  - doc_id 缺失、路径错、索引缺行、状态不符 → 非零退出，不写代码。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.documentation.require_approved_specs import check

DOC_IDS = [
    "FLOW-SPEC-MODULE-BOUNDARIES-V1",
    "FLOW-SPEC-FINANCIAL-FACTS-V2",
    "FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1",
]
PATHS = {
    "FLOW-SPEC-MODULE-BOUNDARIES-V1": "docs/40_specs/platform/module-boundaries-v1.md",
    "FLOW-SPEC-FINANCIAL-FACTS-V2": "docs/40_specs/financial-facts/financial-facts-contract-v2.md",
    "FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1": "docs/40_specs/security/internal-workbench-rbac-audit-v1.md",
}


def _spec(root: Path, doc_id: str, rel: str, status: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"doc_id: {doc_id}",
                "title: test spec",
                "doc_type: specification",
                f"status: {status}",
                "version: 1.0",
                "created_at: 2026-09-13",
                "updated_at: 2026-09-13",
                "owner: FLOW",
                "decision_refs: [D053]",
                "knowledge_release: flow-knowledge-2026-09-12.1",
                "applies_to: specs",
                "---",
                "",
                "# spec",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _index(root: Path, rows: list[tuple[str, str]]) -> None:
    lines = [
        "# SPEC_INDEX",
        "",
        "| spec | 域 | status | 权威路径 | 备注 |",
        "|---|---|---|---|---|",
    ]
    for rel, status in rows:
        lines.append(f"| x | platform | {status} | `{rel}` |  |")
    (root / "docs/40_specs").mkdir(parents=True, exist_ok=True)
    (root / "docs/40_specs/SPEC_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fixture(root: Path, statuses: dict[str, str], index_status: str = "approved") -> None:
    for doc_id in DOC_IDS:
        _spec(root, doc_id, PATHS[doc_id], statuses.get(doc_id, "approved"))
    _index(root, [(PATHS[d], index_status) for d in DOC_IDS])


class RequireApprovedSpecsTest(unittest.TestCase):
    def run_check(self, root: Path) -> list[str]:
        return check(root, DOC_IDS)

    def test_all_approved_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {})
            self.assertEqual(self.run_check(root), [])

    def test_review_status_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {"FLOW-SPEC-FINANCIAL-FACTS-V2": "review"})
            errors = self.run_check(root)
            self.assertTrue(any("FLOW-SPEC-FINANCIAL-FACTS-V2" in e and "review" in e for e in errors))

    def test_draft_status_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {"FLOW-SPEC-MODULE-BOUNDARIES-V1": "draft"})
            self.assertTrue(self.run_check(root))

    def test_missing_doc_id_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {})
            (root / PATHS["FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1"]).unlink()
            errors = self.run_check(root)
            self.assertTrue(any("FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1" in e for e in errors))

    def test_index_row_missing_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {})
            _index(root, [(PATHS[d], "approved") for d in DOC_IDS[:2]])  # 第三行缺失
            errors = self.run_check(root)
            self.assertTrue(any("SPEC_INDEX" in e for e in errors))

    def test_index_status_not_approved_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {}, index_status="review")
            errors = self.run_check(root)
            self.assertTrue(any("SPEC_INDEX" in e and "review" in e for e in errors))

    def test_index_path_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root, {})
            _index(root, [(PATHS[d] + ".wrong", "approved") for d in DOC_IDS])
            self.assertTrue(self.run_check(root))

    def test_real_repository_review_state_fails(self):
        """真实仓库：规格处于 review 时门禁必须失败（获批后此测试转为通过 approved）。"""
        import scripts.documentation.require_approved_specs as mod

        root = Path(mod.__file__).resolve().parents[2]
        errors = check(root, DOC_IDS)
        spec = root / PATHS["FLOW-SPEC-MODULE-BOUNDARIES-V1"]
        if not spec.exists():
            self.skipTest("三份规格尚未落盘")
        from scripts.documentation.metadata import parse_frontmatter

        status = parse_frontmatter(spec.read_text(encoding="utf-8"))["status"]
        if status == "approved":
            self.assertEqual(errors, [])
        else:
            self.assertTrue(errors, "review 状态下门禁必须通过失败")


if __name__ == "__main__":
    unittest.main()
