#!/usr/bin/env python3
"""Deterministic KB manifest generator (plan FLOW-DOC-MIGRATION-001, Task 1 Step 6).

kb_manifest.py --write  从 docs/knowledge-base/ 全量生成
    99_manifest/inventory.tsv（relative_path<TAB>size<TAB>modified_time<TAB>mime）
    99_manifest/sha256sums.txt（<sha256>  ./<path>）
kb_manifest.py --check  在临时目录重建并对账；同时重验每条 SHA-256。

约定（与既有 99_manifest 手工约定一致并固化为机器合同）：
- 两份 manifest 排除自身；路径按 UTF-8 字节序排序；
- modified_time 为文件系统 mtime（ISO-8601 +08:00）。确定性边界：--check 对
  inventory.tsv 的 mtime 列豁免（fresh clone 中 fs mtime 不可复现，逐字节会
  在 CI 必挂），其余列逐字节比较；sha256sums.txt 仍逐字节比较。
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

KB_DIR = Path("docs/knowledge-base")
MANIFEST_DIR = KB_DIR / "99_manifest"
INV_NAME = "inventory.tsv"
SUMS_NAME = "sha256sums.txt"
INV_HEADER = ["relative_path", "size_bytes", "modified_time", "mime_type"]

MIME_BY_EXT = {
    ".md": "text/markdown", ".markdown": "text/markdown",
    ".html": "text/html", ".htm": "text/html",
    ".txt": "text/plain",
    ".json": "application/json", ".jsonl": "application/x-ndjson",
    ".pdf": "application/pdf",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
    ".gz": "application/gzip", ".zip": "application/zip",
    ".yaml": "application/yaml", ".yml": "application/yaml",
    ".tsv": "text/tab-separated-values", ".csv": "text/csv",
    ".py": "text/x-python", ".ts": "text/javascript", ".tsx": "text/javascript",
    ".js": "text/javascript", ".mjs": "text/javascript",
    ".sh": "text/x-shellscript", ".sql": "application/sql", ".toml": "text/plain",
}


def _mime(path: Path) -> str:
    return MIME_BY_EXT.get(path.suffix.lower(), "application/octet-stream")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _mtime_iso(p: Path) -> str:
    st = p.stat().st_mtime
    return datetime.datetime.fromtimestamp(st).astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S+08:00")


def collect(root: Path) -> List[Tuple[str, int, str, str, str]]:
    """返回 (rel_path, size, mtime, mime, sha256)，UTF-8 字节序，排除 manifest 自身。"""
    base = root / KB_DIR
    out: List[Tuple[str, int, str, str, str]] = []
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        rel = p.relative_to(base).as_posix()
        if rel.startswith("99_manifest/"):
            continue
        data = p.read_bytes()
        out.append((rel, len(data), _mtime_iso(p), _mime(p), _sha256(data)))
    out.sort(key=lambda r: r[0].encode("utf-8"))
    return out


def render_inventory(rows: List[Tuple[str, int, str, str, str]]) -> bytes:
    import io

    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(INV_HEADER)
    for rel, size, mtime, mime, _sha in rows:
        w.writerow([rel, size, mtime, mime])
    return buf.getvalue().encode("utf-8")


def render_sums(rows: List[Tuple[str, int, str, str, str]]) -> bytes:
    lines = [f"{sha}  ./{rel}" for rel, _s, _m, _mime, sha in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write(root: Path) -> None:
    rows = collect(root)
    mdir = root / MANIFEST_DIR
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / INV_NAME).write_bytes(render_inventory(rows))
    (mdir / SUMS_NAME).write_bytes(render_sums(rows))


def parse_inventory(raw: bytes) -> List[Tuple[str, str, str, str, str]]:
    """解析为 (path, size, mtime, mime, sha)——sha 取自 sha256sums 对账表。"""
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "\t".join(INV_HEADER):
        raise AssertionError("inventory.tsv 表头不符")
    return [tuple(line.split("\t")) for line in lines[1:] if line]  # type: ignore[misc]


def check(root: Path) -> bool:
    rows = collect(root)
    want_inv = render_inventory(rows)
    want_sums = render_sums(rows)
    mdir = root / MANIFEST_DIR
    got_inv = (mdir / INV_NAME).read_bytes()
    got_sums = (mdir / SUMS_NAME).read_bytes()

    # sha256sums.txt 逐字节
    if got_sums != want_sums:
        want_map = dict(
            (ln.split("  ./", 1)[1], ln.split("  ", 1)[0])
            for ln in want_sums.decode().splitlines())
        got_map = dict(
            (ln.split("  ./", 1)[1], ln.split("  ", 1)[0])
            for ln in got_sums.decode().splitlines())
        detail = []
        for p in sorted(set(want_map) | set(got_map))[:5]:
            if want_map.get(p) != got_map.get(p):
                detail.append(f"{p}: want {want_map.get(p)} got {got_map.get(p)}")
        raise AssertionError("sha256sums.txt 漂移:\n" + "\n".join(detail))

    # inventory.tsv：除 mtime 列外逐字段
    want_rows = parse_inventory(want_inv)
    got_rows = parse_inventory(got_inv)
    norm = lambda rs: [(r[0], r[1], r[3]) for r in rs]  # noqa: E731  path,size,mime
    if norm(want_rows) != norm(got_rows):
        raise AssertionError("inventory.tsv（path/size/mime）与重建结果不一致")

    # 每条 SHA-256 对实际文件重验
    base = root / KB_DIR
    for rel, _s, _m, _mime, sha in rows:
        actual = _sha256((base / rel).read_bytes())
        if actual != sha:
            raise AssertionError(f"SHA-256 漂移: {rel}")
    return True


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    root = Path.cwd()
    if args.write:
        write(root)
        print(f"KB manifest written ({len(collect(root))} files)")
        return 0
    try:
        check(root)
        print("KB manifest check: PASS")
        return 0
    except AssertionError as exc:
        print(f"KB manifest check: FAIL\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
