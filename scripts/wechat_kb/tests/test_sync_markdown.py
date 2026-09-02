from __future__ import annotations

import unittest

from scripts.wechat_kb.article_markdown import compose_article_markdown


class ArticleMarkdownComposerTests(unittest.TestCase):
    def test_composer_preserves_attribution_and_has_stable_whitespace(self) -> None:
        meta = {
            "title": "经营分析样例",
            "account": "数据熊",
            "author": "FLOW 研究组",
            "publish_time": "2026-08-31 09:00",
            "digest": "用于验证来源与摘要。",
            "categories": ["经营分析"],
        }
        url = "https://mp.weixin.qq.com/s/example"
        body = "第一段。  \n\n第二段。\t\n"

        article = compose_article_markdown(meta, url, body)

        self.assertIn("# 经营分析样例", article)
        self.assertIn("> 来源：微信公众号「数据熊」 · 作者 FLOW 研究组", article)
        self.assertIn("> 发布于 2026-08-31 09:00", article)
        self.assertIn(f"> 原文链接：{url}", article)
        self.assertIn("> 摘要：用于验证来源与摘要。", article)
        self.assertIn("第一段。", article)
        self.assertIn("第二段。", article)
        self.assertTrue(article.endswith("\n"))
        self.assertFalse(article.endswith("\n\n"))
        self.assertTrue(all(line == line.rstrip(" \t") for line in article.splitlines()))


if __name__ == "__main__":
    unittest.main()
