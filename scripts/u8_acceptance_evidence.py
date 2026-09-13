#!/usr/bin/env python3
"""Validate machine-readable U8 acceptance evidence with fail-closed rules."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

SHA256 = re.compile(r"^[0-9a-f]{64}$")
MODES = {"full", "restore-u8-baseline"}


def validate_evidence(evidence: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if evidence.get("mode") not in MODES:
        errors.append("mode must be full or restore-u8-baseline")
    if not str(evidence.get("base_url", "")).startswith("https://"):
        errors.append("base_url must use https")
    if evidence.get("tls_verified") is not True:
        errors.append("TLS verification did not pass")
    if evidence.get("health_status") != 200:
        errors.append("restored application health must return 200")
    if evidence.get("web_status") != 200:
        errors.append("web endpoint must return 200")

    downloads = evidence.get("downloads")
    if not isinstance(downloads, list) or (evidence.get("mode") == "full" and not downloads):
        errors.append("at least one download must be verified")
    else:
        for index, download in enumerate(downloads):
            expected = str(download.get("expected_sha256", ""))
            actual = str(download.get("actual_sha256", ""))
            if not SHA256.fullmatch(expected) or expected != actual:
                errors.append(f"download {index} SHA-256 mismatch")

    if evidence.get("restore_exit_code") != 0:
        errors.append("pg_restore must exit with status 0")
    tables = evidence.get("critical_tables")
    if not isinstance(tables, dict) or not tables:
        errors.append("critical table counts are missing")
    else:
        for table, counts in tables.items():
            if not isinstance(counts, dict) or counts.get("before") != counts.get("after"):
                errors.append(f"critical table mismatch: {table}")

    expected_hash = str(evidence.get("expected_payload_hash", ""))
    restored_hash = str(evidence.get("restored_payload_hash", ""))
    if not SHA256.fullmatch(expected_hash) or expected_hash != restored_hash:
        errors.append("frozen payload hash mismatch")
    skipped = evidence.get("skipped")
    if not isinstance(skipped, list) or skipped:
        errors.append("acceptance contains a skip or lacks an explicit empty skipped list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    try:
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR evidence unreadable: {exc}")
        return 1
    errors = validate_evidence(evidence)
    for error in errors:
        print(f"ERROR {error}")
    print(f"U8 evidence: {'PASS' if not errors else 'FAIL'}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
