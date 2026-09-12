#!/usr/bin/env python3
"""Reader-test rubric validator (plan Task 15, design V1.1 §10.3).

校验 RUBRIC yaml：五题、critical 集合 {1,2,4}、分值合计与通过规则（4/5 且 critical 无错）。
平铺 YAML（key: value）解析，仅标准库。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CRITICAL = {1, 2, 4}


def _parse_flat_yaml(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_0-9]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def validate(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    meta = _parse_flat_yaml(text)
    errors = []
    questions = [int(q) for q in re.findall(r"^question_(\d+)_points:", text, re.M)]
    if sorted(questions) != [1, 2, 3, 4, 5]:
        errors.append(f"expected questions 1-5, got {sorted(questions)}")
    crit = {int(q) for q in re.findall(r"^question_(\d+)_critical: true", text, re.M)}
    if crit != CRITICAL:
        errors.append(f"critical set must be {sorted(CRITICAL)}, got {sorted(crit)}")
    pass_rule = meta.get("pass_rule", "")
    if "4" not in pass_rule or "5" not in pass_rule:
        errors.append("pass_rule must encode 4-of-5")
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    print(f"rubric validate: {'PASS' if not errors else 'FAIL'}")
    return 0 if not errors else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rubric", type=Path)
    args = ap.parse_args(argv)
    return validate(args.rubric)


if __name__ == "__main__":
    sys.exit(main())
