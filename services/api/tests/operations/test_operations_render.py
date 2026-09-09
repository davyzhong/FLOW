"""O3：六主题概览 HTML 渲染（复用 objective 渲染链与打印链）。

- 每个可算指标按事实卡片渲染：值 + 比较基准 + 口径（借鉴 #1/#2）；
- not_applicable 主题渲染「待内部数据」状态与 typed 原因，不隐藏不伪造；
- 管理关注 ≤3 条带方向标签（借鉴 #5）；叙事按 #13 客观部分组织，
  行动章显式标注不在客观报告范围（U5 门禁）。
"""

from __future__ import annotations

from flow_api.operations.engine import (
    OperationsMetricItem,
    OperationsOverview,
    OperationsTheme,
)
from flow_api.operations.renderers import render_operations_html


def _overview() -> OperationsOverview:
    return OperationsOverview(
        report_id="r-1",
        catalog_id="flow.analysis.objective_finance.v1",
        themes=[
            OperationsTheme(
                theme_id="growth_quality",
                name="增长质量",
                availability="financial_report",
                status="available",
                metrics=[
                    OperationsMetricItem(
                        entry_id="revenue_yoy",
                        name="营业收入同比",
                        status="computed",
                        value="0.1260",
                        basis="上年同期",
                        caliber_note="本期/上年同期−1",
                    ),
                    OperationsMetricItem(
                        entry_id="revenue_growth",
                        name="营业收入增长率",
                        status="not_computable",
                        reason="fact_missing",
                        source="metric_dictionary",
                    ),
                ],
            ),
            OperationsTheme(
                theme_id="users_channels",
                name="用户与渠道",
                availability="internal_process",
                status="not_applicable",
                reason="internal_data_required",
                metrics=[],
            ),
        ],
        management_watch=[
            {
                "code": "cash_content_below_one",
                "message": "净利润现金含量 0.6000，经营现金流低于净利润",
                "direction": "negative",
            }
        ],
    )


def test_renders_fact_cards_with_basis_and_caliber() -> None:
    html = render_operations_html(_overview())
    assert "营业收入同比" in html and "0.1260" in html
    assert "上年同期" in html, "值必须伴随比较基准（借鉴 #1）"
    assert "本期/上年同期−1" in html, "口径必须可见（借鉴 #2）"


def test_renders_not_applicable_with_typed_reason() -> None:
    html = render_operations_html(_overview())
    assert "待内部数据" in html
    assert "internal_data_required" in html
    assert "fact_missing" in html, "不可算指标的 typed 原因必须可见"


def test_renders_management_watch_with_direction() -> None:
    html = render_operations_html(_overview())
    assert "管理关注" in html
    assert "净利润现金含量 0.6000" in html
    assert "关注" in html


def test_narrative_marks_action_layer_out_of_scope() -> None:
    html = render_operations_html(_overview())
    assert "行动" in html and "不在客观报告范围" in html, (
        "#9：行动章必须显式标注不在客观报告范围（U5 门禁）"
    )
