"""Task 6 (M2.1) tests: source coverage builder (design V1.1 §4.8, §10.1).

分层 coverage：组级条目与基线声明对账（不写死篇数数字）；篇级条目来自
评估明细中已识别的 HIGH 代表篇标识符。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.documentation.knowledge_release import (
    CoverageRow,
    build_coverage,
    verify_coverage,
)


def make_kb(tmp: Path) -> Path:
    scan = tmp / "docs/knowledge-base/02_research/synthesis/2026-09-12-obsidian-scan"
    scan.mkdir(parents=True)
    (scan / "A-finance.md").write_text(
        "# A 财务与会计分类扫描评估\n\n扫描日期：2026-09-11｜总数：3 篇\n\n"
        "## HIGH 相关（共 2 篇）\n\n"
        "#### ★ 财务总监驾驶舱（1918937918732913424）\n- 主题：x\n\n"
        "#### ★ 集团驾驶舱（wechat-3e6b42d04fe7）\n- 主题：y\n",
        encoding="utf-8",
    )
    (scan / "W4-wechat-1546-snapshot.md").write_text(
        "# 增量\n\n| 公众号 | 正文数 | 直接候选 |\n|---|---:|---:|\n| 木木自由 | 5 | 2 |\n"
        "| **合计** | 5 | 2 |\n",
        encoding="utf-8",
    )
    return tmp


class CoverageBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_kb(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_builds_group_and_article_rows(self) -> None:
        rows = build_coverage(self.root)
        groups = [r for r in rows if r.level == "group"]
        articles = [r for r in rows if r.level == "article"]
        self.assertGreaterEqual(len(groups), 2)  # A 组 + W4 公众号组
        ids = {r.source_id for r in rows}
        self.assertTrue(all(ids))  # 无空 ID
        # 篇级：HIGH 标识符被抽取
        joined = " ".join(r.source_id + r.title for r in articles)
        self.assertIn("1918937918732913424", joined)
        self.assertIn("wechat-3e6b42d04fe7", joined)

    def test_coverage_rows_are_unique_and_sorted(self) -> None:
        rows = build_coverage(self.root)
        ids = [r.source_id for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))

    def test_verify_passes_against_declared_baseline(self) -> None:
        rows = build_coverage(self.root)
        declared = {r.source_id: r.declared_count for r in rows if r.level == "group"}
        errors = verify_coverage(rows, declared)
        self.assertEqual(errors, [])

    def test_verify_fails_on_count_mismatch(self) -> None:
        rows = build_coverage(self.root)
        declared = {r.source_id: (r.declared_count + 1 if r.level == "group" else r.declared_count)
                    for r in rows}
        errors = verify_coverage(rows, declared)
        self.assertTrue(any("mismatch" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
