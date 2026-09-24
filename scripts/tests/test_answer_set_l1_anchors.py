#!/usr/bin/env python3
"""P1 红灯测试：亏损行正数披露的符号翻转定位 + 图像页目视核验登记。

钉死两条规则：
1. locate() 在常规（含括号负数归一）定位失败后，允许「行名同页 + 绝对值同页」
   的强锚符号翻转（披露把亏损印成正数），match_mode 显式标记，绝不产生弱锚翻转；
2. 图像页（无文本层）行可通过 config/statements/l1_visual_verified.yaml 登记
   目视核验证据进入答案集，match_mode=visual-verified，证据缺字段必须失败。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import build_answer_set_l1 as builder  # noqa: E402


def _haystack(text: str) -> str:
    return builder._page_haystack(text)


class SignFlipLocateTest(unittest.TestCase):
    def test_loss_row_positive_presentation_locates_with_explicit_mode(self) -> None:
        pages = [
            _haystack("某些无关页面 9,083"),
            _haystack(
                "淨利潤 80,234 140,350\n"
                "歸屬於非控制性權益的淨損失 7,652 9,083\n"
                "歸屬於阿里巴巴集團股東的淨利潤 87,886 149,433"
            ),
        ]
        located = builder.locate(pages, "歸屬於非控制性權益損益", [-7652, -9083])
        self.assertIsNotNone(located)
        page, mode = located
        self.assertEqual(page, 2)
        self.assertEqual(mode, "strong-sign-flip-loss-row")

    def test_sign_flip_requires_row_name_on_same_page(self) -> None:
        # 仅数值同页（无行名）不得符号翻转——弱锚不允许翻转
        pages = [_haystack("某摘要页 7,652 9,083 无行名")]
        self.assertIsNone(builder.locate(pages, "歸屬於非控制性權益損益", [-7652, -9083]))

    def test_positive_values_never_sign_flip(self) -> None:
        pages = [_haystack("歸屬於非控制性權益的淨損失 7,652 9,083")]
        # 正值行正常 strong 命中，不得标记为翻转
        located = builder.locate(pages, "歸屬於非控制性權益損益", [7652, 9083])
        self.assertIsNotNone(located)
        self.assertEqual(located[1], "strong")


class VisualVerifiedOverrideTest(unittest.TestCase):
    def test_override_schema_validation(self) -> None:
        overrides = builder.load_visual_overrides(REPO)
        self.assertIsInstance(overrides, dict)
        for key, ov in overrides.items():
            for field in (
                "statement",
                "item",
                "page_seq",
                "printed_page",
                "evidence_image",
                "evidence_sha256",
                "verified_by",
                "verified_at",
                "basis",
            ):
                self.assertIn(field, ov, f"{key} 缺字段 {field}")


if __name__ == "__main__":
    unittest.main()
