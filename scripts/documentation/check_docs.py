#!/usr/bin/env python3
"""Unified documentation check entrypoint (plan Task 3, design V1.1 §6.3).

聚合 metadata / inventory / release 校验，供本地与 CI 使用：
    python3 scripts/documentation/check_docs.py --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from documentation.inventory import repo_head  # noqa: E402
from documentation.metadata import check_repository  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="run full documentation checks")
    args = ap.parse_args(argv)
    if not args.check:
        ap.error("--check required")

    root = Path(__file__).resolve().parent.parent.parent
    result = check_repository(root)
    print(f"metadata: {'PASS' if result.ok else 'FAIL'} "
          f"({result.checked} docs, {result.exempt} legacy-exempt, "
          f"{len(result.errors)} errors)")
    for e in result.errors:
        print(f"  ERROR {e}")
    for w in result.warnings:
        print(f"  warn  {w}")
    print(f"repo head: {repo_head(root)}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
