"""客观报告图表的概念板语义回归测试。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from matplotlib.colors import to_hex

from flow_api.statements import objective_report_charts
from flow_api.visual_tokens import VISUAL_TOKENS


def test_cashflow_bars_use_category_colors_even_for_negative_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def capture(fig: Any) -> bytes:
        captured["figure"] = fig
        return b"png"

    monkeypatch.setattr(objective_report_charts, "_finish", capture)
    result = objective_report_charts.cashflow_bars(
        Decimal("100"), Decimal("-80"), Decimal("30")
    )

    assert result == b"png"
    colors = [to_hex(patch.get_facecolor()) for patch in captured["figure"].axes[0].patches]
    assert colors == [
        VISUAL_TOKENS["colors-data-revenue"].lower(),
        VISUAL_TOKENS["colors-brand-gold"].lower(),
        VISUAL_TOKENS["colors-data-cash"].lower(),
    ]
