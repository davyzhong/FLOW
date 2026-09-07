"""客观财务分析报告 v2 渲染器与 Chromium PDF 打印机契约测试。

v2 报告结构：封面身份块 → 摘要 → 盈利与现金（对比条形）→ 资产/资本与偿债 →
杜邦分解 → 引擎条目（口径化）→ 数据边界 → 附录逐行对比 → 页脚。
所有动态值 html.escape；数值格式化（亿/万 + 百分比）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from flow_api.analysis.objective import (
    ObjectiveAnalysisResult,
    ObjectiveEntryResult,
    ObjectiveStatus,
)
from flow_api.statements.objective_report_html import render_objective_report_v3
from flow_api.statements.objective_report_pdf import ChromiumNotFoundError, print_pdf

REPORT = SimpleNamespace(
    company_name="测试公司",
    stock_code="000000.SZ",
    report_kind="一季报",
    period_label="2026Q1",
    unit_note="人民币千元",
)
GENERATED = datetime(2026, 9, 4, 9, 0, tzinfo=UTC)

NORMALIZED = [
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并利润表",
        item_name="营业收入", item_id="is.revenue",
        value_current=2_137_000, value_prior=1_800_000,
        value_begin=None, value_end=None,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并利润表",
        item_name="归属于上市公司股东的净利润", item_id="is.net_profit",
        value_current=252_000, value_prior=210_000,
        value_begin=None, value_end=None,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并现金流量表",
        item_name="经营活动产生的现金流量净额", item_id="cf.operating",
        value_current=300_000, value_prior=None,
        value_begin=None, value_end=None,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并资产负债表",
        item_name="资产总计", item_id="bs.total_assets",
        value_current=2_000_000, value_prior=None,
        value_begin=1_900_000, value_end=2_000_000,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并资产负债表",
        item_name="负债合计", item_id="bs.total_liab",
        value_current=1_200_000, value_prior=None,
        value_begin=None, value_end=None,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并资产负债表",
        item_name="所有者权益合计", item_id="bs.equity",
        value_current=800_000, value_prior=None,
        value_begin=None, value_end=None,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并资产负债表",
        item_name="流动资产合计", item_id="bs.current_assets",
        value_current=900_000, value_prior=None,
        value_begin=None, value_end=None,
    ),
    SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并资产负债表",
        item_name="流动负债合计", item_id="bs.current_liab",
        value_current=450_000, value_prior=None,
        value_begin=None, value_end=None,
    ),
]


def _result() -> ObjectiveAnalysisResult:
    return ObjectiveAnalysisResult(
        report_id="r1",
        catalog_id="flow.analysis.objective_finance.v1",
        entries=(
            ObjectiveEntryResult(
                entry_id="revenue_yoy",
                name="营业收入同比",
                kind="yoy",
                status=ObjectiveStatus.COMPUTED,
                value="18.7%",
                basis="上年同期",
                caliber_note="同比 = 本期 / 上年同期 − 1",
                refs=("is.revenue:cur", "is.revenue:prior_yoy"),
            ),
            ObjectiveEntryResult(
                entry_id="gross_margin",
                name="毛利率",
                kind="ratio",
                status=ObjectiveStatus.NOT_COMPUTABLE,
                value=None,
                basis="毛利 / 营业收入",
                caliber_note="毛利缺失",
                refs=("metric.gross_margin",),
                reason="上年同期毛利值缺失",
            ),
        ),
    )


def _render() -> str:
    return render_objective_report_v3(REPORT, _result(), NORMALIZED, generated_at=GENERATED)


def test_v2_cover_summary_and_structure() -> None:
    html = _render()
    assert "测试公司" in html and "000000.SZ" in html and "2026Q1" in html
    assert "flow.analysis.objective_finance.v1" in html
    # 摘要：金额格式化（亿）与同比
    assert "21.37 亿" in html
    assert "同比" in html
    # 章节
    for heading in ("摘要", "盈利与现金", "资产、资本与偿债",
                    "客观分析引擎条目", "数据边界与不可算项", "附录：归一化报表逐行对比"):
        assert heading in html


def test_v2_comparison_bars_and_dupont() -> None:
    html = _render()
    assert "data:image/png;base64," in html
    assert "上年同期" in html
    # 杜邦：期末口径三因子
    assert "杜邦分解" in html and "ROE" in html
    assert "净利率" in html and "总资产周转率" in html and "权益乘数" in html
    # 数值格式化：亿/万
    assert "亿" in html or "万" in html


def test_v2_boundary_and_appendix() -> None:
    html = _render()
    assert "毛利率" in html and "数据不足" in html
    assert "归一化报表逐行对比" in html
    assert "营业收入" in html  # 附录含逐行
    assert "现金流量表" in html


def test_v2_escapes_html() -> None:
    malicious = SimpleNamespace(
        report_id="r1", mapping_version="v1", statement_type="合并利润表",
        item_name="<script>x</script>", item_id=None,
        value_current=1, value_prior=None, value_begin=None, value_end=None,
    )
    html = render_objective_report_v3(REPORT, _result(), [malicious], generated_at=GENERATED)
    assert "<script>x</script>" not in html


def test_print_pdf_produces_pdf_bytes(tmp_path: Path) -> None:
    from flow_api.statements.objective_report_pdf import print_pdf

    out = tmp_path / "report.pdf"
    try:
        print_pdf(_render(), out_path=out)
    except ChromiumNotFoundError:
        pytest.skip("本机未找到固定 Chromium，跳过打印器冒烟")
    assert out.exists()
    assert out.read_bytes()[:5] == b"%PDF-"
    assert out.stat().st_size > 1000
