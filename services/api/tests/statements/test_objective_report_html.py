"""客观分析报告 HTML 渲染器与 Chromium PDF 打印机契约测试（P08 前置/格式评审）。

- render_objective_html：A4 打印 CSS、公司/期间/目录身份、逐条目 值+口径+来源引用、
  not_computable 原因、HTML 转义、D049 客观性声明；
- print_pdf：固定 Chromium 将 HTML 打为 PDF（%PDF 魔数），Chromium 缺失时抛
  ChromiumNotFoundError。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from flow_api.analysis.objective import (
    ObjectiveAnalysisResult,
    ObjectiveEntryResult,
    ObjectiveStatus,
)
from flow_api.statements.objective_report_html import render_objective_html
from flow_api.statements.objective_report_pdf import ChromiumNotFoundError, print_pdf


class _FakeReport:
    company_name = "测试公司"
    stock_code = "000000.SZ"
    report_kind = "一季报"
    period_label = "2026Q1"
    unit_note = "人民币千元"


def _result() -> ObjectiveAnalysisResult:
    return ObjectiveAnalysisResult(
        report_id="report-1",
        catalog_id="flow.analysis.objective_finance.v1",
        entries=(
            ObjectiveEntryResult(
                entry_id="asset_structure",
                name="资产结构",
                kind="structure",
                status=ObjectiveStatus.COMPUTED,
                value="固定资产 12.3%",
                basis="期末资产总计",
                caliber_note="占总资产比重",
                refs=("bs.fixed_assets", "bs.total_assets"),
                parts=(),
            ),
            ObjectiveEntryResult(
                entry_id="revenue_yoy",
                name="营业收入同比",
                kind="yoy",
                status=ObjectiveStatus.NOT_COMPUTABLE,
                value=None,
                basis="上年同期",
                caliber_note="同比 = 本期 / 上年同期 − 1",
                refs=("is.revenue",),
                reason="上年同期值缺失",
            ),
        ),
    )


def test_render_contains_identity_entries_and_print_css() -> None:
    html = render_objective_html(_FakeReport(), _result(), generated_at=datetime(2026, 9, 4, 9, 0, tzinfo=UTC))
    assert "测试公司" in html and "000000.SZ" in html
    assert "2026Q1" in html and "一季报" in html
    assert "flow.analysis.objective_finance.v1" in html
    assert "@page" in html and "A4" in html
    assert "资产结构" in html and "12.3%" in html
    assert "上年同期值缺失" in html
    assert "占总资产比重" in html and "bs.fixed_assets" in html
    assert "不构成业务因果" in html or "客观财务分析" in html


def test_render_escapes_html_in_dynamic_values() -> None:
    result = ObjectiveAnalysisResult(
        report_id="r",
        catalog_id="c",
        entries=(
            ObjectiveEntryResult(
                entry_id="x",
                name="<script>alert(1)</script>",
                kind="ratio",
                status=ObjectiveStatus.COMPUTED,
                value="<b>1.0</b>",
                basis="basis",
                caliber_note="note",
                refs=(),
            ),
        ),
    )
    html = render_objective_html(_FakeReport(), result, generated_at=datetime(2026, 9, 4, tzinfo=UTC))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_print_pdf_produces_pdf_bytes(tmp_path: Path) -> None:
    html = render_objective_html(_FakeReport(), _result(), generated_at=datetime(2026, 9, 4, tzinfo=UTC))
    out = tmp_path / "report.pdf"
    try:
        print_pdf(html, out_path=out)
    except ChromiumNotFoundError:
        pytest.skip("本机未找到固定 Chromium，跳过打印器冒烟")
    assert out.exists()
    assert out.read_bytes()[:5] == b"%PDF-"
    assert out.stat().st_size > 1000
