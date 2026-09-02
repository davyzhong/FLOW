# -*- coding: utf-8 -*-
"""扫描 08_wechat_sources 下全部文章 meta.json，生成账号级与全局 INDEX.md。

目录布局（organize_albums.py 重组后）：
    08_wechat_sources/<来源id>/[<NN_合集目录>/]<日期_标题>/meta.json
索引按 来源 → 合集 分节；每个合集目录内同时生成自身 INDEX.md，可独立浏览。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[2] / "docs" / "knowledge-base" / "08_wechat_sources"


def load_article(meta_path: Path) -> dict | None:
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["dir"] = str(meta_path.parent.relative_to(KB_DIR)) if meta_path.parent.is_relative_to(KB_DIR) \
        else str(meta_path.parent)
    return meta


def load_account(account_dir: Path) -> dict[str, list[dict]]:
    """返回 {板块名: [meta,...]}：板块 = 合集目录（含其自身 INDEX）或平铺层。"""
    sections: dict[str, list[dict]] = {}
    for child in sorted(account_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "meta.json").exists():
            meta = load_article(child / "meta.json")
            if meta:
                sections.setdefault("未分类", []).append(meta)
            continue
        metas = []
        for article_dir in sorted(child.iterdir()):
            meta_path = article_dir / "meta.json"
            if article_dir.is_dir() and meta_path.exists():
                meta = load_article(meta_path)
                if meta:
                    metas.append(meta)
        metas.sort(key=lambda m: m.get("publish_time") or "")
        if metas:
            sections[child.name] = metas
    return sections


def table_rows(metas: list[dict]) -> list[str]:
    lines = ["| 日期 | 文章（本地） | 合集归属 | 相关性 | 原文 |", "|---|---|---|---|---|"]
    for meta in reversed(metas):  # 新→旧
        date = (meta.get("publish_time") or "未知日期")[:10]
        title = (meta.get("title") or "无标题").replace("|", "\\|")
        albums = "、".join(meta.get("albums") or meta.get("categories") or [])
        rel = meta.get("relevance") or ""
        link = meta.get("url") or ""
        lines.append("| %s | [%s](%s/) | %s | %s | [原文](%s) |" % (
            date, title, meta["dir"], albums, rel, link))
    return lines


def render_section(name: str, metas: list[dict], with_title: bool = True) -> list[str]:
    lines = []
    if with_title:
        lines += ["## %s（%d 篇）" % (name, len(metas)), ""]
    lines += table_rows(metas)
    lines.append("")
    return lines


def build(kb_dir: Path = KB_DIR) -> str:
    lines = [
        "# 公众号素材库总索引",
        "",
        "> 本文件由 `scripts/wechat_kb/build_index.py` 自动生成，请勿手工编辑。",
        "",
    ]
    total = 0
    account_blocks: list[tuple[str, dict[str, list[dict]]]] = []
    if not kb_dir.exists():
        pass
    else:
        for child in sorted(kb_dir.iterdir()):
            if not child.is_dir() or child.name in ("queue", "logs", "albums", "state"):
                continue
            sections = load_account(child)
            if sections:
                account_blocks.append((child.name, sections))
                total += sum(len(v) for v in sections.values())

    lines.append("共 %d 个来源、%d 篇已归档文章。" % (len(account_blocks), total))
    lines.append("")
    for name, sections in account_blocks:
        account = next((m[0].get("account") for m in sections.values() if m), name)
        lines.append("## %s（%s）" % (account, name))
        lines.append("")
        # 合集目录按名称排序（01_ 前缀），平铺未分类排最后
        ordered = sorted(sections.items(), key=lambda kv: (kv[0] == "未分类", kv[0]))
        for sec_name, metas in ordered:
            lines += render_section(sec_name, metas)
            # 合集目录内生成独立 INDEX.md
            if sec_name != "未分类":
                sub = ["# %s（%d 篇）" % (sec_name, len(metas)), "",
                       "> 由 `scripts/wechat_kb/build_index.py` 自动生成。", ""]
                sub += table_rows(metas)
                (kb_dir / name / sec_name / "INDEX.md").write_text(
                    "\n".join(sub) + "\n", encoding="utf-8")
    out = kb_dir / "INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    kb = Path(sys.argv[1]) if len(sys.argv) > 1 else KB_DIR
    print("written:", build(kb))
