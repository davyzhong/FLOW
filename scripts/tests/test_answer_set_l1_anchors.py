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

import build_answer_set_l1 as builder


def _haystack(text: str) -> str:
    return builder._page_haystack(text)


class SignFlipLocateTest(unittest.TestCase):
    def test_scoped_row_name_anchors_to_the_disclosed_base_label(self) -> None:
        pages = [_haystack("流动资产 證券投資 9,927 4,234")]
        located = builder.locate(pages, "流动资产：證券投資", [9927, 4234])
        self.assertEqual(located, (1, "strong"))

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
        self.assertIsNone(
            builder.locate(pages, "歸屬於非控制性權益損益", [-7652, -9083])
        )

    def test_positive_values_never_sign_flip(self) -> None:
        pages = [_haystack("歸屬於非控制性權益的淨損失 7,652 9,083")]
        # 正值行正常 strong 命中，不得标记为翻转
        located = builder.locate(pages, "歸屬於非控制性權益損益", [7652, 9083])
        self.assertIsNotNone(located)
        self.assertEqual(located[1], "strong")

    def test_source_page_hint_prevents_summary_page_capture(self) -> None:
        pages = [
            _haystack("摘要 年度綜合收益總額 6,133,484 7,504,495"),
            _haystack("其他报表内容"),
            _haystack("年度綜合收益總額 6,133,484 7,504,495"),
        ]

        located = builder.locate(
            pages, "年度綜合收益總額", [6133484, 7504495], page_hint=3
        )

        self.assertEqual(located, (3, "strong"))

    def test_source_page_hint_fails_closed_instead_of_falling_back(self) -> None:
        pages = [
            _haystack("摘要 年度綜合收益總額 6,133,484 7,504,495"),
            _haystack("实际报表页缺少目标数字"),
        ]

        located = builder.locate(
            pages, "年度綜合收益總額", [6133484, 7504495], page_hint=2
        )

        self.assertIsNone(located)


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


class VersionedExtractionSourceTest(unittest.TestCase):
    def test_historical_jdl_yaml_is_not_an_active_accuracy_input(self) -> None:
        sources = builder.source_paths()
        self.assertNotIn(
            REPO / "docs/implementation/p5/jdl_2025fy_statements.yaml", sources
        )
        self.assertIn(
            REPO
            / "validation/financial_reports/corrections/jdl_2025fy_statements_v3.yaml",
            sources,
        )

    def test_historical_alibaba_fy2023_yaml_is_replaced_by_versioned_correction(self) -> None:
        sources = builder.source_paths()
        self.assertNotIn(
            REPO / "docs/implementation/p5/alibaba_2023fy_statements.yaml", sources
        )
        self.assertIn(
            REPO
            / "validation/financial_reports/corrections/alibaba_2023fy_statements_v2.yaml",
            sources,
        )

    def test_alibaba_fy2023_correction_preserves_source_and_period_identity(self) -> None:
        import yaml

        path = (
            REPO
            / "validation/financial_reports/corrections/alibaba_2023fy_statements_v2.yaml"
        )
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["correction_version"], 2)
        self.assertEqual(
            payload["supersedes"],
            "docs/implementation/p5/alibaba_2023fy_statements.yaml",
        )
        self.assertEqual(
            payload["source_sha256"],
            "28256e2d4fcebbd94fd2d1c46d51c75af2f93fbe492b31b764a44da0813fa9a7",
        )
        row = next(
            row
            for row in payload["statements"]["合并利润表"]
            if row["item"] == "商譽減值"
        )
        self.assertEqual(row["上期发生额"], -25141)
        self.assertEqual(row["page"], 38)

    def test_alibaba_fy2023_comparatives_match_fy2022_current_values(self) -> None:
        import yaml

        current_path = (
            REPO
            / "validation/financial_reports/corrections/alibaba_2023fy_statements_v2.yaml"
        )
        prior_path = REPO / "docs/implementation/p5/alibaba_2022fy_statements.yaml"
        current = yaml.safe_load(current_path.read_text(encoding="utf-8"))["statements"]
        prior = yaml.safe_load(prior_path.read_text(encoding="utf-8"))["statements"]
        prior_values = {
            (statement, row["item"]): row.get("本期发生额")
            for statement, rows in prior.items()
            for row in rows
        }
        comparisons = [
            (statement, row["item"], row["上期发生额"], prior_values[(statement, row["item"])])
            for statement, rows in current.items()
            for row in rows
            if row.get("上期发生额") is not None
            and prior_values.get((statement, row["item"])) is not None
        ]

        self.assertEqual(len(comparisons), 24)
        self.assertTrue(
            all(current_value == prior_value for _, _, current_value, prior_value in comparisons)
        )

    def test_jdl_correction_has_source_identity_and_supersedes_link(self) -> None:
        import yaml

        path = (
            REPO
            / "validation/financial_reports/corrections/jdl_2025fy_statements_v3.yaml"
        )
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["correction_version"], 3)
        self.assertEqual(
            payload["supersedes"],
            "validation/financial_reports/corrections/jdl_2025fy_statements_v2.yaml",
        )
        self.assertEqual(len(payload["source_sha256"]), 64)
        income = payload["statements"]["合并利润表"]
        comprehensive = payload["statements"]["合并综合收益表"]
        self.assertEqual(
            {
                row["page"]
                for row in income
                if row["item"] in {"年度利潤", "本公司所有者", "非控制性權益"}
            },
            {106},
        )
        self.assertEqual({row["page"] for row in comprehensive}, {107})

    def test_l1_v3_keeps_duplicate_jdl_rows_on_their_source_pages(self) -> None:
        import yaml

        answer_set = yaml.safe_load(
            (REPO / "config/statements/answer_set_l1_v3.yaml").read_text(
                encoding="utf-8"
            )
        )
        jdl_entries = [
            row
            for row in answer_set["entries"]
            if row["source_pdf"].endswith("JDL_FY2025_annual_report.pdf")
            and row["item"] in {"年度利潤", "本公司所有者", "非控制性權益"}
            and row["statement"] in {"合并利润表", "合并综合收益表"}
        ]
        expected_pages = {
            ("合并利润表", "年度利潤"): 106,
            ("合并利润表", "本公司所有者"): 106,
            ("合并利润表", "非控制性權益"): 106,
            ("合并综合收益表", "年度利潤"): 107,
            ("合并综合收益表", "本公司所有者"): 107,
            ("合并综合收益表", "非控制性權益"): 107,
        }
        self.assertEqual(len(jdl_entries), 12)
        self.assertTrue(
            all(
                row["page"] == expected_pages[(row["statement"], row["item"])]
                for row in jdl_entries
            )
        )

    def test_l1_v4_contains_corrected_alibaba_comparative_value(self) -> None:
        import yaml

        answer_set = yaml.safe_load(
            (REPO / "config/statements/answer_set_l1_v4.yaml").read_text(
                encoding="utf-8"
            )
        )
        entry = [
            row
            for row in answer_set["entries"]
            if row["source_pdf"].endswith("BABA_FY2023_annual_results.pdf")
            and row["item"] == "商譽減值"
            and row["column"] == "上期发生额"
        ]
        self.assertEqual(answer_set["version"], 4)
        self.assertEqual(
            answer_set["supersedes"], "config/statements/answer_set_l1_v3.yaml"
        )
        self.assertEqual(len(entry), 1)
        self.assertEqual((entry[0]["value"], entry[0]["page"], entry[0]["match_mode"]), (-25141, 38, "strong"))
        self.assertEqual(answer_set["coverage"]["values_total"], 1776)

    def test_l0_expected_uses_corrected_alibaba_comparative_value(self) -> None:
        from scripts.accuracy_benchmark import collect_expected

        expected = collect_expected()
        key = (
            "docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/BABA_FY2023_annual_results.pdf",
            "合并利润表",
            "商譽減值",
            "value_prior",
        )
        self.assertEqual(expected[key], -25141)

    def test_source_mapping_suffix_matches_each_extraction_source(self) -> None:
        import yaml

        mapping = yaml.safe_load(
            (REPO / "config/statements/answer_set_sources.yaml").read_text(
                encoding="utf-8"
            )
        )
        # 2026-09-29 ZTO 接入后源 PDF 不再全部位于 p5_samples（ZTO 冻结于
        # validation/financial_reports/original/）；一致性改为「suffix 是
        # source_pdf 的路径后缀」，存在性按解析后的真实路径核验。
        for row in mapping["reports"]:
            extraction = yaml.safe_load(
                (
                    REPO / f"docs/implementation/p5/{row['sample']}_statements.yaml"
                ).read_text(encoding="utf-8")
            )
            source_pdf = extraction["source_pdf"]
            self.assertTrue(
                source_pdf.endswith(row["source_pdf_suffix"]), row["sample"]
            )
            self.assertTrue((REPO / source_pdf).is_file(), row["sample"])


if __name__ == "__main__":
    unittest.main()
