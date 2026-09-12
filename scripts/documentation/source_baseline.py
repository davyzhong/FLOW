#!/usr/bin/env python3
"""Source baseline builder/checker (plan FLOW-DOC-MIGRATION-001, Task 2 Step 5c).

职责：从固定的 source-inputs.yaml 生成、冻结和校验来源级基线
（逐条 source_id 行 + 文件自身 SHA-256），支持批准的 count 订正。
仅使用标准库；YAML 输入只使用本文件定义的受限子集解析器
（与 metadata.py 的纯 Python 约定一致，CI 系统 Python 无 PyYAML 依赖）。

TSV 列（UTF-8 字节序按 source_id 排序）：
source_id, snapshot_id, locator, title, author, bytes, sha256,
duplicate_group, k_route, availability, evidence_path
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

HEADER = [
    "source_id", "snapshot_id", "locator", "title", "author", "bytes",
    "sha256", "duplicate_group", "k_route", "availability", "evidence_path",
]

ENTRY_HEADER = ["source_id", "locator", "title", "author", "k_route",
                "availability", "evidence_path", "duplicate_group"]


class BaselineError(ValueError):
    """来源基线输入或校验失败。"""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_inputs(text: str) -> dict:
    """受限 YAML 子集：顶层标量、块列表（corrections/groups）与一层嵌套字段。

    groups 的列表项展开为 dict；corrections 的列表项按 inline JSON 解析。
    """
    result: Dict[str, object] = {}
    groups: List[dict] = []
    corrections: List[dict] = []
    current: Optional[dict] = None
    target: Optional[str] = None  # 当前列表名：groups / corrections
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith(" ") and raw.rstrip().endswith(":") and ":" in raw:
            key = raw.strip()[:-1]
            if key in ("groups", "corrections"):
                target = key
                current = None
                result[key] = [] if key not in result else result[key]
            else:
                target = None
                result[key] = ""
            continue
        if raw.lstrip().startswith("- "):
            item = raw.lstrip()[2:].strip()
            if target == "corrections":
                corrections.append(json.loads(item))
            elif target == "groups":
                current = {}
                groups.append(current)
                key, _, value = item.partition(": ")
                if _:
                    current[key.strip()] = value.strip().strip("'\"")
            continue
        stripped = raw.strip()
        if stripped and current is not None:
            key, _, value = stripped.partition(": ")
            if _:
                current[key.strip()] = value.strip().strip("'\"")
            continue
        key, _, value = raw.partition(": ")
        if key.strip() and not raw.startswith(" "):
            value = value.strip()
            if value.startswith("[") or value.startswith("{"):
                result[key.strip()] = json.loads(value)
            else:
                result[key.strip()] = value.strip("'\"")
    result["groups"] = groups
    # 块列表与 inline JSON 二选一：块列表非空优先，否则保留 inline 解析结果
    result["corrections"] = corrections if corrections else result.get("corrections", [])
    return result


def _git_blob(root: Path, treeish: str, rel: str) -> Optional[bytes]:
    proc = subprocess.run(
        ["git", "cat-file", "blob", f"{treeish}:{rel}"],
        cwd=str(root), capture_output=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def _wechat_rows(root: Path, snapshot_id: str, group: dict,
                 treeish: Optional[str]) -> List[List[object]]:
    proc = subprocess.run(
        ["git", "ls-files", "-z", "--", group["root"]],
        cwd=str(root), check=True, capture_output=True,
    )
    tracked = [p for p in proc.stdout.decode("utf-8").split("\0") if p]
    rows: List[List[object]] = []
    import fnmatch

    pattern = group.get("pattern", "**/article.md")
    for rel in sorted(tracked):
        if not fnmatch.fnmatch(rel, pattern) and not rel.endswith(pattern.lstrip("*")):
            continue
        base = rel.rsplit("/", 1)[0]
        if treeish is not None:
            content = _git_blob(root, treeish, rel)
            if content is None:
                raise BaselineError(f"locator 不在 checkpoint tree 内: {rel}")
        else:
            content = (root / rel).read_bytes()
        title, author = "", ""
        meta_path = root / base / "meta.json"
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                title = str(meta.get("title", ""))
                author = str(meta.get("author", ""))
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        rows.append([
            f"wechat-{_sha256(content)[:12]}", snapshot_id, rel, title, author,
            len(content), _sha256(content), "", "", "full-text-in-repo", rel,
        ])
    return rows


def _entry_rows(root: Path, snapshot_id: str, group: dict) -> List[List[object]]:
    path = root / group["path"]
    if not path.is_file():
        raise BaselineError(f"entries 文件不存在: {group['path']}")
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        if header != ENTRY_HEADER:
            raise BaselineError(f"entries 表头不符 {group['path']}: {header}")
        rows: List[List[object]] = []
        for rec in reader:
            if not rec:
                continue
            if len(rec) != len(ENTRY_HEADER):
                raise BaselineError(f"entries 行字段数错误: {rec}")
            sid, locator, title, author, k_route, availability, evidence, dup = rec
            if locator.startswith("repo:") and not (root / locator[5:]).is_file():
                raise BaselineError(f"repo locator 文件不存在: {locator}")
            # entries 8 列 → baseline 11 列（bytes/sha256 留空：locator-only）
            rows.append([sid, snapshot_id, locator, title, author, "", "",
                         dup, k_route, availability, evidence])
    return rows


def build(root: Path, inputs_path: Path, snapshot_id: str, expected_count: int,
          output: Path, treeish: Optional[str] = None) -> List[List[object]]:
    """生成基线 TSV；count、唯一性或定位符失败即抛 BaselineError（fail-closed）。"""
    spec = parse_inputs(inputs_path.read_text(encoding="utf-8"))
    if str(spec.get("snapshot_id", "")) != snapshot_id:
        raise BaselineError(
            f"snapshot_id 不一致: inputs={spec.get('snapshot_id')} arg={snapshot_id}")
    rows: List[List[object]] = []
    for group in spec.get("groups", []):
        if group.get("type") == "wechat-archive-dir":
            rows.extend(_wechat_rows(root, snapshot_id, group, treeish))
        elif group.get("type") == "entries-tsv":
            rows.extend(_entry_rows(root, snapshot_id, group))
        else:
            raise BaselineError(f"未知 group type: {group.get('type')}")
    ids = [r[0] for r in rows]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise BaselineError(f"重复 source_id: {sorted(duplicates)[:5]}")
    rows.sort(key=lambda r: str(r[0]).encode("utf-8"))
    corrections = spec.get("corrections", [])
    delta = sum(int(c.get("delta", 0)) for c in corrections)
    if expected_count + delta != len(rows):
        raise BaselineError(
            f"count 不符: 预期 {expected_count} + 订正 {delta} != 实际 {len(rows)}"
            f"（未经批准不得放宽，需把订正写入 source-inputs.yaml 的 corrections）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(rows)
    return rows


def write_hash_file(baseline: Path, hash_file: Path) -> None:
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(f"{_sha256(baseline.read_bytes())}  {baseline.name}\n",
                         encoding="utf-8")


def check(root: Path, baseline: Path, hash_file: Path,
          metadata: Optional[Path] = None) -> bool:
    """校验：文件哈希对账、结构（字段数/唯一/排序）、full-text 条目内容重验。"""
    want = hash_file.read_text(encoding="utf-8").split()[0]
    got = _sha256(baseline.read_bytes())
    if want != got:
        raise ValueError(f"baseline 文件哈希不符: lock={want} actual={got}")
    with open(baseline, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        if header != HEADER:
            raise ValueError(f"baseline 表头不符: {header}")
        ids: List[str] = []
        for rec in reader:
            if not rec:
                continue
            if len(rec) != len(HEADER):
                raise ValueError(f"行字段数错误: {rec[:3]}")
            sid, snap, locator = rec[0], rec[1], rec[2]
            ids.append(sid)
            if rec[9] == "full-text-in-repo":
                p = root / locator
                if not p.is_file():
                    raise ValueError(f"full-text 条目文件缺失: {locator}")
                if _sha256(p.read_bytes()) != rec[6]:
                    raise ValueError(f"full-text 条目内容漂移: {locator}")
        if ids != sorted(ids, key=lambda s: s.encode("utf-8")):
            raise ValueError("baseline 未按 source_id UTF-8 字节序排序")
        if len(ids) != len(set(ids)):
            raise ValueError("source_id 存在重复")
    if metadata is not None:
        text = metadata.read_text(encoding="utf-8")
        m = re.search(r"source_baseline\.tsv: ([0-9a-f]{64})", text)
        if m and m.group(1) != got:
            raise ValueError("baseline.yaml 中的 source-baseline 哈希引用不一致")
    return True


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--input-manifest", type=Path, required=True)
    b.add_argument("--snapshot-id", required=True)
    b.add_argument("--expected-count", type=int, required=True)
    b.add_argument("--output", type=Path, required=True)
    b.add_argument("--hash-output", type=Path, required=True)
    b.add_argument("--tree-ish", dest="treeish")
    c = sub.add_parser("check")
    c.add_argument("--baseline", type=Path, required=True)
    c.add_argument("--hash-file", type=Path, required=True)
    c.add_argument("--metadata", type=Path)
    args = ap.parse_args(argv)
    root = Path.cwd()
    try:
        if args.cmd == "build":
            rows = build(root, args.input_manifest, args.snapshot_id,
                         args.expected_count, args.output, treeish=args.treeish)
            write_hash_file(args.output, args.hash_output)
            print(f"source baseline written: {len(rows)} rows -> {args.output}")
            return 0
        check(root, args.baseline, args.hash_file, args.metadata)
        print("source baseline check: PASS")
        return 0
    except (BaselineError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
