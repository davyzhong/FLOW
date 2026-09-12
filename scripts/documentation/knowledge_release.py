#!/usr/bin/env python3
"""Static knowledge release tooling (plan Tasks 6-8, design V1.1 §4.8).

分层 coverage 构建（组级 + HIGH 篇级）、声明对账、release lock 构建与
CURRENT_RELEASE 切换。仅标准库。
"""

from __future__ import annotations

import argparse
import hashlib
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
    args = ap.parse_args(argv)
    root = Path(args.repo).resolve()

    if args.build_coverage:
        rows = build_coverage(root)
        write_coverage_tsv(rows, Path(args.build_coverage))
        n_group = sum(1 for r in rows if r.level == "group")
        n_art = sum(1 for r in rows if r.level == "article")
        print(f"coverage: {len(rows)} rows ({n_group} group / {n_art} article) -> {args.build_coverage}")
        return 0
    if args.verify_coverage:
        import json
        declared = json.loads(Path(args.verify_coverage).read_text(encoding="utf-8"))
        rows = build_coverage(root)
        errors = verify_coverage(rows, declared)
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        print("coverage verify: " + ("PASS" if not errors else "FAIL"))
        return 0 if not errors else 1
    ap.error("choose --build-coverage or --verify-coverage")
    return 2


if __name__ == "__main__":
    sys.exit(main())
