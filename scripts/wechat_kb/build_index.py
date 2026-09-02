# -*- coding: utf-8 -*-
"""扫描 08_wechat_sources 下全部文章 meta.json，生成账号级与全局 INDEX.md。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KB_DIR = Path(__file__).resolve().parents[2] / "docs" / "knowledge-base" / "08_wechat_sources"


def load_articles(kb_dir: Path) -> dict[str, list[dict]]:
    """返回 {账号目录名: [meta,...]}，meta 附 dir 字段。"""
    accounts: dict[str, list[dict]] = {}
    if not kb_dir.exists():
        return accounts
    for child in sorted(kb_dir.iterdir()):
        if not child.is_dir() or child.name in ("queue", "logs"):
            continue
        metas = []
        for article_dir in sorted(child.iterdir()):
            meta_path = article_dir / "meta.json"
            if article_dir.is_dir() and meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta["dir"] = child.name + "/" + article_dir.name
                metas.append(meta)
        metas.sort(key=lambda m: m.get("publish_time") or "")
        if metas:
            accounts[child.name] = metas
    return accounts


def fmt_row(meta: dict) -> str:
    date = (meta.get("publish_time") or "未知日期")[:10]
    title = (meta.get("title") or "无标题").replace("|", "\\|")
    cats = "、".join(meta.get("categories") or [])
    rel = meta.get("relevance") or ""
    link = meta.get("url") or ""
    return "| %s | [%s](%s/) | %s | %s | [原文](%s) |" % (date, title, meta["dir"], cats, rel, link)


def build(kb_dir: Path = KB_DIR) -> str:
    accounts = load_articles(kb_dir)
    total = sum(len(v) for v in accounts.values())

    lines = [
        "# 公众号素材库总索引",
        "",
        "> 本文件由 `scripts/wechat_kb/build_index.py` 自动生成，请勿手工编辑。",
        "",
        "共 %d 个来源、%d 篇已归档文章。" % (len(accounts), total),
        "",
    ]
    for name, metas in accounts.items():
        account = metas[0].get("account") or name
        lines.append("## %s（%s）" % (account, name))
        lines.append("")
        lines.append("| 日期 | 文章（本地） | 分类 | 相关性 | 原文 |")
        lines.append("|---|---|---|---|---|")
        for meta in reversed(metas):  # 新→旧
            lines.append(fmt_row(meta))
        lines.append("")
    out = kb_dir / "INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    kb = Path(sys.argv[1]) if len(sys.argv) > 1 else KB_DIR
    print("written:", build(kb))
