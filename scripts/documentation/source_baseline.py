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
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

HEADER = [
    "source_id", "snapshot_id", "locator", "title", "author", "bytes",
    "sha256", "duplicate_group", "k_route", "availability", "evidence_path",
]

ENTRY_HEADER = ["source_id", "locator", "title", "author", "k_route",
                "availability", "evidence_path", "duplicate_group"]

V2_REGISTRY_HEADER = ["source_id", "source_type", "normalized_origin", "author",
                      "first_title", "first_body_sha256", "locator", "snapshot_id"]
V2_BASELINE_HEADER = ["source_id", "snapshot_id", "locator", "title", "author",
                      "file_sha256", "body_sha256", "image_set_sha256",
                      "has_summary_appendix", "has_image_appendix", "source_type",
                      "vault_commit", "vault_tree", "source_url_or_external_id",
                      "summary_model_version", "image_model_version", "k_domain",
                      "authority_level", "sensitivity", "availability", "flow_disposition"]
V2_DIFF_HEADER = ["source_id", "presence_change", "path_changed", "body_changed",
                  "enrichment_changed", "old_locator", "new_locator"]
WIKI_TERMS = ("财务", "经营", "预算", "成本", "现金", "应收", "指标", "分析",
              "报告", "物流", "业财")
APPENDIX_RE = re.compile(
    r"(?:<!--\s*)?%%davybase-(image-notes|summary)-begin%%(?:\s*-->)?"
    r".*?(?:<!--\s*)?%%davybase-\1-end%%(?:\s*-->)?",
    re.IGNORECASE | re.DOTALL,
)


class BaselineError(ValueError):
    """来源基线输入或校验失败。"""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalized_text(data: bytes) -> str:
    return unicodedata.normalize("NFC", data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n"))


def _body_text(text: str) -> str:
    return APPENDIX_RE.sub("", text)


def _read_v2_inputs(path: Path) -> dict:
    """Read the deliberately small, JSON-compatible YAML shape used by build-v2."""
    result: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise BaselineError(f"无效的 v2 输入清单行: {line}")
        value = value.strip()
        if value.startswith("[") or value.startswith("{"):
            result[key.strip()] = json.loads(value)
        else:
            result[key.strip()] = value.strip("'\"")
    if not result.get("snapshot_id") or not result.get("vault_root") or not result.get("source_roots"):
        raise BaselineError("v2 输入清单必须包含 snapshot_id、vault_root、source_roots")
    return result


def _previous_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if not reader.fieldnames or "source_id" not in reader.fieldnames or "locator" not in reader.fieldnames:
            raise BaselineError(f"previous baseline 缺少 source_id/locator: {path}")
        rows = {}
        for row in reader:
            if row["source_id"] in rows:
                raise BaselineError(f"previous baseline source_id 重复: {row['source_id']}")
            rows[row["source_id"]] = row
        return rows


def _image_inventory(vault: Path, source_file: Path, markdown: str,
                     treeish: Optional[str] = None) -> tuple[str, bool]:
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)|!\[\[([^\]]+)\]\]", markdown)
    entries = []
    for index, pair in enumerate(refs, 1):
        raw = next((value for value in pair if value), "").split("|", 1)[0]
        target = (source_file.parent / raw).resolve()
        if not target.is_file():
            target = (vault / raw).resolve()
        if not target.is_relative_to(vault.resolve()):
            entries.append([index, unicodedata.normalize("NFC", raw), "missing"])
        else:
            relative = os.path.relpath(target, vault).replace(os.sep, "/")
            if treeish:
                content = _git_blob(vault, treeish, relative)
            elif target.is_file():
                content = target.read_bytes()
            else:
                content = None
            entries.append([index, unicodedata.normalize("NFC", relative), _sha256(content) if content is not None else "missing"])
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _sha256(encoded), bool(re.search(r"%%davybase-image-notes-begin%%", markdown, re.I))


def _source_title_author(path: Path, text: str) -> tuple[str, str, str]:
    title = ""
    author = ""
    meta = path.parent / "meta.json"
    if meta.is_file():
        try:
            metadata = json.loads(meta.read_text(encoding="utf-8"))
            title = str(metadata.get("title", ""))
            author = str(metadata.get("author", ""))
            origin = str(metadata.get("url") or metadata.get("note_id") or metadata.get("id") or "")
            if origin:
                return title or path.stem, author, origin
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            pass
    title_match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    title = title or (title_match.group(1).strip() if title_match else path.stem)
    author_match = re.search(r"(?m)^(?:作者|author)\s*[:：]\s*(.+)$", text, re.I)
    author = author or (author_match.group(1).strip() if author_match else "")
    return title, author, ""


def _source_type(locator: str) -> str:
    if "/processed/微信知识库/" in f"/{locator}/":
        return "wechat"
    if "/wiki/" in f"/{locator}/":
        return "wiki"
    return "domain-note"


def _new_local_id(source_type: str, origin: str, author: str, title: str, body_hash: str) -> str:
    payload = json.dumps(["flow-source-id-v1", source_type, origin, author, title, body_hash],
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "SRC-LOCAL-v1-" + _sha256(payload)[:20]


def _write_tsv(path: Path, header: list[str], rows: list[list[object]]) -> bytes:
    from io import StringIO
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    data = buffer.getvalue().encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def build_v2(manifest_path: Path, inputs_path: Path, registry_path: Path,
             baseline_path: Path, diff_path: Path, previous_path: Path,
             previous_tree: Optional[str] = None) -> list[dict[str, str]]:
    """Create deterministic source registry, baseline and four-dimension diff.

    Only explicit allowlist roots are indexed. Existing source IDs are retained by
    exact prior locator; no title-similarity matching is attempted.
    """
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "accepted" or manifest.get("snapshot_kind") != "working_tree":
        raise BaselineError("snapshot manifest 必须是 accepted working_tree")
    inputs = _read_v2_inputs(inputs_path)
    if inputs["snapshot_id"] != manifest.get("snapshot_id"):
        raise BaselineError("input manifest 与 accepted snapshot_id 不一致")
    vault = Path(inputs["vault_root"]).resolve(strict=True)
    prior = _previous_rows(previous_path)
    prior_by_locator = {row["locator"].removeprefix("vault:").lstrip("/"): row for row in prior.values()}
    paths: set[Path] = set()
    for root_name in inputs["source_roots"]:
        root = (vault / root_name).resolve()
        if not root.is_relative_to(vault) or not root.is_dir():
            raise BaselineError(f"来源 root 不存在或越界: {root_name}")
        for path in root.rglob("*.md"):
            if path.is_file() and not path.is_symlink():
                if root_name.rstrip("/") == "wiki" and not any(term in path.name or term in path.read_text(encoding="utf-8", errors="replace")[:10000] for term in WIKI_TERMS):
                    continue
                paths.add(path)
    registry_rows: list[list[object]] = []
    baseline_rows: list[list[object]] = []
    current: dict[str, dict[str, str]] = {}
    for path in sorted(paths, key=lambda item: os.fsencode(item.relative_to(vault).as_posix())):
        locator = unicodedata.normalize("NFC", path.relative_to(vault).as_posix())
        raw = path.read_bytes()
        text = _normalized_text(raw)
        body = _body_text(text)
        body_hash = _sha256(body.encode("utf-8"))
        title, author, external_origin = _source_title_author(path, text)
        stype = _source_type(locator)
        previous = prior_by_locator.get(locator)
        origin = external_origin or locator
        sid = previous["source_id"] if previous else _new_local_id(stype, origin, author, title, body_hash)
        image_hash, has_image_appendix = _image_inventory(vault, path, text)
        has_summary = bool(re.search(r"%%davybase-summary-begin%%", text, re.I))
        baseline_rows.append([sid, inputs["snapshot_id"], locator, title, author,
                              _sha256(raw), body_hash, image_hash, str(has_summary).lower(),
                              str(has_image_appendix).lower(), stype,
                              manifest["candidate"]["head"], manifest["candidate"]["tree"],
                              external_origin, "not-recorded", "not-recorded", "pending-review",
                              "unclassified", "unclassified", "readable-full-text", "pending-review"])
        registry_rows.append([sid, stype, origin, author, title, body_hash, locator, inputs["snapshot_id"]])
        current[sid] = {"locator": locator, "body_sha256": body_hash,
                        "image_set_sha256": image_hash, "has_summary_appendix": str(has_summary).lower(),
                        "has_image_appendix": str(has_image_appendix).lower()}
    ids = [str(row[0]) for row in registry_rows]
    if len(ids) != len(set(ids)):
        raise BaselineError("v2 source registry 中 source_id 重复")
    registry_rows.sort(key=lambda row: str(row[0]).encode("utf-8"))
    baseline_rows.sort(key=lambda row: str(row[0]).encode("utf-8"))
    previous_by_sid: dict[str, dict[str, str]] = {}
    for sid, row in prior.items():
        locator = row["locator"].removeprefix("vault:").lstrip("/")
        body_hash = row.get("body_sha256", "")
        if not body_hash and previous_tree:
            blob = _git_blob(vault, previous_tree, locator)
            if blob is not None:
                old_text = _normalized_text(blob)
                body_hash = _sha256(_body_text(old_text).encode("utf-8"))
                old_image_hash, old_image_appendix = _image_inventory(
                    vault, vault / locator, old_text, treeish=previous_tree)
                row["image_set_sha256"] = old_image_hash
                row["has_summary_appendix"] = str(bool(re.search(r"%%davybase-summary-begin%%", old_text, re.I))).lower()
                row["has_image_appendix"] = str(old_image_appendix).lower()
        previous_by_sid[sid] = {"locator": locator, "body_sha256": body_hash,
                                "image_set_sha256": row.get("image_set_sha256", ""),
                                "has_summary_appendix": row.get("has_summary_appendix", ""),
                                "has_image_appendix": row.get("has_image_appendix", "")}
    diffs = []
    for sid in sorted(set(previous_by_sid) | set(current), key=lambda item: item.encode("utf-8")):
        old, new = previous_by_sid.get(sid), current.get(sid)
        presence = "added" if old is None else "deleted" if new is None else "present"
        path_changed = bool(old and new and old["locator"] != new["locator"])
        body_changed = bool(old and new and old["body_sha256"] and old["body_sha256"] != new["body_sha256"])
        enrichment_changed = bool(old and new and any(old[key] != new[key] for key in
            ("image_set_sha256", "has_summary_appendix", "has_image_appendix")))
        diffs.append([sid, presence, str(path_changed).lower(), str(body_changed).lower(),
                      str(enrichment_changed).lower(), old["locator"] if old else r"\N",
                      new["locator"] if new else r"\N"])
    _write_tsv(registry_path, V2_REGISTRY_HEADER, registry_rows)
    _write_tsv(baseline_path, V2_BASELINE_HEADER, baseline_rows)
    _write_tsv(diff_path, V2_DIFF_HEADER, diffs)
    return [{"source_id": str(row[0]), "presence_change": str(row[1]),
             "path_changed": str(row[2]), "body_changed": str(row[3]),
             "enrichment_changed": str(row[4])} for row in diffs]


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
            sid, _, locator = rec[0], rec[1], rec[2]
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
    v2 = sub.add_parser("build-v2")
    v2.add_argument("--snapshot-manifest", type=Path, required=True)
    v2.add_argument("--input-manifest", type=Path, required=True)
    v2.add_argument("--registry", type=Path, required=True)
    v2.add_argument("--baseline", type=Path, required=True)
    v2.add_argument("--diff", type=Path, required=True)
    v2.add_argument("--previous-baseline", type=Path, required=True)
    v2.add_argument("--previous-tree")
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
        if args.cmd == "build-v2":
            rows = build_v2(args.snapshot_manifest, args.input_manifest, args.registry,
                            args.baseline, args.diff, args.previous_baseline,
                            args.previous_tree)
            print(f"source baseline v2: PASS ({len(rows)} diff rows)")
            return 0
        check(root, args.baseline, args.hash_file, args.metadata)
        print("source baseline check: PASS")
        return 0
    except (BaselineError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
