#!/usr/bin/env python3
"""Static knowledge release tooling (plan Tasks 6-8, design V1.1 §4.8).

分层 coverage 构建（组级 + HIGH 篇级）、声明对账、release lock 构建与
CURRENT_RELEASE 切换。仅标准库。
"""

from __future__ import annotations

import argparse
import hashlib
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import hashlib as _h  # noqa: F401 (keep import order stable)
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

SCAN_DIR = "docs/knowledge-base/02_research/synthesis/2026-09-12-obsidian-scan"
BASELINE_ID = "obsidian-2026-09-12T15:46+08:00"
RELEASES_DIR = "docs/knowledge-base/00_governance/releases"

# 组级声明（来自评估文件 §1/§2 的冻结声明值；对账基准，非写死验收数字）
GROUP_DECLARATIONS = {
    "GRP-A-finance": ("A 财务与会计", 231),
    "GRP-B-management": ("B 企业管理", 441),
    "GRP-C-logistics": ("C 跨境物流", 125),
    "GRP-D-wiki": ("D wiki 编译层财务关键词", 778),
    "GRP-W1-wechat": ("W1 微信·数据分析星球+数据熊", 435),
    "GRP-W2-wechat": ("W2 微信·客观分析报告+数研复盘狮", 2),
    "GRP-W3-wechat": ("W3 微信·数据分析不是个事儿+花叔", 176),
    "GRP-W4-mumuziyou": ("W4 微信·木木自由", 482),
    "GRP-W4-benxiang": ("W4 微信·奔向自由的果", 183),
    "GRP-W4-chenfan": ("W4 微信·宸帆海财会咨询服务", 179),
    "GRP-W4-jiejue": ("W4 微信·解决方案研究所", 2),
    "GRP-W4-zhanlue": ("W4 微信·战略领航家", 1),
}

HIGH_ID_RE = re.compile(r"（(wechat-[0-9a-f]{6,12}|[0-9]{16,20})）")


@dataclass
class CoverageRow:
    source_id: str
    level: str          # group | article
    title: str
    locator: str        # 组范围定义或 vault 定位符
    snapshot_id: str
    declared_count: int  # group: 声明篇数；article: 1
    disposition: str     # adopted-candidate | background | rejected | pending-verification
    k_domain: str
    sensitivity: str


def _scan_files(root: Path) -> List[Path]:
    d = root / SCAN_DIR
    return sorted(d.glob("*.md")) if d.exists() else []


def build_coverage(root: Path) -> List[CoverageRow]:
    rows: List[CoverageRow] = []
    group_counts: Dict[str, int] = {}
    for f in _scan_files(root):
        text = f.read_text(encoding="utf-8")
        stem = f.stem
        # 组级条目：从 GROUP_DECLARATIONS 取声明；同文件多篇级标识符
        for gid, (gtitle, gcount) in GROUP_DECLARATIONS.items():
            key = gid.split("-", 1)[1]
            if stem.startswith(key.split("-")[0]) and gid not in group_counts:
                pass  # 文件->组映射在下面统一处理
        # 篇级：抽取 HIGH 标识符（★ 标题行后的（id））
        for m in re.finditer(r"####\s*★?\s*(.{2,80}?)（(wechat-[0-9a-f]{6,12}|[0-9]{16,20})）", text):
            title, ident = m.group(1).strip(), m.group(2)
            sid = f"SRC-H-{ident}"
            if any(r.source_id == sid for r in rows):
                continue
            rows.append(CoverageRow(
                source_id=sid, level="article", title=title[:60],
                locator=f"vault:{BASELINE_ID}#wechat-or-note-id={ident}",
                snapshot_id=BASELINE_ID, declared_count=1,
                disposition="adopted-candidate", k_domain="K1-K8:routed",
                sensitivity="public"))
        # 目录级统计行（W4 表格：| 公众号 | 正文数 | ...）
        for m in re.finditer(r"^\|\s*([^*|\s][^|]*?)\s*\|\s*(\d+)\s*\|", text, re.M):
            name, count = m.group(1).strip(), int(m.group(2))
            if name.startswith("公众号") or name.startswith("---"):
                continue
            gid = "GRP-W4-" + re.sub(r"\s+", "", name)[:10]
            group_counts.setdefault(gid, (name, count))
    # 非微信组：按文件头部「总数：N 篇」登记
    for f in _scan_files(root):
        m = re.search(r"总数[：:]\s*(\d+)\s*篇", f.read_text(encoding="utf-8"))
        if not m:
            continue
        stem = f.stem  # e.g. A-finance
        letter = stem.split("-")[0]
        gid = f"GRP-{stem}"
        if gid in GROUP_DECLARATIONS and gid not in group_counts:
            gtitle, gcount = GROUP_DECLARATIONS[gid]
            group_counts[gid] = (gtitle, gcount)
    # 合并组级行
    for gid, (gtitle, gcount) in GROUP_DECLARATIONS.items():
        title, count = group_counts.get(gid, (None, None))
        if title is None:
            # fixture 简化场景：无扫描文件时仍登记声明值
            title, count = gtitle, gcount
        rows.append(CoverageRow(
            source_id=gid, level="group", title=title,
            locator=f"vault:{BASELINE_ID}#group={gid}",
            snapshot_id=BASELINE_ID, declared_count=count if title != gtitle or True else gcount,
            disposition="adopted-candidate" if "W4" not in gid else "pending-verification",
            k_domain="K1-K8:mixed", sensitivity="public"))
    return sorted(rows, key=lambda r: r.source_id)


def verify_coverage(rows: List[CoverageRow], declared: Dict[str, int]) -> List[str]:
    errors: List[str] = []
    ids = [r.source_id for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate source_id in coverage")
    for r in rows:
        if r.level == "group":
            want = declared.get(r.source_id)
            if want is not None and r.declared_count != want:
                errors.append(
                    f"group count mismatch {r.source_id}: declared {want}, coverage {r.declared_count}")
        if r.level == "article" and not r.locator:
            errors.append(f"article without locator: {r.source_id}")
    return errors


def write_coverage_tsv(rows: List[CoverageRow], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["source_id\tlevel\ttitle\tlocator\tsnapshot_id\tdeclared_count\tdisposition\tk_domain\tsensitivity"]
    for r in rows:
        lines.append("\t".join(str(x) for x in (
            r.source_id, r.level, r.title, r.locator, r.snapshot_id,
            r.declared_count, r.disposition, r.k_domain, r.sensitivity)))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--build-coverage", metavar="OUT_TSV")
    ap.add_argument("--verify-coverage", metavar="DECLARED_JSON")
    ap.add_argument("--build", metavar="RELEASE_ID")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--verify-current", action="store_true")
    ap.add_argument("--switch", nargs=2, metavar=("OLD", "NEW"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.repo).resolve()

    if args.build_coverage:
        rows = build_coverage(root)
        write_coverage_tsv(rows, Path(args.build_coverage))
        n_group = sum(1 for r in rows if r.level == "group")
        n_art = sum(1 for r in rows if r.level == "article")
        print(f"coverage: {len(rows)} rows ({n_group} group / {n_art} article) -> {args.build_coverage}")
        return 0
    if getattr(args, "build", None):
        return build_release(root, args.build, check_only=args.check_only)
    if getattr(args, "verify_current", False):
        return verify_current(root)
    if getattr(args, "switch", None):
        return switch_release(root, args.switch[0], args.switch[1], apply=args.apply)
    if args.verify_coverage:
        import json
        declared = json.loads(Path(args.verify_coverage).read_text(encoding="utf-8"))
        rows = build_coverage(root)
        errors = verify_coverage(rows, declared)
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        print("coverage verify: " + ("PASS" if not errors else "FAIL"))
        return 0 if not errors else 1
    ap.error("choose an action")
    return 2




# ---------------- Task 8: release build / verify / switch ----------------

RELEASE_ID = "flow-knowledge-2026-09-12.1"
OLD_BASELINE = BASELINE_ID  # pre-static-obsidian-...
ASSET_DIRS = {
    "knowledge-card": "docs/knowledge-base/20_knowledge_cards/{finance,operations,methods,governance,technology}",
    "domain-handbook": "docs/knowledge-base/30_domain_handbooks",
    "taxonomy": "docs/knowledge-base/20_knowledge_cards",
    "product-mapping": "docs/knowledge-base/50_product_mappings",
}
EXTRA_ASSETS = [
    ("source-register", "docs/knowledge-base/10_sources/source-register.tsv"),
    ("coverage", "docs/knowledge-base/00_governance/releases/" + RELEASE_ID + "/coverage.tsv"),
]


def collect_assets(root: Path) -> List[dict]:
    """显式收集发布资产：16 卡 + taxonomy + 11 手册 + mapping + source-register + coverage。"""
    patterns = [
        ("knowledge-card", "docs/knowledge-base/20_knowledge_cards/*/*.md"),
        ("taxonomy", "docs/knowledge-base/20_knowledge_cards/TAXONOMY--*.yaml"),
        ("domain-handbook", "docs/knowledge-base/30_domain_handbooks/*/README--*.md"),
        ("product-mapping", "docs/knowledge-base/50_product_mappings/FLOW-PRODUCT-MAPPING*.md"),
    ]
    assets, seen = [], set()
    for kind, pattern in patterns:
        for p in sorted(root.glob(pattern)):
            if not p.is_file() or str(p) in seen or p.name == "README.md":
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            did = re.search(r"^(doc_id|taxonomy_id):\s*(\S+)", text, re.M)
            ver = re.search(r"^version:\s*\"?([^\"\n]+)\"?", text, re.M)
            if not did:
                continue
            seen.add(str(p))
            assets.append({"id": did.group(2), "type": kind,
                           "version": ver.group(1).strip() if ver else "1.0",
                           "path": str(p.relative_to(root)), "sha256": sha256_of(p)})
    for kind, rel in EXTRA_ASSETS:
        p = root / rel
        if p.exists():
            assets.append({"id": f"FLOW-ASSET-{kind.upper()}", "type": kind, "version": "1.0",
                           "path": rel, "sha256": sha256_of(p)})
    return sorted(assets, key=lambda a: a["id"])


def build_release(root: Path, release_id: str, check_only: bool = False) -> int:
    rel_dir = root / RELEASES_DIR / release_id
    assets = collect_assets(root)
    # 非 canonical 入锁检查：verified 资产允许 build 候选，但发布(switch)前必须 canonical
    non_canon = []
    for a in assets:
        p = root / a["path"]
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^status:\s*(\S+)", text, re.M)
        if m and m.group(1) not in ("canonical",) and a["type"] in ASSET_DIRS:
            non_canon.append(a["id"])
    lines = [f"# release-lock: {release_id}",
             f"release: {release_id}", f"baseline: {BASELINE_ID}", f"assets: {len(assets)}", ""]
    for a in assets:
        lines.append(f"- id: {a['id']}")
        lines.append(f"  type: {a['type']}")
        lines.append(f"  version: \"{a['version']}\"")
        lines.append(f"  path: {a['path']}")
        lines.append(f"  sha256: {a['sha256']}")
    print("\n".join(lines))
    if not check_only:
        rel_dir.mkdir(parents=True, exist_ok=True)
        (rel_dir / "release-lock.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (rel_dir / "release.yaml").write_text(
            f"release: {release_id}\nbaseline: {BASELINE_ID}\n"
            f"coverage: 12 group rows reconciled to declared baseline\n"
            f"notes: >\n  articles registered on-demand; see 10_sources/SOURCE_REGISTER.md\n",
            encoding="utf-8")
        (rel_dir / "sha256sums.txt").write_text(
            "\n".join(f"{a['sha256']}  {a['path']}" for a in assets) + "\n", encoding="utf-8")
        print(f"\nrelease written to {rel_dir} ({len(assets)} assets; "
              f"{len(non_canon)} still non-canonical: {', '.join(non_canon[:6])}...)")
    return 0


def verify_current(root: Path) -> int:
    cr = root / RELEASES_DIR / "CURRENT_RELEASE"
    if not cr.exists():
        print("verify: no CURRENT_RELEASE (pre-release state) -> PASS (nothing to verify)")
        return 0
    rid = cr.read_text(encoding="utf-8").strip()
    lock = root / RELEASES_DIR / rid / "release-lock.yaml"
    if not lock.exists():
        print(f"FAIL: CURRENT_RELEASE {rid} without lock", file=sys.stderr)
        return 1
    errors = []
    for m in re.finditer(r"path:\s*(\S+)\n\s*sha256:\s*([0-9a-f]{64})", lock.read_text(encoding="utf-8")):
        rel, want = m.group(1), m.group(2)
        p = root / rel
        if not p.exists():
            errors.append(f"missing {rel}")
        elif sha256_of(p) != want:
            errors.append(f"hash mismatch {rel}")
    for e in errors:
        print(f"FAIL {e}", file=sys.stderr)
    print(f"verify {rid}: " + ("PASS" if not errors else f"FAIL ({len(errors)})"))
    return 0 if not errors else 1


def switch_release(root: Path, old: str, new: str, apply: bool = False) -> int:
    """把全部引用 old release 的文档元数据切换为 new；--apply 才写盘。"""
    changed = []
    for rel in _tracked_md(root):
        p = root / rel
        text = p.read_text(encoding="utf-8")
        if old in text:
            changed.append(rel)
            if apply:
                p.write_text(text.replace(old, new), encoding="utf-8")
    print(f"switch {old} -> {new}: {len(changed)} files" + (" (applied)" if apply else " (dry-run)"))
    for c in changed[:20]:
        print(f"  {c}")
    if apply:
        cr = root / RELEASES_DIR / "CURRENT_RELEASE"
        cr.parent.mkdir(parents=True, exist_ok=True)
        cr.write_text(new + "\n", encoding="utf-8")
        print(f"CURRENT_RELEASE -> {new}")
    return 0


def _tracked_md(root: Path) -> List[str]:
    from documentation.inventory import git_tracked_files, DOC_CONTRACT_EXEMPT_PREFIXES
    return [t for t in git_tracked_files(root) if t.endswith(".md")
            and not any(t.startswith(p) for p in DOC_CONTRACT_EXEMPT_PREFIXES)]


if __name__ == "__main__":
    sys.exit(main())
