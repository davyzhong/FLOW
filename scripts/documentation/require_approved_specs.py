#!/usr/bin/env python3
"""S01 Task 2: approved-spec 门禁（require_approved_specs）。

合同（S01 计划 Task 2 Step 5 / Task 3–8 共同 Step 0）：
  - 给定 doc_id 必须在 docs/ 下各定位到唯一 markdown 文件；
  - 每份规格 frontmatter status 必须为 approved（draft/review 均失败）；
  - docs/40_specs/SPEC_INDEX.md 必须存在该文件权威路径对应的行，且行内 status 为 approved；
  - doc_id 缺失/重复、索引缺行、路径不符、状态不符 → 非零退出，不写代码。

用法：
  python3 scripts/documentation/require_approved_specs.py <doc_id> [<doc_id>...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.documentation.metadata import parse_frontmatter  # noqa: E402

SPEC_INDEX = "docs/40_specs/SPEC_INDEX.md"

# S01 三份实施子规格（Task 3–8 的共同 Step 0 门禁对象）
S01_SPEC_DOC_IDS = [
    "FLOW-SPEC-MODULE-BOUNDARIES-V1",
    "FLOW-SPEC-FINANCIAL-FACTS-V2",
    "FLOW-SPEC-INTERNAL-RBAC-AUDIT-V1",
]


def _locate_by_doc_id(root: Path) -> Dict[str, List[str]]:
    """扫描 docs/ 下所有 markdown，建立 doc_id -> 相对路径列表。"""
    found: Dict[str, List[str]] = {}
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return found
    for p in sorted(docs_dir.rglob("*.md")):
        try:
            meta = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if meta and meta.get("doc_id"):
            found.setdefault(meta["doc_id"], []).append(p.relative_to(root).as_posix())
    return found


def _index_rows(root: Path) -> Dict[str, str]:
    """解析 SPEC_INDEX 表格：权威路径（去反引号/备注） -> 行内 status。"""
    rows: Dict[str, str] = {}
    index = root / SPEC_INDEX
    if not index.exists():
        return rows
    for line in index.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in ("spec", "---") or set(cells[0]) <= {"-", ":"}:
            continue
        status = cells[2]
        # 权威路径列：取第一个反引号包裹的路径；无反引号则取首个空白/（前的记号
        m = re.search(r"`([^`]+)`", cells[3])
        path = m.group(1) if m else re.split(r"[\s（(]", cells[3])[0]
        if path:
            rows[path] = status
    return rows


def check(root: Path, doc_ids: List[str]) -> List[str]:
    """返回错误列表；空列表表示门禁通过。"""
    errors: List[str] = []
    located = _locate_by_doc_id(root)
    index_rows = _index_rows(root)
    index_exists = (root / SPEC_INDEX).exists()

    for doc_id in doc_ids:
        paths = located.get(doc_id, [])
        if not paths:
            errors.append(f"{doc_id}: 未在 docs/ 下定位到任何 markdown 文件")
            continue
        if len(paths) > 1:
            errors.append(f"{doc_id}: doc_id 不唯一 -> {', '.join(paths)}")
            continue
        rel = paths[0]

        meta = parse_frontmatter((root / rel).read_text(encoding="utf-8")) or {}
        status = meta.get("status", "")
        if status != "approved":
            errors.append(f"{doc_id}: frontmatter status 为 {status!r}，门禁要求 approved（{rel}）")

        if not index_exists:
            errors.append(f"{doc_id}: SPEC_INDEX 缺失（{SPEC_INDEX}）")
            continue
        row_status = index_rows.get(rel)
        if row_status is None:
            errors.append(f"{doc_id}: SPEC_INDEX 缺少权威路径 {rel} 对应的行")
        elif row_status != "approved":
            errors.append(
                f"{doc_id}: SPEC_INDEX 行内 status 为 {row_status!r}，门禁要求 approved（{rel}）")

    return errors


def main(argv: List[str]) -> int:
    doc_ids = argv[1:] or S01_SPEC_DOC_IDS
    errors = check(ROOT, doc_ids)
    if errors:
        print("approved-spec 门禁失败：")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"approved-spec 门禁通过（{len(doc_ids)} 份规格均为 approved）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
