# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
# -*- coding: utf-8 -*-
"""公众号素材库 ↔ Obsidian 库（唯一内容仓库）。

Obsidian vault 是知识内容的唯一存储（多机同步）；FLOW 仓库只保留流水线配置、
队列/状态/日志与链接引用，不存正文。

用法：
    # 周期维护：只重建各账号「目录.md」MOC（从 vault 自扫描，幂等）
    uv run scripts/wechat_kb/export_obsidian.py --moc-only

    # 迁移/回填模式：把一个 KB 格式文章目录（article.md+meta.json+images/）
    # 写入 vault（供 sync.py 之外的手工迁移使用）
    uv run scripts/wechat_kb/export_obsidian.py --article-dir <dir>

库内结构：<vault>/<公众号>/<合集目录>/<YYYY-MM-DD 标题>.md + attachments/ + 目录.md。
frontmatter 对齐用户 Web Clipper 习惯（author 用 [[wikilink]]、tags 含 clippings）。
同名同日期冲突时自动追加序号，绝不覆盖不同内容。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "docs" / "knowledge-base" / "08_wechat_sources"
DEFAULT_VAULT = Path.home() / "ObsidianWiki" / "Clippings" / "微信知识库"

BAD_FN = re.compile(r'[\\/:*?"<>|#^\[\]\r\n\t]')
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def obsidian_filename(title: str, published: str) -> str:
    t = BAD_FN.sub(" ", title or "无标题")
    t = re.sub(r"\s+", " ", t).strip(" .")
    t = t[:80] or "无标题"
    day = (published or "")[:10]
    return ("%s %s" % (day, t)) if day else t


def album_topic(meta: dict) -> str:
    c = meta.get("collection") or meta.get("_collection")
    if not c:
        return (meta.get("albums") or ["未分类"])[0] if meta.get("albums") else "未分类"
    return re.sub(r"^\d+[_\-]?", "", c)


def build_note(meta: dict, article_dir: Path, image_map: dict[str, str]) -> str:
    topic = album_topic(meta)
    fm = {
        "title": meta.get("title"),
        "source": meta.get("url"),
        "author": ["[[%s]]" % meta["author"]] if meta.get("author") else None,
        "account": meta.get("account"),
        "published": (meta.get("publish_time") or "")[:10] or None,
        "created": date.today().isoformat(),
        "album": topic,
        "categories": meta.get("categories"),
        "tags": ["clippings", "公众号", meta.get("account") or "未知", topic],
    }
    fm = {k: v for k, v in fm.items() if v not in (None, [], "")}
    head = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()

    src = "> [!info] 来源\n> 微信公众号「%s」" % (meta.get("account") or "未知")
    if meta.get("author"):
        src += " · 作者 %s" % meta["author"]
    if meta.get("publish_time"):
        src += " · 发布于 %s" % meta["publish_time"][:10]
    src += " · [原文链接](%s)" % meta.get("url", "")
    if meta.get("digest"):
        src += "\n> 摘要：%s" % meta["digest"]

    body = (article_dir / "article.md").read_text(encoding="utf-8")
    body = re.sub(r"\A---\n.*?\n---\n", "", body, count=1, flags=re.S)
    body = re.sub(r"\A\s*#\s*[^\n]*\n", "", body, count=1)
    body = re.sub(
        r"\A\s*(> 来源：[^\n]*\n)+\s*(> 原文链接：[^\n]*\n)?\s*(> 摘要：[^\n]*\n)?", "", body, count=1)

    def repl(m):
        rel = m.group(1)
        target = image_map.get(rel)
        return "![图片](attachments/%s)" % target if target else m.group(0)

    body = re.sub(r"!\[[^\]]*\]\((images/[^)]+)\)", repl, body)
    return "---\n%s\n---\n\n# %s\n\n%s\n\n%s" % (
        head, meta.get("title") or "无标题", src, body.strip())


def write_article(article_dir: Path, vault: Path, force: bool = False) -> Path:
    """把一个 KB 格式文章目录写入 vault（单篇；供 sync 与迁移调用），返回笔记路径。"""
    meta = json.loads((article_dir / "meta.json").read_text(encoding="utf-8"))
    account = BAD_FN.sub(" ", meta.get("account") or "未知账号").strip() or "未知账号"
    collection = meta.get("collection")
    target_dir = vault / account / collection if collection else vault / account
    base = obsidian_filename(meta.get("title"), meta.get("publish_time") or "")

    image_map: dict[str, str] = {}
    attachments = target_dir / "attachments"
    for img in meta.get("images", []):
        rel = img.get("file")
        if not rel:
            continue
        src_img = article_dir / rel
        if not src_img.exists():
            continue
        target_name = "%s-%s" % (base, Path(rel).name)
        dst = attachments / target_name
        if not dst.exists() or dst.stat().st_size != src_img.stat().st_size:
            attachments.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_img, dst)
        image_map[rel] = target_name

    content = build_note(meta, article_dir, image_map)
    note_path = target_dir / (base + ".md")
    n = 2
    while note_path.exists() and not force and note_path.read_text(encoding="utf-8") != content:
        note_path = target_dir / ("%s (%d).md" % (base, n))  # 同名不同文：加序号不覆盖
        n += 1
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(content, encoding="utf-8")
    return note_path


def parse_note(note_path: Path) -> tuple[str, str, str]:
    """读 vault 笔记 frontmatter → (published, title, source)。"""
    text = note_path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    fm = yaml.safe_load(m.group(1)) if m else {}
    return str(fm.get("published") or ""), str(fm.get("title") or note_path.stem), str(fm.get("source") or "")


def regen_mocs(vault: Path) -> list[Path]:
    """从 vault 自扫描重建各账号「目录.md」（不依赖仓库内容）。"""
    mocs: list[Path] = []
    for account_dir in sorted(p for p in vault.iterdir() if p.is_dir()):
        rows: list[tuple[str, str, str, str]] = []  # published, title, relpath, section
        for md in account_dir.rglob("*.md"):
            if md.name == "目录.md":
                continue
            published, title, _ = parse_note(md)
            rel = md.relative_to(account_dir)
            section = re.sub(r"^\d+[_\-]?", "", rel.parts[0]) if len(rel.parts) > 1 else "未分类"
            rows.append((published, title, md.stem, section))
        if not rows:
            continue
        rows.sort(key=lambda r: r[0])
        lines = ["# %s 文章目录" % account_dir.name, "",
                 "> 由 `export_obsidian.py` 自动生成；共 %d 篇。" % len(rows), ""]
        cur = None
        for published, title, stem, section in rows:
            if section != cur:
                lines += ["## %s" % section, ""]
                cur = section
            lines.append("- %s [[%s|%s]]" % ((published or "未知") + " · ", stem, title))
        lines.append("")
        moc = account_dir / "目录.md"
        moc.write_text("\n".join(lines), encoding="utf-8")
        mocs.append(moc)
    return mocs


def load_accounts(kb_dir: Path) -> dict[str, list[Path]]:
    """迁移模式：扫 KB 文章目录（含合集子目录与平铺层）。"""
    accounts: dict[str, list[Path]] = {}
    for account_dir in sorted(kb_dir.iterdir()):
        if not account_dir.is_dir() or account_dir.name in ("queue", "logs", "albums", "state"):
            continue
        for meta_path in account_dir.rglob("meta.json"):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            name = meta.get("account") or account_dir.name
            accounts.setdefault(name, []).append(meta_path.parent)
    return accounts


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号素材库 Obsidian 写入/维护")
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--moc-only", action="store_true", help="只重建各账号目录.md")
    parser.add_argument("--article-dir", type=Path, default=None,
                        help="把单个 KB 文章目录写入 vault（迁移用）")
    parser.add_argument("--kb-dir", type=Path, default=KB_DIR,
                        help="配合 --migrate 使用：从 KB 全量迁移")
    parser.add_argument("--migrate", action="store_true", help="把 kb-dir 下全部文章写入 vault")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.article_dir:
        print(write_article(args.article_dir, args.vault, args.force))
    if args.migrate:
        total = 0
        for account, dirs in load_accounts(args.kb_dir).items():
            for d in dirs:
                write_article(d, args.vault, args.force)
                total += 1
            print("%s：迁移 %d 篇" % (account, len(dirs)))
        print("迁移完成：%d 篇" % total)
    mocs = regen_mocs(args.vault)
    for m in mocs:
        print("MOC →", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
