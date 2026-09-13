#!/usr/bin/env python3
"""Generate plan status views and enforce roadmap/work-item consistency."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.documentation.metadata import parse_frontmatter  # noqa: E402

WORK_ITEM_LINK = re.compile(r"\]\(work_items/([^\)]+\.md)\)")
STATUS_TOKEN = re.compile(r"\*\*(proposed|active|blocked|completed|cancelled|archived)")
VIEW_META = {
    "active": ("FLOW-VIEW-ACTIVE-001", "活动视图", "活动工作包"),
    "blocked": ("FLOW-VIEW-BLOCKED-001", "阻塞视图", "阻塞工作包"),
    "completed": ("FLOW-VIEW-COMPLETED-001", "已完成视图", "已完成工作包"),
}


@dataclass(frozen=True)
class WorkItem:
    filename: str
    doc_id: str
    title: str
    status: str
    updated_at: str


def load_work_items(root: Path) -> Dict[str, WorkItem]:
    items: Dict[str, WorkItem] = {}
    for path in sorted((root / "docs/50_plans/work_items").glob("*.md")):
        meta = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not meta or meta.get("doc_type") != "work-item":
            continue
        items[path.name] = WorkItem(
            filename=path.name,
            doc_id=meta.get("doc_id", ""),
            title=meta.get("title", path.stem),
            status=meta.get("status", ""),
            updated_at=meta.get("updated_at", ""),
        )
    return items


def load_roadmap_states(root: Path) -> Dict[str, List[str]]:
    states: Dict[str, List[str]] = {}
    roadmap = root / "docs/50_plans/CURRENT_ROADMAP.md"
    for line in roadmap.read_text(encoding="utf-8").splitlines():
        link = WORK_ITEM_LINK.search(line)
        if not link:
            continue
        token = STATUS_TOKEN.search(line)
        states.setdefault(link.group(1), []).append(token.group(1) if token else "")
    return states


def _view_for(status: str) -> str | None:
    if status in {"active", "proposed"}:
        return "active"
    if status == "blocked":
        return "blocked"
    if status in {"completed", "cancelled", "archived"}:
        return "completed"
    return None


def render_views(root: Path) -> Dict[str, str]:
    items = load_work_items(root)
    serial = [item.__dict__ for item in sorted(items.values(), key=lambda value: value.doc_id)]
    input_hash = hashlib.sha256(
        json.dumps(serial, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    updated_at = max((item.updated_at for item in items.values()), default="2026-09-13")
    rendered: Dict[str, str] = {}
    for view, (doc_id, title, heading) in VIEW_META.items():
        selected = sorted(
            (item for item in items.values() if _view_for(item.status) == view),
            key=lambda item: item.doc_id,
        )
        lines = [
            "---",
            f"doc_id: {doc_id}",
            f"title: {title}",
            "doc_type: generated",
            "status: generated",
            "version: 1.0",
            "created_at: 2026-09-12",
            f"updated_at: {updated_at}",
            "owner: FLOW",
            "generator_ref: scripts/documentation/plan_views.py",
            f"input_hash: {input_hash}",
            "applies_to: planning",
            "---",
            "",
            f"# {heading}",
            "",
            "> 本页由工作包元数据确定性生成，请勿手工修改。",
            "",
        ]
        if selected:
            lines.extend(
                f"- [{item.title}](../work_items/{item.filename}) — `{item.status}`"
                for item in selected
            )
        else:
            lines.append("- 暂无")
        lines.append("")
        rendered[view] = "\n".join(lines)
    return rendered


def write_views(root: Path) -> None:
    view_dir = root / "docs/50_plans/views"
    view_dir.mkdir(parents=True, exist_ok=True)
    for view, content in render_views(root).items():
        (view_dir / f"{view}.md").write_text(content, encoding="utf-8")


def check(root: Path) -> List[str]:
    errors: List[str] = []
    items = load_work_items(root)
    roadmap = load_roadmap_states(root)
    for filename, item in items.items():
        states = roadmap.get(filename, [])
        if not states:
            errors.append(f"{filename} missing from CURRENT_ROADMAP")
        elif len(states) != 1:
            errors.append(f"{filename} appears {len(states)} times in CURRENT_ROADMAP")
        elif states[0] != item.status:
            errors.append(
                f"{filename} status mismatch: work-item={item.status} roadmap={states[0] or 'missing'}"
            )
    for filename in roadmap:
        if filename not in items:
            errors.append(f"CURRENT_ROADMAP references unknown work-item {filename}")
    for view, expected in render_views(root).items():
        path = root / "docs/50_plans/views" / f"{view}.md"
        if not path.is_file() or path.read_text(encoding="utf-8") != expected:
            errors.append(f"generated view drift: {path.relative_to(root)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        write_views(ROOT)
        return 0
    errors = check(ROOT)
    for error in errors:
        print(f"ERROR {error}")
    print(f"plan views: {'PASS' if not errors else 'FAIL'}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
