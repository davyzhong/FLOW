"""四表一注覆盖与质量规则（B04）测试。

- 季报（顺丰）：三表齐全且勾稽通过 → 覆盖全 passed，不标四表一注完整（季报本就不要求）；
- 年报（京东物流）：权益变动表与附注缺失 → 不得标完整，阻断项为空但完整为 False；
- 业绩公告（腾讯）：简表 → 其余报表 not_applicable；
- 关键勾稽不平衡 → 阻断正式发布（publishable=False）；
- 权益变动表缺失的年报永不得标「四表一注完整」。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flow_api.statements.extraction import ExtractionCheck, ExtractionResult, extract_statements
from flow_api.statements.reconciliation import (
    CoverageStatus,
    evaluate_report_quality,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES = REPO_ROOT / "docs/knowledge-base/02_research/original/p5_samples"


def _load(name: str) -> bytes:
    return (SAMPLES / name).read_bytes()


def test_quarter_report_coverage_passes_but_not_four_statement_complete() -> None:
    result = extract_statements(_load("sf_002352/SF_2026_Q1_report.pdf"))
    quality = evaluate_report_quality(result, report_kind="一季报")
    by_type = {c.statement_type: c for c in quality.coverage}
    assert set(by_type) == {"合并资产负债表", "合并利润表", "合并现金流量表"}
    assert all(c.status == CoverageStatus.PASSED for c in quality.coverage)
    assert quality.publishable
    assert not quality.four_statements_complete, "季报不要求四表一注，不得标完整"


def test_annual_report_never_complete_without_equity_statement_and_notes() -> None:
    result = extract_statements(_load("jd_logistics_2618/JDL_FY2025_annual_report.pdf"))
    quality = evaluate_report_quality(result, report_kind="年报")
    by_type = {c.statement_type: c for c in quality.coverage}
    assert by_type["合并资产负债表"].status == CoverageStatus.PASSED
    assert by_type["合并所有者权益变动表"].status == CoverageStatus.MISSING
    assert by_type["附注"].status == CoverageStatus.MISSING
    assert not quality.four_statements_complete, "缺权益表与附注不得标四表完整"
    assert quality.publishable, "勾稽全过的年报不应有关键阻断"


def test_results_announcement_marks_other_statements_not_applicable() -> None:
    result = extract_statements(_load("tencent_0700/Tencent_2026_Q2_results.pdf"))
    quality = evaluate_report_quality(result, report_kind="业绩公告")
    by_type = {c.statement_type: c for c in quality.coverage}
    assert by_type["合并利润表"].status == CoverageStatus.PASSED
    assert quality.publishable


def test_critical_imbalance_blocks_publish() -> None:
    fake = ExtractionResult(
        adapter_id="cn_ashare_table",
        unit_note="人民币千元",
        statements={
            "合并资产负债表": [{"item": "资产总计", "期末余额": 1}],
            "合并利润表": [{"item": "五、净利润", "本期发生额": 1}],
            "合并现金流量表": [{"item": "六、期末现金及现金等价物余额", "本期发生额": 1}],
        },
        checks=(
            ExtractionCheck("资产总计=负债合计+所有者权益合计 [期末余额]", 100, 99, "不一致"),
            ExtractionCheck("净利润=归母+少数股东损益 [本期发生额]", 10, 10, "一致"),
        ),
        warnings=(),
        page_count=1,
        source_sha256="a" * 64,
    )
    quality = evaluate_report_quality(fake, report_kind="一季报")
    assert not quality.publishable
    assert quality.blockers == ("资产总计=负债合计+所有者权益合计 [期末余额]",)


def test_unknown_report_kind_rejected() -> None:
    result = extract_statements(_load("sf_002352/SF_2026_Q1_report.pdf"))
    with pytest.raises(ValueError, match="未知报告种类"):
        evaluate_report_quality(result, report_kind="旬报")


def test_missing_core_statement_blocks_publish() -> None:
    fake = ExtractionResult(
        adapter_id="cn_ashare_table",
        unit_note="人民币千元",
        statements={
            "合并利润表": [{"item": "五、净利润", "本期发生额": 1}],
        },
        checks=(),
        warnings=(),
        page_count=1,
        source_sha256="a" * 64,
    )
    quality = evaluate_report_quality(fake, report_kind="一季报")
    assert not quality.publishable
    assert any("missing_required_statement" in blocker for blocker in quality.blockers)


def test_announcement_publish_is_not_blocked_by_missing_tables() -> None:
    result = extract_statements(
        (REPO_ROOT / "docs/knowledge-base/02_research/original/p5_samples"
         / "tencent_0700/Tencent_2026_Q2_results.pdf").read_bytes()
    )
    quality = evaluate_report_quality(result, report_kind="业绩公告")
    assert quality.publishable
