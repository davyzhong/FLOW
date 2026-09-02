# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
# -*- coding: utf-8 -*-
"""生成仓库侧引用索引 INDEX.md：知识内容在 Obsidian vault，仓库只保留链接。

用法：
    uv run scripts/wechat_kb/build_index.py [--content-root <vault 路径>]

每行：日期 | 标题 | vault 笔记（file:// 链接）| obsidian:// 链接 | 原文。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_obsidian

KB_DIR = Path(__file__).resolve().parents[2] / "docs" / "knowledge-base" / "08_wechat_sources"
DEFAULT_CONTENT_ROOT = Path.home() / "ObsidianWiki" / "Clippings" / "微信知识库"


def build(kb_dir: Path = KB_DIR, content_root: Path | None = None) -> str:
    vault = content_root or DEFAULT_CONTENT_ROOT
    lines = [
        "# 公众号素材库引用索引",
        "",
        "> 本文件由 `scripts/wechat_kb/build_index.py` 自动生成，请勿手工编辑。",
        "> 知识内容唯一存储于 Obsidian vault（多机同步），本仓库只保留链接引用。",
        "> vault 根：`%s`" % vault,
        "",
    ]
    accounts = 0
    total = 0
    if not vault.exists():
        lines.append("**vault 不可达：%s**（本机未挂载？内容请从 Obsidian 同步获取）" % vault)
    else:
        for account_dir in sorted(p for p in vault.iterdir() if p.is_dir()):
            rows = []
            for md in account_dir.rglob("*.md"):
                if md.name == "目录.md":
                    continue
                published, title, source = export_obsidian.parse_note(md)
                rel = md.relative_to(vault)
                rows.append((published, title, rel, source))
            if not rows:
                continue
            accounts += 1
            total += len(rows)
            lines.append("## %s（%d 篇）" % (account_dir.name, len(rows)))
            lines.append("")
            lines.append("| 日期 | 文章 | vault 笔记 | 原文 |")
            lines.append("|---|---|---|---|")
            for published, title, rel, source in sorted(rows, reverse=True):
                lines.append("| %s | %s | [%s](file://%s) · [obsidian](obsidian://open?path=%s) | %s |" % (
                    published or "未知",
                    title.replace("|", "\\|"),
                    rel.name,
                    (vault / rel).as_posix(),
                    str(vault / rel),
                    ("<%s>" % source) if source else "-",
                ))
            lines.append("")
    lines.insert(5, "共 %d 个来源、%d 篇笔记（位于 vault）。" % (accounts, total))
    out = kb_dir / "INDEX.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb-dir", type=Path, default=KB_DIR)
    parser.add_argument("--content-root", type=Path, default=DEFAULT_CONTENT_ROOT)
    args = parser.parse_args()
    print("written:", build(args.kb_dir, args.content_root))
