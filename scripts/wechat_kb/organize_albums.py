# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6.0"]
# ///
# -*- coding: utf-8 -*-
"""把账号目录下的平铺文章按合集重组为类别子目录。

用法（仓库根目录）：
    uv run scripts/wechat_kb/organize_albums.py [--source shujuxiong]

- 合集清单来自 docs/knowledge-base/08_wechat_sources/albums/<topic>.json；
- 类别目录与优先级来自 sources.yaml 的 albums[].dir（顺序即主归属优先级）；
- 一篇文章属于多个合集时，物理归入优先级最前的合集目录，meta.json 记录全部归属；
- state/seen_urls.json 的 dir 字段同步更新；
- 幂等：已在类别子目录中的文章跳过。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "docs" / "knowledge-base" / "08_wechat_sources"


def load_album_map(kb_dir: Path, source: dict) -> tuple[dict[str, tuple[str, str, list[str]]], list[str]]:
    """返回 {url: (collection_dir, topic, [全部topic])} 与类别目录名列表。"""
    entries = source.get("albums") or []
    dir_by_topic: dict[str, str] = {}
    order: list[str] = []
    for e in entries:
        topic = e["topic"]
        dir_by_topic[topic] = e.get("dir") or topic
        order.append(topic)
    url_map: dict[str, tuple[str, str, list[str]]] = {}
    for topic in order:
        path = kb_dir / "albums" / (topic + ".json")
        if not path.exists():
            continue
        for it in json.loads(path.read_text(encoding="utf-8"))["items"]:
            url = it["url"].split("#")[0]
            if url in url_map:
                url_map[url][2].append(topic)  # 追加归属，主归属不变
            else:
                url_map[url] = (dir_by_topic[topic], topic, [topic])
    return url_map, [dir_by_topic[t] for t in order]


def main() -> int:
    parser = argparse.ArgumentParser(description="按合集重组文章目录")
    parser.add_argument("--source", default="shujuxiong")
    parser.add_argument("--kb-dir", type=Path, default=KB_DIR)
    args = parser.parse_args()

    sources = []
    for name in ("sources.yaml", "sources.auto.yaml"):
        p = args.kb_dir / name
        if p.exists():
            sources += yaml.safe_load(p.read_text(encoding="utf-8"))["sources"]
    source = next((s for s in sources if s["id"] == args.source), None)
    if source is None:
        raise SystemExit(f"sources 中不存在 {args.source}")

    url_map, collection_dirs = load_album_map(args.kb_dir, source)
    if not collection_dirs:
        raise SystemExit("该来源未配置 albums，无需重组")

    account_dir = args.kb_dir / args.source
    state_path = args.kb_dir / "state" / "seen_urls.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    moved = kept_flat = 0
    for article_dir in sorted(account_dir.iterdir()):
        if not article_dir.is_dir() or article_dir.name in collection_dirs:
            continue
        meta_path = article_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        url = (meta.get("url") or "").split("#")[0]
        hit = url_map.get(url)
        if not hit:
            kept_flat += 1  # 不属于任何已知合集（如手动种子），保留在平铺层
            continue
        collection_dir, topic, all_topics = hit
        target_parent = account_dir / collection_dir
        target_parent.mkdir(parents=True, exist_ok=True)
        target = target_parent / article_dir.name
        if target.exists():
            raise SystemExit(f"目标已存在：{target}")
        article_dir.rename(target)
        meta["collection"] = collection_dir
        meta["albums"] = all_topics
        (target / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
        old_rel = f"{args.source}/{article_dir.name}"
        new_rel = f"{args.source}/{collection_dir}/{article_dir.name}"
        for entry in state.values():
            if entry.get("dir") == old_rel:
                entry["dir"] = new_rel
        moved += 1

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                          encoding="utf-8")
    print(f"重组完成：移动 {moved} 篇，保留平铺 {kept_flat} 篇；类别目录：{collection_dirs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
