#!/usr/bin/env python3
"""Document metadata contracts & cross-document integrity (plan Task 3, design V1.1 §6.3).

纯 Python 实现（无 jsonschema 依赖）：frontmatter 合同、七项跨文档检查、
legacy-exempt 哈希锁、唯一入口断言。仅标准库。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# 设计规范 §7：各 doc_type 的合法状态与必填附加字段
DOC_TYPES: Dict[str, dict] = {
    "design": {"statuses": {"draft", "review", "approved", "superseded", "archived"},
               "required": ["decision_refs", "knowledge_release"]},
    "specification": {"statuses": {"draft", "review", "approved", "superseded", "archived"},
                      "required": ["decision_refs", "knowledge_release"]},
    "architecture": {"statuses": {"draft", "review", "approved", "superseded", "archived"},
                     "required": ["decision_refs", "applies_to"]},
    "product": {"statuses": {"draft", "review", "canonical", "superseded", "archived"},
                "required": ["decision_refs"]},
    "state": {"statuses": {"draft", "current", "superseded", "archived"},
              "required": ["applies_to"]},
    "navigation": {"statuses": {"draft", "current", "superseded", "archived"}, "required": []},
    "governance": {"statuses": {"draft", "current", "superseded", "archived"}, "required": []},
    "plan": {"statuses": {"proposed", "active", "blocked", "completed", "cancelled", "archived"},
             "required": ["depends_on", "acceptance_refs"]},
    "work-item": {"statuses": {"proposed", "active", "blocked", "completed", "cancelled", "archived"},
                  "required": ["depends_on", "acceptance_refs"]},
    "decision": {"statuses": {"proposed", "accepted", "amended", "superseded", "retired", "rejected"},
                 "required": ["decided_at", "authority"]},
    "knowledge-card": {"statuses": {"candidate", "verified", "canonical", "deprecated"},
                       "required": ["knowledge_release", "source_refs", "authority_level", "sensitivity"]},
    "domain-handbook": {"statuses": {"candidate", "verified", "canonical", "deprecated"},
                        "required": ["knowledge_release", "source_refs", "authority_level", "sensitivity"]},
    "taxonomy": {"statuses": {"candidate", "verified", "canonical", "deprecated"},
                 "required": ["knowledge_release", "source_refs"]},
    "product-mapping": {"statuses": {"candidate", "verified", "canonical", "deprecated"},
                        "required": ["knowledge_release", "source_refs"]},
    "source-evidence": {"statuses": {"registered", "verified", "withdrawn"},
                        "required": ["snapshot_id", "sensitivity"]},
    "review": {"statuses": {"open", "partially-resolved", "resolved", "accepted-risk", "obsolete"},
               "required": ["subject_ref", "findings"]},
    "delivery": {"statuses": {"draft", "verified", "superseded", "archived"},
                 "required": ["commit_refs", "evidence_refs"]},
    "verification": {"statuses": {"draft", "verified", "superseded", "archived"},
                     "required": ["commit_refs", "evidence_refs"]},
    "operations": {"statuses": {"draft", "active", "superseded", "archived"},
                   "required": ["applies_to", "owner"]},
    "generated": {"statuses": {"generated", "superseded", "archived"},
                  "required": ["generator_ref", "input_hash"]},
}

CORE_FIELDS = ["doc_id", "title", "doc_type", "status", "version",
               "created_at", "updated_at", "owner"]

PRE_STATIC_PREFIX = "pre-static-"
RELEASES_DIR = "docs/knowledge-base/00_governance/releases"


@dataclass
class Doc:
    path: str
    meta: Dict[str, str]
    sha256: str


@dataclass
class CheckResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checked: int = 0
    exempt: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_frontmatter(text: str) -> Optional[Dict[str, str]]:
    """解析平铺 YAML frontmatter（key: value 标量 / [行内列表] / 多行 - item 列表）。"""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    meta: Dict[str, str] = {}
    current_key: Optional[str] = None
    for line in text[4:end].splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("- "):
            if current_key:
                item = line.strip()[2:].strip()
                prev = meta.get(current_key, "").strip("[]")
                items = [x for x in prev.split(",") if x]
                items.append(item)
                meta[current_key] = "[" + ", ".join(items) + "]"
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            meta[k] = v
            current_key = k if v == "" else None
    return meta


FALLBACK_SKIP_PARTS = {".git", ".zcode", ".venv", "node_modules", "site-packages",
                       "dist-info", ".pytest_cache", "__pycache__",
                       "01_conversations", "02_research", "08_wechat_sources",
                       "03_assets", "05_design", "99_manifest", "00_governance"}


def _doc_contract_exempt_prefixes() -> tuple:
    from documentation.inventory import DOC_CONTRACT_EXEMPT_PREFIXES
    return DOC_CONTRACT_EXEMPT_PREFIXES


def iter_markdown(root: Path):
    """文档合同仅适用于 git 跟踪的可变 markdown（与 M0 清单同口径）。

    不可变档案/基线设施/微信档案区不适用；非 git 环境（测试 fixture）
    回退为 rglob + 目录排除。
    """
    try:
        from documentation.inventory import git_tracked_files
        tracked = git_tracked_files(root)
        exempt_prefixes = _doc_contract_exempt_prefixes()
    except Exception:
        tracked = None
    if tracked is not None:
        for rel in sorted(t for t in tracked if t.endswith(".md")
                          and not any(t.startswith(p) for p in exempt_prefixes)):
            yield root / rel, rel
        return
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if any(part in FALLBACK_SKIP_PARTS for part in rel.parts[:-1]):
            continue
        yield p, str(rel)


def load_legacy_exemptions(root: Path) -> Dict[str, str]:
    f = root / "docs/10_governance/legacy-exemptions.tsv"
    if not f.exists():
        return {}
    out = {}
    lines = f.read_text(encoding="utf-8").splitlines()[1:]
    for line in lines:
        if not line.strip():
            continue
        path, sha, *_ = line.split("\t")
        out[path] = sha
    return out


def _ref_list(value: str) -> List[str]:
    value = (value or "").strip()
    if value in ("", "null", "[]", "~"):
        return []
    return re.findall(r"[A-Za-z0-9_.\-/]+", value)


def check_repository(root: Path) -> CheckResult:
    result = CheckResult()
    exemptions = load_legacy_exemptions(root)
    docs: List[Doc] = []

    for p, rel in iter_markdown(root):
        meta = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if meta is None:
            if rel in exemptions:
                if exemptions[rel] != sha:
                    result.errors.append(f"legacy-exempt modified, must comply: {rel}")
                else:
                    result.exempt += 1
            else:
                result.errors.append(f"missing frontmatter, not exempt: {rel}")
            continue
        docs.append(Doc(rel, meta, sha))

    result.checked = len(docs)
    by_id: Dict[str, Doc] = {}
    for d in docs:
        # 检查 1：doc_id 唯一
        if d.meta.get("doc_id") in by_id:
            result.errors.append(f"duplicate doc_id {d.meta.get('doc_id')}: "
                                 f"{by_id[d.meta['doc_id']].path} vs {d.path}")
        elif d.meta.get("doc_id"):
            by_id[d.meta["doc_id"]] = d

    # 当前 release（M2 前可能不存在）
    current_release = None
    cr = root / RELEASES_DIR / "CURRENT_RELEASE"
    if cr.exists():
        current_release = cr.read_text(encoding="utf-8").strip()

    for d in docs:
        m = d.meta
        dt = m.get("doc_type", "")
        spec = DOC_TYPES.get(dt)
        # 必填字段
        for f in CORE_FIELDS:
            if not m.get(f):
                result.errors.append(f"missing field {f}: {d.path}")
        if spec is None:
            result.errors.append(f"unknown doc_type {dt!r}: {d.path}")
            continue
        # 检查 6a：状态合法
        status = m.get("status", "")
        if status not in spec["statuses"]:
            result.errors.append(f"invalid status {status!r} for {dt}: {d.path}")
        for f in spec["required"]:
            if not m.get(f):
                result.errors.append(f"missing required field {f} for {dt}: {d.path}")
        # 检查 2：引用存在
        for ref_field in ("supersedes", "superseded_by", "decision_refs", "source_refs",
                          "depends_on", "acceptance_refs", "related_code"):
            for ref in _ref_list(m.get(ref_field, "")):
                if ref_field in ("supersedes", "superseded_by", "decision_refs"):
                    if ref.startswith("D") and ref[1:].isdigit():
                        continue  # 决策编号由 M1 决策索引承载
                if ref in by_id or (root / ref).exists():
                    continue
                if ref_field in ("depends_on", "acceptance_refs", "source_refs", "related_code"):
                    continue  # 计划/知识引用域 M2/M4 起有专用登记，M1 不强制存在
                result.errors.append(f"unresolved reference {ref_field}={ref}: {d.path}")
        # 检查 4：knowledge_release 可解析
        kr = m.get("knowledge_release", "")
        if kr and spec["required"] and "knowledge_release" in spec["required"]:
            if kr.startswith(PRE_STATIC_PREFIX):
                pass
            elif current_release and kr == current_release and \
                    (root / RELEASES_DIR / kr).is_dir():
                pass
            else:
                result.errors.append(f"knowledge_release not resolvable {kr!r}: {d.path}")
        # 检查 3a：depends_on 上游规格必须 approved（引用可解析到仓内文档时）
        for ref in _ref_list(m.get("depends_on", "")):
            dd = by_id.get(ref)
            if dd is not None and dd.meta.get("doc_type") in ("specification", "design", "architecture") \
                    and dd.meta.get("status") != "approved":
                result.errors.append(
                    f"upstream {ref} not approved ({dd.meta.get('status')}): {d.path}")
        # 检查 3：上游 decision accepted（M1 后决策文件存在时启用）
        for ref in _ref_list(m.get("decision_refs", "")):
            dd = by_id.get(ref)
            if dd is not None and dd.meta.get("status") not in (None, "accepted", "amended"):
                result.errors.append(f"decision {ref} not accepted: {d.path}")
        # 检查 7：canonical 知识有来源
        if dt in ("knowledge-card", "domain-handbook", "taxonomy", "product-mapping") \
                and status == "canonical" and not m.get("source_refs", "").strip("[]"):
            result.errors.append(f"canonical knowledge without source_refs: {d.path}")

    # 唯一入口断言：恰一个 PROJECT_STATE current（Task 4 建立前允许为零，仅提示）
    states = [d for d in docs if d.meta.get("doc_type") == "state"]
    current = [d for d in states if d.meta.get("status") == "current"]
    if len(current) > 1:
        result.errors.append(
            f"expected exactly one current state doc, found {len(current)}: "
            + ", ".join(d.path for d in current))
    elif len(current) == 0:
        result.warnings.append("no current state doc yet (established in M1 Task 4)")

    return result


def check_release_lock(root: Path, release_id: str) -> List[str]:
    """检查 5：release-lock 内 path 与 SHA-256 一致（M2 发布后生效）。"""
    errors = []
    lock = root / RELEASES_DIR / release_id / "release-lock.yaml"
    if not lock.exists():
        return [f"release lock missing: {lock}"]
    text = lock.read_text(encoding="utf-8")
    for match in re.finditer(r"path:\s*(\S+).*?sha256:\s*([0-9a-f]{64})", text, re.S):
        rel, want = match.group(1), match.group(2)
        p = root / rel
        if not p.exists():
            errors.append(f"release-lock path missing: {rel}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != want:
            errors.append(f"release-lock hash mismatch: {rel}")
    return errors
