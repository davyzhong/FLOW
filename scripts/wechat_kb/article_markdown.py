from __future__ import annotations

import json

FRONTMATTER_KEYS = (
    "title",
    "account",
    "account_id",
    "author",
    "publish_time",
    "url",
    "crawled_at",
    "collection",
    "categories",
    "relevance",
    "relevance_score",
    "word_count",
)


def _without_line_ending_whitespace(value: str) -> str:
    return "\n".join(line.rstrip(" \t") for line in value.splitlines()).rstrip("\n")


def compose_article_markdown(meta: dict[str, object], url: str, body_md: str) -> str:
    frontmatter = ["---"]
    for key in FRONTMATTER_KEYS:
        frontmatter.append(f"{key}: {json.dumps(meta.get(key), ensure_ascii=False)}")
    frontmatter.append("---")

    source = f"> 来源：微信公众号「{meta.get('account') or '未知'}」"
    if meta.get("author"):
        source += f" · 作者 {meta['author']}"
    attribution = [source]
    if meta.get("publish_time"):
        attribution.append(f"> 发布于 {meta['publish_time']}")
    attribution.append(f"> 原文链接：{url}")
    if meta.get("digest"):
        attribution.append(f"> 摘要：{meta['digest']}")

    sections = (
        "\n".join(frontmatter),
        f"# {meta.get('title') or '无标题'}",
        "\n".join(attribution),
        _without_line_ending_whitespace(body_md),
    )
    article = "\n\n".join(section for section in sections if section)
    return _without_line_ending_whitespace(article) + "\n"
