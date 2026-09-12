#!/usr/bin/env python3
"""Full-repo markdown link checker (plan Task 14, M6.1).

规则：git 跟踪 md；排除文档合同豁免区与 link-allowlist 登记（历史档案故意断链）；
相对链接必须可解析且不逃逸仓库根；HTTP/obsidian/file 链接只登记不阻断。
仅标准库。
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import re
import sys
from pathlib import Path
from typing import List, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.documentation.inventory import DOC_CONTRACT_EXEMPT_PREFIXES, git_tracked_files  # noqa: E402

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "obsidian://", "file://", "mailto:", "chatgpt-conversation://")


def load_allowlist(root: Path) -> List[Tuple[str, str]]:
    f = root / "docs/10_governance/link-allowlist.tsv"
    out = []
    if f.exists():
        for row in csv.reader(f.read_text(encoding="utf-8").splitlines(), delimiter="\t"):
            if row and not row[0].startswith("path"):
                out.append((row[0], row[1] if len(row) > 1 else "*"))
    return out


def _exempt(rel: str, allow: List[Tuple[str, str]]) -> bool:
    for path_pat, link_pat in allow:
        if fnmatch.fnmatch(rel, path_pat):
            return True
    return False


def iter_link_files(root: Path):
    allow = load_allowlist(root)
    for rel in sorted(git_tracked_files(root)):
        if not rel.endswith(".md"):
            continue
        if any(rel.startswith(p) for p in DOC_CONTRACT_EXEMPT_PREFIXES):
            continue
        if _exempt(rel, allow):
            continue
        yield root / rel, rel


def check_links(root: Path) -> List[str]:
    errors: List[str] = []
    http_seen = set()
    for p, rel in iter_link_files(root):
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in LINK_RE.finditer(text):
            target = m.group(1).split("#")[0]
            if not target or target.startswith(EXTERNAL_PREFIXES):
                if target.startswith("http"):
                    http_seen.add(target)
                continue
            resolved = (p.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"escapes repo root: {rel} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken: {rel} -> {target}")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.repo).resolve()
    errors = check_links(root)
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    print(f"links check: {'PASS' if not errors else 'FAIL'} ({len(errors)} errors)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
