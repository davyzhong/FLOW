#!/usr/bin/env python3
"""Validate source coverage closure and traceable exceptions for K3."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

COVERAGE_HEADER = ["source_id", "terminal_status", "evidence_ref"]
EXCEPTION_HEADER = ["source_id", "exception_code", "reason"]
CHANGE_HEADER = ["source_id", "change_id"]
TERMINAL_STATUSES = {"routed", "filtered", "failed", "not_applicable"}
NONTERMINAL_STATUSES = {"pending_review", "in_progress"}


def _read(path: Path, expected_header: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    errors = []
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != expected_header:
                return [], [f"{path}: header must be {' / '.join(expected_header)}"]
            rows = list(reader)
    except OSError as exc:
        return [], [f"{path}: cannot read ({exc})"]
    for line, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"{path}:{line}: field count mismatch")
    return rows, errors


def validate_coverage(coverage_path: Path, exceptions_path: Path,
                      change_manifest_path: Path, source_ids: set[str],
                      strict: bool = False) -> list[str]:
    coverage, errors = _read(coverage_path, COVERAGE_HEADER)
    exceptions, exception_errors = _read(exceptions_path, EXCEPTION_HEADER)
    changes, change_errors = _read(change_manifest_path, CHANGE_HEADER)
    errors.extend(exception_errors)
    errors.extend(change_errors)
    if errors:
        return errors

    covered = [row["source_id"] for row in coverage]
    exception_ids = [row["source_id"] for row in exceptions]
    if len(covered) != len(set(covered)):
        errors.append("coverage contains duplicate source_id")
    if len(exception_ids) != len(set(exception_ids)):
        errors.append("exceptions contains duplicate source_id")
    covered_set = set(covered)
    missing = source_ids - covered_set
    orphan = covered_set - source_ids
    if missing:
        errors.append(f"coverage missing {len(missing)} source_id(s): {sorted(missing)[:5]}")
    if orphan:
        errors.append(f"coverage orphan source_id(s): {sorted(orphan)[:5]}")

    status_by_id: dict[str, str] = {}
    for row in coverage:
        sid, status, evidence = row["source_id"], row["terminal_status"], row["evidence_ref"]
        status_by_id[sid] = status
        if status not in TERMINAL_STATUSES | NONTERMINAL_STATUSES:
            errors.append(f"{sid}: unknown terminal_status {status!r}")
        elif strict and status not in TERMINAL_STATUSES:
            errors.append(f"{sid}: status {status!r} is not terminal")
        if status == "routed" and not evidence.strip():
            errors.append(f"{sid}: routed source has no evidence_ref")

    exception_set = set(exception_ids)
    failed = {sid for sid, status in status_by_id.items() if status == "failed"}
    if failed - exception_set:
        errors.append(f"failed sources without exception record: {sorted(failed - exception_set)[:5]}")
    if exception_set - failed:
        errors.append(f"orphan exception record(s): {sorted(exception_set - failed)[:5]}")
    for row in exceptions:
        if not row["exception_code"].strip() or not row["reason"].strip():
            errors.append(f"{row['source_id']}: exception requires code and reason")

    change_keys = [(row["source_id"], row["change_id"]) for row in changes]
    if len(change_keys) != len(set(change_keys)):
        errors.append("change manifest contains duplicate source_id/change_id")
    unknown_changes = {sid for sid, _ in change_keys} - source_ids
    if unknown_changes:
        errors.append(f"change manifest orphan source_id(s): {sorted(unknown_changes)[:5]}")
    if any(not change_id.strip() for _, change_id in change_keys):
        errors.append("change manifest contains empty change_id")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path, required=True)
    parser.add_argument("--change-manifest", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    baseline_header = ["source_id", "snapshot_id", "locator", "title", "author",
                       "file_sha256", "body_sha256", "image_set_sha256",
                       "has_summary_appendix", "has_image_appendix", "source_type",
                       "vault_commit", "vault_tree", "source_url_or_external_id",
                       "summary_model_version", "image_model_version", "k_domain",
                       "authority_level", "sensitivity", "availability", "flow_disposition"]
    rows, errors = _read(args.baseline, baseline_header)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    errors = validate_coverage(args.coverage, args.exceptions,
                               args.change_manifest,
                               {row["source_id"] for row in rows},
                               strict=args.strict)
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"coverage: PASS ({len(rows)} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
