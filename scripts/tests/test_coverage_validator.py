from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.documentation.coverage_validator import validate_coverage


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


class CoverageValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.coverage = self.root / "coverage.tsv"
        self.exceptions = self.root / "exceptions.tsv"
        self.changes = self.root / "changes.tsv"
        write_tsv(self.coverage, ["source_id", "terminal_status", "evidence_ref"], [
            ["s1", "routed", "evidence/a"], ["s2", "failed", ""],
        ])
        write_tsv(self.exceptions, ["source_id", "exception_code", "reason"], [
            ["s2", "unreadable", "encoding error"],
        ])
        write_tsv(self.changes, ["source_id", "change_id"], [["s1", "l2-1"]])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_accepts_closed_universe_with_accounted_failure(self) -> None:
        result = validate_coverage(self.coverage, self.exceptions, self.changes, {"s1", "s2"})
        self.assertEqual(result, [])

    def test_rejects_duplicate_missing_and_orphaned_sources(self) -> None:
        write_tsv(self.coverage, ["source_id", "terminal_status", "evidence_ref"], [
            ["s1", "routed", "evidence/a"], ["s1", "routed", "evidence/b"],
        ])
        errors = validate_coverage(self.coverage, self.exceptions, self.changes, {"s1", "s2"})
        self.assertTrue(any("duplicate" in error for error in errors))
        self.assertTrue(any("missing" in error for error in errors))
        self.assertTrue(any("orphan" in error for error in errors))

    def test_rejects_unreviewed_status_in_strict_mode(self) -> None:
        write_tsv(self.coverage, ["source_id", "terminal_status", "evidence_ref"], [
            ["s1", "pending_review", ""], ["s2", "failed", ""],
        ])
        errors = validate_coverage(self.coverage, self.exceptions, self.changes, {"s1", "s2"}, strict=True)
        self.assertTrue(any("not terminal" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
