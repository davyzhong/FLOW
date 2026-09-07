"""报告图表生成（matplotlib → PNG bytes，供 HTML 内嵌 base64）。

风格：蓝金配色、浅色背景、中文标注（PingFang SC 等 macOS/中文环境自带字体）。
所有函数返回 PNG 字节；调用方以 data URI 内嵌进报告 HTML。
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["font.sans-serif"] = [
    "PingFang SC", "Hiragino Sans GB", "Heiti SC", "Arial Unicode MS",
    "Noto Sans CJK SC", "Microsoft YaHei",
]
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#2f6bd8"
LIGHT_BLUE = "#9db6e8"
ORANGE = "#e08a3c"
GREY = "#8a94a6"
NEG = "#c2604f"
GREEN = "#2e8b57"

DPI = 150


def _finish(fig: Any) -> bytes:
    fig.tight_layout()
    import io

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=DPI, facecolor="white")
    plt.close(fig)
    return buffer.getvalue()


def _scale(values: Sequence[Decimal | None]) -> tuple[list[float], str]:
    """自动量纲：返回 (数值列表[亿], 单位标签)。"""
    peak = max((abs(v) for v in values if v is not None), default=Decimal(0))
    if peak >= Decimal(1_000_000_000):
        return [float(v / Decimal(1_000_000_000)) if v is not None else 0.0 for v in values], "亿元"
    if peak >= Decimal(1_000_000):
        return [float(v / Decimal(1_000_000)) if v is not None else 0.0 for v in values], "百万元"
    if peak >= Decimal(1_000):
        return [float(v / Decimal(1_000)) if v is not None else 0.0 for v in values], "千元"
    return [float(v) if v is not None else 0.0 for v in values], "元"


def bar_compare(title: str, current: Decimal | None, prior: Decimal | None,
                unit_note: str = "", color: str = BLUE) -> bytes:
    values = [prior, current]
    floats, unit = _scale(values)
    labels = ["上年同期", "本期"]
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    bars = ax.bar(labels, floats, color=[LIGHT_BLUE, color], width=0.5)
    for bar, value in zip(bars, values, strict=False):
        if value is not None:
            ax.annotate(f"{float(value):,.0f}", (bar.get_x() + bar.get_width() / 2,
                        bar.get_height()), ha="center", va="bottom", fontsize=9)
    ax.set_title(f"{title}（{unit}）", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    if floats[1] and floats[0]:
        delta = (floats[1] - floats[0]) / abs(floats[0]) * 100
        ax.set_xlabel(f"同比 {delta:+.1f}%", fontsize=10)
    return _finish(fig)


def hbar_structure(title: str, items: list[tuple[str, Decimal]], unit_note: str = "",
                   show_share_of: Decimal | None = None) -> bytes:
    pairs = [(name, value) for name, value in items if value is not None]
    pairs.sort(key=lambda pair: abs(pair[1]), reverse=True)
    names = [name for name, _ in pairs]
    floats, unit = _scale([value for _, value in pairs])
    fig, ax = plt.subplots(figsize=(6.4, 0.62 * len(pairs) + 1.4))
    y = range(len(pairs))
    colors = [BLUE if value >= 0 else NEG for _, value in pairs]
    ax.barh(list(y), floats, color=colors, height=0.62)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=10)
    ax.invert_yaxis()
    ax.set_title(f"{title}（{unit}）", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    total = sum(abs(value) for _, value in pairs) or Decimal(1)
    for bar, (_, value) in zip(ax.patches, pairs, strict=False):
        share = abs(Decimal(value)) / total * 100
        ax.annotate(f"{float(value):,.0f}（{share:.0f}%）",
                    (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    va="center", fontsize=8.5)
    return _finish(fig)


def donut(title: str, items: list[tuple[str, Decimal | None]]) -> bytes:
    pairs = [(name, value) for name, value in items
             if value is not None and value > 0]
    if len(pairs) < 2:
        raise ValueError("donut 需要至少两个正数项")
    names = [name for name, _ in pairs]
    values = [float(value) for _, value in pairs]
    palette = ["#2f6bd8", "#9db6e8", "#e08a3c", "#f2c57c", "#7fb3a3", "#b7a6d9", "#d98a8a"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    wedges, _, autotexts = ax.pie(
        values, labels=names, autopct="%1.1f%%", startangle=90,
        colors=palette[: len(pairs)], pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="white"),
        textprops=dict(fontsize=9),
    )
    for text in autotexts:
        text.set_fontsize(8.5)
        text.set_color("#1a2233")
    ax.set_title(title, fontsize=11)
    return _finish(fig)


def cashflow_bars(operating: Decimal | None, investing: Decimal | None,
                  financing: Decimal | None, unit_note: str = "") -> bytes:
    labels = ["经营", "投资", "筹资"]
    floats, unit = _scale([operating, investing, financing])
    colors = [GREEN if value >= 0 else NEG for value in floats]
    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    bars = ax.bar(labels, floats, color=colors, width=0.5)
    ax.axhline(0, color="#5b6478", linewidth=0.8)
    for bar, value in zip(bars, (operating, investing, financing), strict=False):
        if value is not None:
            ax.annotate(f"{float(value):,.0f}",
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha="center", va="bottom" if value >= 0 else "top", fontsize=9)
    ax.set_title(f"现金流量净额（{unit_note or unit}）", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    return _finish(fig)


def dupont_chart(net_margin: Decimal | None, asset_turnover: Decimal | None,
                 equity_multiplier: Decimal | None, roe: Decimal | None) -> bytes:
    factors = ["净利率", "总资产周转率", "权益乘数"]
    values = [        float(net_margin * 100) if net_margin is not None else 0.0,
        float(asset_turnover) if asset_turnover is not None else 0.0,
        float(equity_multiplier) if equity_multiplier is not None else 0.0,
    ]
    formatted = [
        f"{float(net_margin * 100):.2f}%" if net_margin is not None else "—",
        f"{float(asset_turnover):.3f}" if asset_turnover is not None else "—",
        f"{float(equity_multiplier):.3f}" if equity_multiplier is not None else "—",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4))
    for ax, label, value, text in zip(axes, factors, values, formatted, strict=False):
        ax.bar([label], [value], color=BLUE, width=0.45)
        ax.set_title(f"{label}\n{text}", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xticks([])
    fig.suptitle(
        f"杜邦分解：ROE = {float(roe) * 100:.2f}%（期末权益口径）"
        if roe is not None else "杜邦分解",
        fontsize=11, y=1.02,
    )
    return _finish(fig)
