# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.31",
#   "beautifulsoup4>=4.12",
#   "lxml>=5.0",
#   "pyyaml>=6.0",
#   "defusedxml>=0.7",
#   "pillow>=10.0",
# ]
# ///
# -*- coding: utf-8 -*-
"""公众号素材库同步入口。

用法（仓库根目录）：
    uv run scripts/wechat_kb/sync.py [--dry-run] [--limit N] [--skip-manifest] [--recompress]

流程：发现新文章 URL（seed/合集/mp_platform/rss）→ 逐篇抓取正文与图片 →
财经相关性筛选 → 经 work/ staging 写入 Obsidian vault（内容唯一仓库）→
重建 vault 目录页与仓库内引用索引。低相关性文章只记 logs/excluded.jsonl。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_index
import classify
import export_obsidian
import make_manifest
import organize_albums
import providers
from article_markdown import compose_article_markdown
from wechatlib import (
    CST,
    FetchError,
    MarkdownBuilder,
    download_images,
    download_named_image,
    fetch_article_html,
    parse_article_meta,
    recompress_pngs,
    render_images,
    slugify_title,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "docs" / "knowledge-base" / "08_wechat_sources"
WORK_DIR = REPO_ROOT / "work" / "wechat_kb"
CRED_PATH = WORK_DIR / "mp_credentials.json"
# 内容仓库 = Obsidian vault（多机同步）；仓库内不存正文，staging 只是摄取中转
STAGING_ROOT = WORK_DIR / "staging"
DEFAULT_CONTENT_ROOT = Path.home() / "ObsidianWiki" / "Clippings" / "微信知识库"


def load_state(kb_dir: Path) -> dict:
    path = kb_dir / "state" / "seen_urls.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_state(kb_dir: Path, state: dict) -> None:
    path = kb_dir / "state" / "seen_urls.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_sources(kb_dir: Path) -> list[dict]:
    """合并手工 sources.yaml 与自动登记的 sources.auto.yaml。"""
    sources: list[dict] = []
    for name in ("sources.yaml", "sources.auto.yaml"):
        path = kb_dir / name
        if path.exists():
            sources += yaml.safe_load(path.read_text(encoding="utf-8"))["sources"]
    return sources


def load_content_root(kb_dir: Path) -> Path:
    """知识内容唯一存储（sources.yaml 顶层 content_root，默认本机 Obsidian vault）。"""
    path = kb_dir / "sources.yaml"
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("content_root"):
            return Path(data["content_root"])
    return DEFAULT_CONTENT_ROOT


def register_source(kb_dir: Path, meta: dict) -> str:
    """按文章实际公众号自动登记来源（sources.auto.yaml），返回来源 id。"""
    nickname = (meta.get("account") or "").strip()
    if not nickname:
        return "inbox"
    existing = load_sources(kb_dir)
    for s in existing:
        if s.get("name") == nickname or (
            meta.get("account_id") and s.get("account_id") == meta.get("account_id")
        ):
            return s["id"]
    slug = re.sub(r'[\\/:*?"<>|\s·（）()]+', "", nickname) or "unknown"
    for s in existing:
        if s["id"] == slug:
            slug = slug + "_" + (meta.get("account_id") or "x").replace("gh_", "")
    auto_path = kb_dir / "sources.auto.yaml"
    data = {"sources": []}
    if auto_path.exists():
        data = yaml.safe_load(auto_path.read_text(encoding="utf-8")) or data
    data.setdefault("sources", []).append({
        "id": slug,
        "name": nickname,
        "account_id": meta.get("account_id"),
        "biz": meta.get("biz"),
        "note": "自动登记于 %s" % datetime.now(CST).strftime("%Y-%m-%d"),
    })
    auto_path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print("  [新来源] %s（%s）已自动登记" % (nickname, slug))
    return slug


def unique_dir(base: Path) -> Path:
    if not base.exists():
        return base
    n = 2
    while base.with_name(base.name + "_%d" % n).exists():
        n += 1
    return base.with_name(base.name + "_%d" % n)


def ingest_from_html(html_text: str, url: str, article_root: Path | None,
                     recompress: bool = False, collection: str | None = None) -> dict:
    """解析 HTML → 分类 →（非 excluded 且给定目录时）落盘。返回 meta。"""
    meta = parse_article_meta(html_text)
    meta["url"] = url
    meta["crawled_at"] = datetime.now(CST).isoformat(timespec="seconds")

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_text, "lxml")
    js_content = soup.find(id="js_content")
    builder = MarkdownBuilder()
    body_md = builder.container(js_content) if js_content else ""
    if not body_md.strip():
        raise FetchError("正文为空（js_content 未解析到内容）")
    # 标题/表格等行内上下文的图片占位符是原始 URL 形式，统一登记并转为序号形式
    body_md = re.sub(r"\x00IMG:(https?://[^\x00]+)\x00",
                     lambda m: "\x00IMG:#%d\x00" % builder.register(m.group(1)),
                     body_md)

    cls = classify.classify(meta.get("title") or "", classify.content_to_text(body_md))
    meta.update({
        "collection": collection,
        "categories": cls["categories"],
        "relevance": cls["relevance"],
        "relevance_score": cls["score"],
        "title_hits": cls["title_hits"],
    })
    if cls["relevance"] == "excluded" or article_root is None:
        meta["excluded"] = True
        return meta

    article_root.mkdir(parents=True, exist_ok=True)
    images_dir = article_root / "images"

    # 封面（若与正文重复也无妨，独立命名不占正文图片序号）
    cover_file = None
    if meta.get("cover_url"):
        try:
            cover_file = download_named_image(meta["cover_url"], images_dir, "cover")
        except Exception:
            cover_file = None

    saved_images = download_images(builder.image_urls, images_dir)
    if recompress:
        recompress_pngs(images_dir, saved_images)
    body_md = render_images(body_md, builder, saved_images)

    meta["cover_file"] = cover_file
    meta["images"] = [s for s in saved_images if s.get("file")]
    meta["image_failures"] = [s for s in saved_images if not s.get("file")]
    meta["word_count"] = len(classify.content_to_text(body_md))

    article_md = compose_article_markdown(meta, url, body_md)
    (article_root / "article.md").write_text(article_md, encoding="utf-8")
    meta_clean = {k: v for k, v in meta.items() if k != "excluded"}
    (article_root / "meta.json").write_text(
        json.dumps(meta_clean, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号素材库同步")
    parser.add_argument("--kb-dir", type=Path, default=KB_DIR)
    parser.add_argument("--dry-run", action="store_true", help="只发现与解析，不写入知识库")
    parser.add_argument("--limit", type=int, default=0, help="每次最多处理文章数（0=不限）")
    parser.add_argument("--skip-manifest", action="store_true", help="跳过 99_manifest 重建")
    parser.add_argument("--exclude-borderline", action="store_true", help="相关性不足的文章不入库")
    parser.add_argument("--since", default=None, metavar="YYYY-MM-DD",
                        help="只入库该日期（含）之后发布的文章，更早的标记跳过")
    parser.add_argument("--discover-only", action="store_true",
                        help="只发现并记录新文章 URL，不抓取（用于全量回填前评估规模）")
    parser.add_argument("--recompress", action="store_true",
                        help="大 PNG 图片转 JPEG（幻灯片截图类体积降 70%+，推荐批量入库时开启）")
    args = parser.parse_args()

    kb_dir: Path = args.kb_dir
    sources = load_sources(kb_dir)
    content_root = load_content_root(kb_dir)
    state = load_state(kb_dir)
    queue_dir = kb_dir / "queue"
    report = {"started_at": datetime.now(CST).isoformat(timespec="seconds"),
              "content_root": str(content_root), "sources": {}}
    included_total = 0

    for source in sources:
        sid = source["id"]
        inbox = bool(source.get("inbox"))
        label = source.get("name") or sid
        # 合集归位映射：url → (类别目录, topic, [全部归属])
        album_map: dict[str, tuple[str, str, list[str]]] = {}
        if source.get("albums"):
            album_map, _ = organize_albums.load_album_map(kb_dir, source)
        print("== 来源 %s（%s）%s ==" % (label, sid, "[收件箱]" if inbox else ""))
        urls = providers.discover(queue_dir, source, CRED_PATH, consume=not args.dry_run)
        new_urls = [u for u in urls if u not in state]
        print("  发现 %d 个链接，其中新文章 %d 篇" % (len(urls), len(new_urls)))
        stat = {"discovered": len(urls), "new": len(new_urls),
                "included": 0, "excluded": 0, "errors": 0}

        if args.discover_only:
            for url in new_urls:
                append_jsonl(kb_dir / "logs" / "discovered.jsonl", {
                    "source_hint": sid, "url": url,
                    "discovered_at": datetime.now(CST).isoformat(timespec="seconds")})
            stat["note"] = "discover-only：未抓取，URL 已记录到 logs/discovered.jsonl"
            report["sources"][sid] = stat
            continue

        for url in new_urls:
            if args.limit and (stat["included"] + stat["excluded"]) >= args.limit:
                print("  达到 --limit=%d，本批剩余文章留待下次" % args.limit)
                break
            target = None
            try:
                html_text = fetch_article_html(url, cache_dir=WORK_DIR / "html_cache")
                meta0 = parse_article_meta(html_text)

                # 收件箱：按文章实际公众号自动归类登记
                article_sid = sid
                if inbox and not args.dry_run:
                    article_sid = register_source(kb_dir, meta0)

                date_part = (meta0.get("publish_time")
                             or datetime.now(CST).strftime("%Y-%m-%d %H:%M"))[:10].replace("-", "")

                # --since：更早的文章跳过（在下载图片前判定）
                if args.since and (meta0.get("publish_time") or "")[:10] < args.since:
                    stat["excluded"] += 1
                    state[url] = {"status": "skipped_old", "title": meta0.get("title"),
                                  "date": datetime.now(CST).isoformat(timespec="seconds")}
                    print("  [跳过] %s（早于 %s）" % (meta0.get("title"), args.since))
                    continue

                # 合集归位：已知合集的文章进入类别子目录（staging 中转，最终写 vault）
                collection_dir: str | None = None
                if album_map:
                    hit = album_map.get(url)
                    if hit:
                        collection_dir = hit[0]
                parent = STAGING_ROOT / article_sid / collection_dir if collection_dir else STAGING_ROOT / article_sid
                target = unique_dir(parent / ("%s_%s" % (date_part, slugify_title(meta0.get("title") or "untitled"))))

                meta = ingest_from_html(html_text, url,
                                        None if args.dry_run else target,
                                        recompress=args.recompress,
                                        collection=collection_dir)

                if meta.get("excluded") or (args.exclude_borderline and meta.get("relevance") == "borderline"):
                    stat["excluded"] += 1
                    append_jsonl(kb_dir / "logs" / "excluded.jsonl", {
                        "url": url, "title": meta.get("title"), "relevance": meta.get("relevance"),
                        "score": meta.get("relevance_score"),
                        "crawled_at": datetime.now(CST).isoformat(timespec="seconds")})
                    state[url] = {"status": "excluded", "title": meta.get("title"),
                                  "date": datetime.now(CST).isoformat(timespec="seconds")}
                    print("  [跳过] %s（相关性低）" % (meta.get("title") or url))
                else:
                    stat["included"] += 1
                    included_total += 1
                    note_rel = None
                    if not args.dry_run:
                        note_path = export_obsidian.write_article(target, content_root)
                        note_rel = str(note_path.relative_to(content_root))
                        shutil.rmtree(target, ignore_errors=True)
                    state[url] = {"status": "done", "note": note_rel,
                                  "title": meta.get("title"),
                                  "date": datetime.now(CST).isoformat(timespec="seconds")}
                    print("  [入库] %s（%s，得分 %s）→ %s" % (
                        meta.get("title"), meta.get("relevance"),
                        meta.get("relevance_score"), note_rel or "dry-run"))
                time.sleep(2.5)
            except Exception as exc:
                stat["errors"] += 1
                append_jsonl(kb_dir / "logs" / "errors.jsonl", {
                    "url": url, "error": str(exc)[:300],
                    "crawled_at": datetime.now(CST).isoformat(timespec="seconds")})
                print("  [失败] %s：%s" % (url, str(exc)[:120]))
                if target is not None and target.exists() and not (target / "article.md").exists():
                    shutil.rmtree(target, ignore_errors=True)
                time.sleep(1.0)

        report["sources"][sid] = stat

    report["finished_at"] = datetime.now(CST).isoformat(timespec="seconds")
    report["included_total"] = included_total

    if not args.dry_run:
        save_state(kb_dir, state)
        for moc in export_obsidian.regen_mocs(content_root):
            print("vault 目录页：%s" % moc)
        print("引用索引已更新：%s" % build_index.build(kb_dir, content_root))
        if not args.skip_manifest:
            n = make_manifest.build()
            print("manifest 已重建：inventory=%d 条" % n[0])
        append_jsonl(kb_dir / "logs" / "sync_report.jsonl", report)
    else:
        print("（dry-run：未写状态/索引/manifest）")

    print("完成：本批入库 %d 篇。" % included_total)
    if not CRED_PATH.exists():
        print("提示：如需回填公众号全部历史文章，请配置 %s（cookie+token），格式见 README。" % CRED_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
