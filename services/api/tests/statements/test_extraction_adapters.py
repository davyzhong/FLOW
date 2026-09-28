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

# Historical JDL YAML is retained unchanged as an audit input. These rows came
# from the equity-changes continuation page, which was mistakenly included in
# the balance-sheet page range; the regression below pins their exclusion.
JDL_EQUITY_PAGE_FALSE_BALANCE_ROWS = {
    "截至2025年1月1日",
    "年度利潤",
    "年度其他綜合（虧損）╱收益",
    "年度綜合（虧損）╱收益總額",
    "行使購股權及歸屬限制性股份單位",
    "收購子公司的部分權益25、29",
    "收購受共同控制子公司",
    "股份支付（稅務影響盈餘）",
    "向子公司非控制性權益支付的股息",
    "出售一家受共同控制子公司",
    "截至2025年12月31日",
}

CASES = {
    "sf": {
        "pdf": SAMPLES / "sf_002352/SF_2026_Q1_report.pdf",
        "yaml": EXPECTED / "sf_2026q1_statements.yaml",
        "adapter": "cn_ashare_table",
    },
    "jdl": {
        "pdf": SAMPLES / "jd_logistics_2618/JDL_FY2025_annual_report.pdf",
        "yaml": REPO_ROOT
        / "validation/financial_reports/corrections/jdl_2025fy_statements_v3.yaml",
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

    expected_payload = yaml.safe_load(spec["yaml"].read_text())
    expected = expected_payload["statements"]
    if case == "jdl":
        assert expected_payload["correction_version"] == 3
        assert expected_payload["supersedes"] == (
            "validation/financial_reports/corrections/jdl_2025fy_statements_v2.yaml"
        )
        assert expected_payload["source_sha256"] == result.source_sha256
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


def test_jdl_balance_sheet_excludes_equity_changes_continuation_page() -> None:
    """资产负债表页界限不得把后续权益变动表当成期初/期末余额。"""
    content = CASES["jdl"]["pdf"].read_bytes()
    result = extract_statements(content, adapter_id="hk_traditional_text")
    balance = result.statements["合并资产负债表"]
    names = {row["item"] for row in balance}

    assert max(row["page"] for row in balance) == 109
    assert not names.intersection(JDL_EQUITY_PAGE_FALSE_BALANCE_ROWS)
    by_name = {row["item"]: row for row in balance}
    assert by_name["資產總額"]["期末余额"] == 124599558
    assert by_name["資產總額"]["期初余额"] == 117867788
    assert by_name["權益總額"]["期末余额"] == 59784729
    assert by_name["負債總額"]["期末余额"] == 64814829


def test_jdl_comprehensive_income_page_is_a_distinct_statement() -> None:
    """第107页综合收益表不得并入利润表，重复归属行须在各表内分别保留。"""
    content = CASES["jdl"]["pdf"].read_bytes()
    result = extract_statements(content, adapter_id="hk_traditional_text")

    income = result.statements["合并利润表"]
    comprehensive = result.statements["合并综合收益表"]
    assert max(row["page"] for row in income) == 106
    assert min(row["page"] for row in comprehensive) == 107
    assert max(row["page"] for row in comprehensive) == 107

    income_profit = [row for row in income if row["item"] == "年度利潤"]
    comprehensive_profit = [row for row in comprehensive if row["item"] == "年度利潤"]
    assert len(income_profit) == len(comprehensive_profit) == 1
    assert income_profit[0]["本期发生额"] == comprehensive_profit[0]["本期发生额"] == 6890045

    for name in ("本公司所有者", "非控制性權益"):
        assert len([row for row in income if row["item"] == name]) == 1
        assert len([row for row in comprehensive if row["item"] == name]) == 1

    check_labels = {check.label for check in result.checks}
    assert "年度綜合收益=年度利潤+其他綜合收益 [本期发生额]" in check_labels
    assert "年度綜合收益=本公司所有者+非控制性權益 [上期发生额]" in check_labels
    assert all(check.status == "一致" for check in result.checks)


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


def test_sf_2026h1_combined_company_report_extracts_merged_columns() -> None:
    """合并及公司报表按首两列抽合并口径，不得误取公司列。"""
    pdf = SAMPLES / "sf_002352/SF_2026_H1_report.pdf"
    result = extract_statements(pdf.read_bytes(), adapter_id="cn_ashare_table")

    assert result.statements["合并资产负债表"]
    balance = {row["item"]: row for row in result.statements["合并资产负债表"]}
    assert balance["资产总计"]["期末余额"] == 228885266
    assert balance["负债及股东权益总计"]["期末余额"] == 228885266
    income = {row["item"]: row for row in result.statements["合并利润表"]}
    assert income["营业收入"]["本期发生额"] == 155506421
    assert income["营业收入"]["上期发生额"] == 146858174
    assert income["营业成本"]["本期发生额"] == -134593933
    assert income["归属于母公司股东的净利润"]["本期发生额"] == 5501905
    assert income["少数股东损益"]["本期发生额"] == 468112
    assert income["其中：对联营企业和合营企业的投资收益/(损失)"]["本期发生额"] == 171425
    assert income["基本每股收益(人民币元)"]["本期发生额"] == 1.10
    cashflow = {row["item"]: row for row in result.statements["合并现金流量表"]}
    assert cashflow["经营活动产生/(使用)的现金流量净额"]["本期发生额"] == 11171404
    assert cashflow["处置固定资产和其他长期资产收回的现金"]["本期发生额"] == 90947
    assert cashflow["分配股利、利润或偿付利息支付的现金"]["本期发生额"] == -2755780


def test_tencent_fy2025_annual_report_uses_dynamic_statement_titles() -> None:
    pdf = SAMPLES / "tencent_0700/Tencent_FY2025_annual_report.pdf"
    result = extract_statements(pdf.read_bytes())

    assert result.adapter_id == "hk_traditional_text"
    income = {row["item"]: row for row in result.statements["合并利润表"]}
    assert income["收入成本"]["本期发生额"] == -329173
    assert income["毛利"]["本期发生额"] == 422593
    cashflow = {row["item"]: row for row in result.statements["合并现金流量表"]}
    assert cashflow["經營活動所得現金流量淨額"]["本期发生额"] == 303052


def test_zto_duplicated_text_layer_uses_reliable_text_extractor() -> None:
    pdf = REPO_ROOT / (
        "validation/financial_reports/original/zto_2026q1/ZTO_2026_Q1_results_announcement_c.pdf"
    )
    result = extract_statements(pdf.read_bytes())

    assert result.adapter_id == "hk_results_announcement"
    income = {row["item"]: row for row in result.statements["合并利润表"]}
    assert income["收入"]["本期发生额"] == 13282364
    assert income["淨利潤"]["本期发生额"] == 2156356
    cashflow = {row["item"]: row for row in result.statements["合并现金流量表"]}
    assert cashflow["經營活動產生的現金淨額"]["本期发生额"] == 2789045
    non_gaap = {row["item"]: row for row in result.statements["Non-GAAP 调节"]}
    assert non_gaap["調整後淨利潤"]["本期发生额"] == 2377080


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
