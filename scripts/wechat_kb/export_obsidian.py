# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
# -*- coding: utf-8 -*-
"""把公众号素材库导出为 Obsidian 笔记（本地图片 + frontmatter + MOC 目录页）。

用法（仓库根目录）：
    uv run scripts/wechat_kb/export_obsidian.py \
        [--vault /Users/qiming/ObsidianWiki/Clippings/微信知识库] [--force]

- 笔记结构：<vault>/<公众号>/<合集目录>/<YYYY-MM-DD 标题>.md；
- 图片统一复制到 <合集目录>/attachments/<笔记名>-imgNNN.<ext> 并改写链接（离线可读）；
- frontmatter 对齐用户既有 Web Clipper 习惯：title/source/author([[wikilink]])/published/
  created/album/categories/tags（含 clippings）；
- 每个公众号目录生成「目录.md」MOC（wikilink 索引，按时间倒序）；
- 幂等：目标内容一致则跳过（--force 强制重写）；图片按缺失才复制。
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


def obsidian_filename(title: str, published: str) -> str:
    t = BAD_FN.sub(" ", title or "无标题")
    t = re.sub(r"\s+", " ", t).strip(" .")
    t = t[:80] or "无标题"
    day = (published or "")[:10]
    return ("%s %s" % (day, t)) if day else t


def load_accounts(kb_dir: Path) -> dict[str, list[dict]]:
    """{账号显示名: [{meta, article_dir}]}；合集子目录与平铺层都扫。"""
    accounts: dict[str, list[dict]] = {}
    for account_dir in sorted(kb_dir.iterdir()):
        if not account_dir.is_dir() or account_dir.name in ("queue", "logs", "albums", "state"):
            continue
        metas: list[dict] = []

        def scan(level: Path, collection: str | None):
            for child in sorted(level.iterdir()):
                if not child.is_dir():
                    continue
                if (child / "meta.json").exists():
                    meta = json.loads((child / "meta.json").read_text(encoding="utf-8"))
                    meta["_dir"] = child
                    meta["_collection"] = collection
                    metas.append(meta)
                elif child.name != "attachments":
                    scan(child, child.name)

        scan(account_dir, None)
        if metas:
            name = metas[0].get("account") or account_dir.name
            accounts.setdefault(name, []).extend(metas)
    return accounts


def album_topic(meta: dict) -> str:
    c = meta.get("collection")
    if not c:
        return meta.get("albums", ["未分类"])[0] if meta.get("albums") else "未分类"
    return re.sub(r"^\d+[_\-]?", "", c)


def build_note(meta: dict, image_map: dict[str, str]) -> str:
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

    body = (meta["_dir"] / "article.md").read_text(encoding="utf-8")
    # 去掉知识库版 frontmatter 与重复的一级标题/来源块（导出时重建）
    body = re.sub(r"\A---\n.*?\n---\n", "", body, count=1, flags=re.S)
    body = re.sub(r"\A\s*#\s*[^\n]*\n", "", body, count=1)
    body = re.sub(r"\A\s*(> 来源：[^\n]*\n)+\s*(> 原文链接：[^\n]*\n)?\s*(> 摘要：[^\n]*\n)?", "", body, count=1)

    def repl(m):
        rel = m.group(1)
        target = image_map.get(rel)
        return "![图片](attachments/%s)" % target if target else m.group(0)

    body = re.sub(r"!\[[^\]]*\]\((images/[^)]+)\)", repl, body)

    return "---\n%s\n---\n\n# %s\n\n%s\n\n%s" % (
        head, meta.get("title") or "无标题", src, body.strip())


def export_account(account: str, metas: list[dict], vault: Path, force: bool) -> dict:
    account_dir = vault / account
    stats = {"notes": 0, "skipped": 0, "images": 0, "moc": None}
    toc: list[tuple[str, str, str, str]] = []  # (published, title, relpath, section)

    for meta in sorted(metas, key=lambda m: m.get("publish_time") or ""):
        collection = meta.get("_collection")
        target_dir = account_dir / collection if collection else account_dir
        note_name = obsidian_filename(meta.get("title"), meta.get("publish_time") or "")
        note_path = target_dir / (note_name + ".md")

        # 图片：复制到合集 attachments/，以笔记名做前缀防冲突
        image_map: dict[str, str] = {}
        attachments = target_dir / "attachments"
        for img in meta.get("images", []):
            rel = img.get("file")
            if not rel:
                continue
            src_img = meta["_dir"] / rel
            if not src_img.exists():
                continue
            target_name = "%s-%s" % (note_name, Path(rel).name)
            dst = attachments / target_name
            if not dst.exists() or dst.stat().st_size != src_img.stat().st_size:
                attachments.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_img, dst)
                stats["images"] += 1
            image_map[rel] = target_name

        content = build_note(meta, image_map)
        if note_path.exists() and not force and note_path.read_text(encoding="utf-8") == content:
            stats["skipped"] += 1
        else:
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(content, encoding="utf-8")
            stats["notes"] += 1
        section = meta.get("_collection")
        section = re.sub(r"^\d+[_\-]?", "", section) if section else "未分类"
        toc.append(((meta.get("publish_time") or "")[:10], meta.get("title") or "",
                    str(note_path.relative_to(account_dir)), section))

    # MOC 目录页
    if toc:
        lines = ["# %s 文章目录" % account, "",
                 "> 由 `export_obsidian.py` 自动生成；共 %d 篇。" % len(toc), ""]
        cur = None
        for published, title, rel, section in reversed(toc):
            if section != cur:
                lines += ["## %s" % section, ""]
                cur = section
            lines.append("- %s [[%s|%s]]" % (
                (published or "未知") + " · ", Path(rel).stem, title))
        lines.append("")
        moc = account_dir / "目录.md"
        moc.parent.mkdir(parents=True, exist_ok=True)
        moc.write_text("\n".join(lines), encoding="utf-8")
        stats["moc"] = str(moc)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="导出公众号素材库到 Obsidian")
    parser.add_argument("--kb-dir", type=Path, default=KB_DIR)
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--force", action="store_true", help="内容未变也重写笔记")
    args = parser.parse_args()

    accounts = load_accounts(args.kb_dir)
    total_notes = 0
    for account, metas in accounts.items():
        stats = export_account(account, metas, args.vault, args.force)
        total_notes += stats["notes"] + stats["skipped"]
        print("%s：新写 %d、跳过 %d（图片复制 %d）；MOC → %s" % (
            account, stats["notes"], stats["skipped"], stats["images"], stats["moc"]))
    print("完成：共 %d 篇笔记在 %s" % (total_notes, args.vault))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
