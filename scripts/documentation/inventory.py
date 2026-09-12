#!/usr/bin/env python3
"""Documentation inventory scanner (plan FLOW-DOC-MIGRATION-001, Tasks 1-2).

职责：以 Git 跟踪文件为主清单生成文档/消费者/不可变锁/存储分级清单，
全部输出确定（UTF-8 路径排序、无时间戳），支持 --check 基线对账。
仅使用标准库（Python 3.9+）。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

# 计划 §0：永久原位目录（设计规范 §4.1 legacy immutable roots）
IMMUTABLE_ROOTS = (
    "docs/knowledge-base/01_conversations/raw/",
    "docs/knowledge-base/02_research/original/",
    "docs/knowledge-base/03_assets/logistics_daily/",
    "docs/knowledge-base/03_assets/external_reference/",
    "docs/knowledge-base/05_design/approved/",
)

KIND_BY_EXT = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".tsv": "tsv",
    ".csv": "csv",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".mjs": "javascript",
    ".sh": "shell",
    ".html": "html",
    ".css": "css",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".pdf": "pdf",
    ".pptx": "presentation",
    ".docx": "document",
    ".xlsx": "spreadsheet",
    ".zip": "archive",
    ".jsonl": "jsonl",
    ".sql": "sql",
    ".toml": "toml",
    ".txt": "text",
}

# 消费者扫描仅针对可变文本文件（不可变档案中的旧链接不改写，计划 Task 12 Step 2）
CONSUMER_TEXT_KINDS = {
    "markdown", "yaml", "json", "tsv", "csv", "python", "typescript",
    "javascript", "shell", "html", "css", "text", "jsonl", "sql", "toml",
}

# V1.1 设计 §4.9：github 普通提交单文件上限 / 热档阈值
RELEASE_SIZE_LIMIT = 100 * 1024 * 1024
LFS_SIZE_THRESHOLD = 2 * 1024 * 1024

# docs/ 路径字面量（含中文文件名；排除常见成对符号与空白）
DOCS_PATH_RE = re.compile(r"docs/[^\s\"'`<>()[\]{}，。；：！？、]+")


@dataclass
class Row:
    path: str
    kind: str
    mutability: str
    consumer_count: int
    sha256: str
    size: int


@dataclass
class Consumer:
    consumer_path: str
    line: int
    referenced_path: str


@dataclass
class StorageRow:
    path: str
    size: int
    sha256: str
    proposed_tier: str
    reason: str


# 文档元数据合同不适用的区域 = 五个不可变根 + 基线设施 + 已移交微信档案（M2 拟追加 immutable delta）
DOC_CONTRACT_EXEMPT_PREFIXES = IMMUTABLE_ROOTS + (
    "docs/knowledge-base/00_governance/migration/",
    "docs/knowledge-base/99_manifest/",
    "docs/knowledge-base/08_wechat_sources/",
)

# 基线设施自排除：迁移登记产物不进入清单（自指会导致基线永远漂移）
SELF_EXCLUDE_PREFIXES = ("docs/knowledge-base/00_governance/migration/",)
SELF_EXCLUDE_EXACT = ("docs/knowledge-base/00_governance/immutable-paths.lock.tsv",)


def git_tracked_files(root: Path) -> List[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=str(root), check=True, capture_output=True,
    ).stdout.decode("utf-8")
    return [
        p for p in out.split("\0")
        if p and not p.startswith(SELF_EXCLUDE_PREFIXES) and p not in SELF_EXCLUDE_EXACT
    ]


def git_tree_files(root: Path, treeish: str) -> List[str]:
    """计划 Task 1 Step 3：checkpoint tree 是永久基线主清单（blob 只读，不含工作树漂移）。"""
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--", treeish],
        cwd=str(root), capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"bad tree-ish {treeish!r}: {proc.stderr.decode(errors='replace').strip()}")
    out = proc.stdout.decode("utf-8")
    files = []
    for entry in out.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, otype, _sha = meta.split()
        if otype != "blob":
            continue
        if path.startswith(SELF_EXCLUDE_PREFIXES) or path in SELF_EXCLUDE_EXACT:
            continue
        files.append(path)
    return files


def git_blob(root: Path, treeish: str, rel: str) -> bytes:
    return subprocess.run(
        ["git", "cat-file", "blob", f"{treeish}:{rel}"],
        cwd=str(root), check=True, capture_output=True,
    ).stdout


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_kind(path: str) -> str:
    return KIND_BY_EXT.get(Path(path).suffix.lower(), "other")


def is_immutable(rel: str) -> bool:
    return any(rel.startswith(root) for root in IMMUTABLE_ROOTS)


def find_consumers(root: Path, tracked: Iterable[str], treeish: Optional[str] = None) -> List[Consumer]:
    consumers: List[Consumer] = []
    tracked_set = set(tracked)
    for rel in sorted(tracked_set):
        if is_immutable(rel) or classify_kind(rel) not in CONSUMER_TEXT_KINDS:
            continue
        try:
            if treeish is not None:
                raw = git_blob(root, treeish, rel)
            else:
                raw = (root / rel).read_bytes()
            text = raw.decode("utf-8")
        except (UnicodeDecodeError, ValueError, subprocess.CalledProcessError):
            continue  # 二进制误判为文本：跳过不阻塞
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in DOCS_PATH_RE.finditer(line):
                ref = match.group(0).rstrip(".,;:)】」』")
                # 引用可指向仓库内任一 docs 路径（文件或目录前缀）
                if ref in tracked_set:
                    consumers.append(Consumer(rel, lineno, ref))
    return consumers


def build_inventory(root: Path, treeish: Optional[str] = None) -> List[Row]:
    tracked = (
        git_tree_files(root, treeish) if treeish is not None else git_tracked_files(root)
    )
    consumers = find_consumers(root, tracked, treeish=treeish)
    count_by_ref = {}
    for c in consumers:
        count_by_ref[c.referenced_path] = count_by_ref.get(c.referenced_path, 0) + 1
    rows: List[Row] = []
    for rel in sorted(tracked):
        if treeish is not None:
            content = git_blob(root, treeish, rel)
            size = len(content)
            sha = hashlib.sha256(content).hexdigest()
        else:
            p = root / rel
            if not p.is_file() or p.is_symlink():
                continue  # 不跟随符号链接，跳过坏条目
            size = p.stat().st_size
            sha = sha256_of(p)
        rows.append(Row(
            path=rel,
            kind=classify_kind(rel),
            mutability="immutable" if is_immutable(rel) else "mutable",
            consumer_count=count_by_ref.get(rel, 0),
            sha256=sha,
            size=size,
        ))
    return rows


def build_storage(rows: List[Row]) -> List[StorageRow]:
    """V1.1 设计 §4.9：判定顺序 D(重复) → C(>100MB/归档快照) → B(>2MB 二进制) → A。

    proposed_tier 仅为登记建议，不执行任何移动。
    """
    seen_hash = {}
    for r in rows:  # 找出清单内重复内容（D 候选需人工对账确认）
        seen_hash.setdefault(r.sha256, []).append(r.path)
    out: List[StorageRow] = []
    for r in sorted(rows, key=lambda x: x.path):
        dups = [p for p in seen_hash[r.sha256] if p != r.path]
        if r.mutability == "immutable":
            # 不可变档案永久原位：不参与 LFS/Release/冗余清除（计划 §0）
            tier, reason = "immutable-keep", "legacy-immutable-root"
        elif r.kind in ("markdown", "yaml", "json", "tsv", "csv", "python", "typescript",
                        "javascript", "shell", "html", "css", "text", "jsonl", "sql", "toml"):
            tier, reason = "A", "text"
        elif dups:
            tier, reason = "D", "duplicate-hash:" + dups[0]
        elif r.size > RELEASE_SIZE_LIMIT or r.kind == "archive":
            tier, reason = "C", "archive-or-over-100MB"
        elif r.size > LFS_SIZE_THRESHOLD:
            tier, reason = "B", "binary-over-2MB"
        else:
            tier, reason = "A", "small-binary"
        out.append(StorageRow(r.path, r.size, r.sha256, tier, reason))
    return out


def write_tsv(path: Path, header: List[str], rows: Iterable[Iterable[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        for row in rows:
            w.writerow(list(row))


def repo_head(root: Path) -> Optional[str]:
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(root),
        capture_output=True, text=True,
    )
    return out.stdout.strip() if out.returncode == 0 else None


def generate(root: Path, output_dir: Path, write_lock: Optional[Path] = None,
             treeish: Optional[str] = None) -> dict:
    """Generate all inventory artifacts deterministically; return manifest of hashes."""
    rows = build_inventory(root, treeish=treeish)
    tracked = (
        git_tree_files(root, treeish) if treeish is not None else git_tracked_files(root)
    )
    consumers = find_consumers(root, tracked, treeish=treeish)
    storage = build_storage(rows)
    immutable = [r for r in rows if r.mutability == "immutable"]

    write_tsv(
        output_dir / "document-inventory.tsv",
        ["path", "kind", "mutability", "consumer_count", "size", "sha256"],
        ([r.path, r.kind, r.mutability, r.consumer_count, r.size, r.sha256] for r in rows),
    )
    write_tsv(
        output_dir / "consumer-registry.tsv",
        ["consumer_path", "line", "referenced_path"],
        ([c.consumer_path, c.line, c.referenced_path] for c in consumers),
    )
    write_tsv(
        output_dir / "storage-inventory.tsv",
        ["path", "size", "sha256", "proposed_tier", "reason"],
        ([s.path, s.size, s.sha256, s.proposed_tier, s.reason] for s in storage),
    )
    if write_lock is not None:
        write_tsv(
            write_lock,
            ["path", "sha256", "baseline"],
            ([r.path, r.sha256, "m0"] for r in immutable),
        )
    manifest = {}
    for name in ("document-inventory.tsv", "consumer-registry.tsv", "storage-inventory.tsv"):
        manifest[name] = sha256_of(output_dir / name)
    if write_lock is not None:
        manifest[write_lock.name] = sha256_of(write_lock)
    return manifest


def write_baseline(output_dir: Path, root: Path, manifest: dict,
                   treeish: Optional[str] = None) -> None:
    lines = [
        "# M0 baseline (generated; hand-edit only the exempt list)",
        f"checkpoint: {treeish or repo_head(root) or 'unknown'}",
        f"generator: scripts/documentation/inventory.py",
    ]
    lines += [f"{k}: {v}" for k, v in sorted(manifest.items())]
    (output_dir / "baseline.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_baseline(root: Path, baseline_path: Path, treeish: Optional[str] = None) -> int:
    baseline = {}
    for line in baseline_path.read_text(encoding="utf-8").splitlines():
        if ": " in line and not line.startswith("#"):
            k, v = line.split(": ", 1)
            baseline[k] = v
    stored = {k: v for k, v in baseline.items() if k.endswith(".tsv")}
    output_dir = baseline_path.parent
    frozen_tree = treeish or baseline.get("checkpoint")
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        fresh = generate(root, Path(td), treeish=frozen_tree)  # 同一 checkpoint 重生成
    ok = True
    for name, want in sorted(stored.items()):
        got = fresh.get(name)
        if got is None:
            # 非重生成工件（如不可变锁位于 baseline 目录的兄弟位置）：校验现存文件
            candidates = [output_dir / name, output_dir.parent / name, root / name]
            cand = next((c for c in candidates if c.is_file()), None)
            got = sha256_of(cand) if cand else "missing"
        if got != want:
            print(f"BASELINE MISMATCH {name}: want {want} got {got}", file=sys.stderr)
            ok = False
    print("baseline check: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tree-ish", dest="treeish",
                    help="checkpoint tree to baseline (blob-level, ignores working tree)")
    ap.add_argument("--working-tree", action="store_true",
                    help="scan the current working tree instead (must not mix with --tree-ish)")
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--write-lock", type=Path, help="also write immutable lock tsv to this path")
    ap.add_argument("--check", type=Path, help="verify regenerable outputs against baseline")
    args = ap.parse_args(argv)

    root = Path(args.repo).resolve()
    if args.check:
        return check_baseline(root, args.check.resolve(), treeish=args.treeish)
    if args.output_dir is None:
        ap.error("--output-dir or --check required")
    if args.treeish and args.working_tree:
        ap.error("--tree-ish and --working-tree are mutually exclusive")
    manifest = generate(root, args.output_dir, args.write_lock, treeish=args.treeish)
    write_baseline(args.output_dir, root, manifest, treeish=args.treeish)
    print(f"inventory written to {args.output_dir} ({len(manifest)} artifacts hashed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
