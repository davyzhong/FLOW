"""抽取适配器（B02）测试。

- 三个真实样本：与已提交抽取 YAML 全量比对（零退化），勾稽检查全部通过；
- 自动适配器选择：每个样本命中预期适配器；
- 用例覆盖：跨页续表（顺丰多页报表）、附注号识别、括号负数、空值语义、双单位并存；
- 未知版式：显式 UnsupportedLayoutError 降级；
- 留出公司（圆通）在 A 股适配器下可直接抽取（验证版式泛化）。
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from flow_api.statements.extraction import (
    UnsupportedLayoutError,
    _hk_parse_line,
    extract_statements,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES = REPO_ROOT / "docs/knowledge-base/02_research/original/p5_samples"
EXPECTED = REPO_ROOT / "docs/implementation/p5"

CASES = {
    "sf": {
        "pdf": SAMPLES / "sf_002352/SF_2026_Q1_report.pdf",
        "yaml": EXPECTED / "sf_2026q1_statements.yaml",
        "adapter": "cn_ashare_table",
    },
    "jdl": {
        "pdf": SAMPLES / "jd_logistics_2618/JDL_FY2025_annual_report.pdf",
        "yaml": EXPECTED / "jdl_2025fy_statements.yaml",
        "adapter": "hk_traditional_text",
    },
    "tencent": {
        "pdf": SAMPLES / "tencent_0700/Tencent_2026_Q2_results.pdf",
        "yaml": EXPECTED / "tencent_2026q2_statements.yaml",
        "adapter": "hk_results_announcement",
    },
}


def _norm_items(items: list[dict]) -> list[tuple]:
    rows = []
    for item in items:
        values = tuple(
            sorted(
                (key, None if value is None else Decimal(str(value)))
                for key, value in item.items()
                if key not in ("item", "page")
            )
        )
        rows.append((item["item"], values))
    return rows


@pytest.mark.parametrize("case", ["sf", "jdl", "tencent"])
def test_extraction_matches_committed_yaml(case: str) -> None:
    spec = CASES[case]
    content = spec["pdf"].read_bytes()
    result = extract_statements(content)
    assert result.adapter_id == spec["adapter"], "自动适配器选择错误"
    assert result.source_sha256 is not None and len(result.source_sha256) == 64

    expected = yaml.safe_load(spec["yaml"].read_text())["statements"]
    assert set(result.statements) == set(expected)
    for statement_type, expected_items in expected.items():
        assert _norm_items(result.statements[statement_type]) == _norm_items(expected_items), (
            f"{case} {statement_type} 与已提交 YAML 不一致（退化）"
        )

    failed = [c for c in result.checks if c.status != "一致"]
    assert not failed, f"{case} 勾稽失败：{[(c.label, c.left, c.right) for c in failed]}"


def test_explicit_adapter_selection() -> None:
    content = CASES["sf"]["pdf"].read_bytes()
    result = extract_statements(content, adapter_id="cn_ashare_table")
    assert result.adapter_id == "cn_ashare_table"


def test_yto_holdout_company_extracts_with_ashare_adapter() -> None:
    content = (SAMPLES / "yto_600233/YTO_2026_Q1_report.pdf").read_bytes()
    result = extract_statements(content)
    assert result.adapter_id == "cn_ashare_table"
    income = {item["item"]: item for item in result.statements["合并利润表"]}
    revenue = income["其中：营业收入"]
    assert revenue["本期发生额"] == 18768681556.28
    assert revenue["page"] is not None
    balance = {item["item"]: item for item in result.statements["合并资产负债表"]}
    assert balance["资产总计"]["期末余额"] == 54500821991.88
    failed = [c for c in result.checks if c.status == "不一致"]
    assert not failed, f"圆通勾稽不一致：{[(c.label) for c in failed]}"


def test_hk_parse_line_note_number_and_paren_negative() -> None:
    # 附注号识别：剥完金额后最前的 1-3 位无逗号数字是附注号而非金额
    parsed = _hk_parse_line("物業及設備 12 1,234,567 1,111,111")
    assert parsed == ("物業及設備", 1234567, 1111111)


def test_hk_parse_line_paren_negative_and_dash() -> None:
    parsed = _hk_parse_line("財務成本 (12,345) (10,000)")
    assert parsed == ("財務成本", -12345, -10000)
    parsed_dash = _hk_parse_line("出售產業園的收益 — —")
    assert parsed_dash is None


def test_unknown_layout_explicitly_degrades() -> None:
    minimal = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 52 >>\nstream\n"
        b"BT /F1 12 Tf 72 720 Td (unrelated document text) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n%%EOF"
    )
    with pytest.raises(UnsupportedLayoutError):
        extract_statements(minimal)


def test_tencent_result_carries_scope_warning() -> None:
    result = extract_statements(CASES["tencent"]["pdf"].read_bytes())
    assert result.adapter_id == "hk_results_announcement"
    assert any("简表" in warning for warning in result.warnings)
    assert set(result.statements) == {"合并利润表"}


def test_tencent_paren_negative_without_leading_space_keeps_sign() -> None:
    # 括号紧跟 CJK（PDF 常见排印）也必须解析为负数，不得丢负号
    import re

    from flow_api.statements.extraction import _TENCENT_PARENUM, _parse_signed

    line = "应占联营公司及合营公司盈利/(亏损)净额 (9,993) 4,473 3,620"
    found = re.findall(_TENCENT_PARENUM, line)
    assert len(found) == 3
    assert _parse_signed(found[0]) == -9993
    assert _parse_signed(found[1]) == 4473
