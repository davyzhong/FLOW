# -*- coding: utf-8 -*-
"""自包含高密度财报分析 PDF 生成器（不依赖数据库/flow_api）。

直接读取 P5 抽取 YAML，计算全部可算指标，生成 matplotlib 图表，
渲染 A4 富报告 HTML，用固定 Chromium 打为 PDF。

用法：
    cd services/api && uv run python ../../scripts/rich_report.py \
        --yaml ../../docs/implementation/p5/sf_2026q1_statements.yaml \
        --company 顺丰控股 --period 2026Q1 --out ../../work/reports/
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import subprocess
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

import matplotlib
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# ---- 字体 ----
plt.rcParams["font.sans-serif"] = [
    "PingFang SC", "Hiragino Sans GB", "Heiti SC",
    "Arial Unicode MS", "Noto Sans CJK SC",
]
plt.rcParams["axes.unicode_minus"] = False

BLUE, LBLUE, ORANGE, LORANGE = "#2f6bd8", "#9db6e8", "#e08a3c", "#f2c57c"
GREEN, NEG, GREY, DARK = "#2e8b57", "#c2604f", "#8a94a6", "#14337a"
PALETTE = ["#2f6bd8", "#e08a3c", "#2e8b57", "#c2604f", "#7c5cbf", "#d4a843"]
DPI = 150

# ===================================================== 数据模型


@dataclass
class LineItem:
    name: str
    current: Decimal | None = None
    prior: Decimal | None = None
    begin: Decimal | None = None
    end: Decimal | None = None


@dataclass
class Statement:
    name: str
    items: dict[str, LineItem] = field(default_factory=dict)

    def get(self, pattern: str) -> LineItem | None:
        norm = pattern.replace(" ", "").replace("：", "")
        for name, item in self.items.items():
            if norm in name.replace(" ", "").replace("：", ""):
                return item
        return None


@dataclass
class CompanyData:
    name: str
    stock_code: str
    period: str
    unit: str
    statements: dict[str, Statement] = field(default_factory=dict)

    def bs(self) -> Statement | None:
        return self.statements.get("合并资产负债表")

    def is_(self) -> Statement | None:
        return self.statements.get("合并利润表")

    def cf(self) -> Statement | None:
        return self.statements.get("合并现金流量表")


# ===================================================== 解析

def parse_yaml(path: Path) -> CompanyData:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    unit = data.get("unit", "")
    cd = CompanyData(
        name=data.get("company", path_stem(path)),
        stock_code=data.get("stock_code", ""),
        period=data.get("period", ""),
        unit=unit,
    )
    for stype, raw_items in data.get("statements", {}).items():
        stmt = Statement(name=stype)
        for raw in raw_items:
            name = raw.get("item", "").strip()
            if not name:
                continue
            cur = _d(raw.get("本期发生额"))
            pri = _d(raw.get("上期发生额"))
            end = _d(raw.get("期末余额"))
            begin = _d(raw.get("期初余额"))
            stmt.items[name] = LineItem(name=name, current=cur, prior=pri,
                                        begin=begin, end=end)
        cd.statements[stype] = stmt
    return cd


def path_stem(p: Path) -> str:
    return p.stem


def _d(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


# ===================================================== 指标计算

def _safe_div(a: Decimal | None, b: Decimal | None) -> Decimal | None:
    if a is None or b in (None, Decimal(0)):
        return None
    return a / b


def _d(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _get(stmt: Statement | None, *patterns: str) -> LineItem | None:
    if stmt is None:
        return None
    for pattern in patterns:
        item = stmt.get(pattern)
        if item and item.current is not None:
            return item
    return None


def compute_metrics(cd: CompanyData) -> dict[str, Any]:
    """从原始行项目计算全部可算的财务指标。"""
    bs = cd.bs()
    inc = cd.is_()
    cf = cd.cf()
    m: dict[str, Any] = {}

    def val(stmt: Statement | None, *names: str, col: str = "current") -> Decimal | None:
        item = _get(stmt, *names)
        return getattr(item, col, None) if item else None

    # 收入
    m["revenue"] = val(inc, "一、营业总收入", "其中：营业收入", "营业收入", "营业总收入")
    rev_prior = val(inc, "一、营业总收入", "其中：营业收入", "营业收入", "营业总收入", col="prior")
    m["revenue_yoy"] = _safe_div((m["revenue"] - rev_prior), abs(rev_prior)) if rev_prior else None

    # 利润
    m["net_profit"] = val(inc, "五、净利润", "四、净利润", "净利润")
    m["attr_net_profit"] = val(inc, "1.归属于母公司所有者的净利润",
                               "归属于母公司所有者的净利润",
                               "归属于上市公司股东的净利润")
    attr_prior = val(inc, "1.归属于母公司所有者的净利润",
                     "归属于母公司所有者的净利润",
                     "归属于上市公司股东的净利润", col="prior")
    m["profit_yoy"] = _safe_div((m["attr_net_profit"] - attr_prior), abs(attr_prior)) if attr_prior else None
    m["operating_profit"] = val(inc, "三、营业利润", "三、营业利润（亏损以", "营业利润")
    m["total_profit"] = val(inc, "四、利润总额", "四、利润总额（亏损总额以")

    # 成本费用
    m["cogs"] = val(inc, "其中：营业成本", "营业成本")
    m["selling_exp"] = val(inc, "销售费用")
    m["admin_exp"] = val(inc, "管理费用")
    m["rnd_exp"] = val(inc, "研发费用")
    m["fin_exp"] = val(inc, "财务费用", "其中：利息费用")
    m["income_tax"] = val(inc, "减：所得税费用", "所得税费用")

    # 现金流
    m["ocf"] = val(cf, "经营活动产生的现金流量净额", "经营活动产生的现金流量")
    m["icf"] = val(cf, "投资活动产生的现金流量净额", "投资活动产生的现金流量")
    m["fin_cf"] = val(cf, "筹资活动产生的现金流量净额", "筹资活动产生的现金流量")
    m["capex"] = val(cf, "购建固定资产、无形资产和其他长期资产支付的现金",
                     "购建固定资产、无形资产和其他长期资产支付的现金")
    m["cash_end"] = val(cf, "六、期末现金及现金等价物余额", "六、期末现金及现金等价物余额")

    # 资产负债表
    m["total_assets"] = val(bs, "资产总计", "资产总额")
    m["total_liab"] = val(bs, "负债合计", "负债总额")
    m["equity"] = val(bs, "所有者权益合计", "股东权益合计", "权益合计")
    m["current_assets"] = val(bs, "流动资产合计", "流动资产")
    m["current_liab"] = val(bs, "流动负债合计", "流动负债")
    m["inventory"] = val(bs, "存货", "存货")
    m["ar"] = val(bs, "应收账款", "应收账款")
    m["cash"] = val(bs, "货币资金", "货币资金")

    # ---- 派生比率 ----
    def ratio(a: Decimal | None, b: Decimal | None) -> Decimal | None:
        return _safe_div(a, b)

    if m["revenue"] and m["cogs"] is not None:
        m["gross_margin"] = ratio(m["revenue"] - m["cogs"], m["revenue"])
    else:
        m["gross_margin"] = None
    m["net_margin"] = ratio(m["net_profit"], m["revenue"])
    m["attr_margin"] = ratio(m["attr_net_profit"], m["revenue"])
    if m["revenue"]:
        for key, exp_key in [("selling_ratio", "selling_exp"), ("admin_ratio", "admin_exp"),
                             ("rnd_ratio", "rnd_ratio"), ("fin_ratio", "fin_exp")]:
            exp_val = m.get(exp_key)
            m[key] = ratio(exp_val, m["revenue"]) if exp_val is not None else None
    m["debt_ratio"] = ratio(m["total_liab"], m["total_assets"])
    m["current_ratio"] = ratio(m["current_assets"], m["current_liab"])
    if m["current_liab"] and m["inventory"]:
        quick_assets = m["current_assets"] - m["inventory"]
        m["quick_ratio"] = ratio(quick_assets, m["current_liab"])
    else:
        m["quick_ratio"] = None
    m["ocf_ratio"] = ratio(m["ocf"], m["net_profit"])
    m["roe"] = ratio(m["attr_net_profit"], m["equity"])
    if m["total_assets"] and m["equity"]:
        m["asset_turnover"] = ratio(m["revenue"], m["total_assets"])
        m["equity_multiplier"] = ratio(m["total_assets"], m["equity"])
    else:
        m["asset_turnover"] = None
        m["equity_multiplier"] = None

    return m


# ===================================================== 格式化

def fmt_amount(value: Decimal | None, unit: str = "") -> str:
    if value is None:
        return "—"
    neg = value < 0
    d = abs(value)
    if d >= Decimal(100_000_000):
        text = f"{d / Decimal(100_000_000):,.2f} 亿"
    elif d >= Decimal(10_000):
        text = f"{d / Decimal(10_000):,.2f} 万"
    else:
        text = f"{d:,.0f}"
    return ("-" + text) if negative else text


def fmt_pct(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.2f}%"


def fmt_ratio(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


# ===================================================== 图表生成

def _finish(fig) -> bytes:
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def chart_bar_compare(title: str, labels: list[str], values: list[Decimal | None],
                      color_cur: str = BLUE, color_pri: str = LBLUE) -> bytes:
    cur = values[0] if values[0] is not None else Decimal(0)
    pri = values[1] if values[1] is not None else Decimal(0)
    floats, unit = _scale([cur, pri])
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    bars = ax.bar(["上年同期", "本期"], floats, color=[LBLUE, color_cur], width=0.5)
    for bar, value in zip(bars, (pri, cur)):
        if value is not None:
            ax.annotate(f"{float(value):,.0f}",
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    return _finish(fig)


def chart_hbar(title: str, items: list[tuple[str, Decimal]]) -> bytes:
    pairs = [(n, v) for n, v in items if v is not None and abs(v) > 0]
    if not pairs:
        return b""
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    names = [n for n, _ in pairs]
    floats, unit = _scale([v for _, v in pairs])
    fig, ax = plt.subplots(figsize=(6.5, max(2.0, 0.5 * len(pairs) + 1.0)))
    y_pos = range(len(pairs))
    ax.barh(list(y_pos), floats, color=BLUE, height=0.55)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names, fontsize=9)
    ax.invert_yaxis()
    ax.set_title(f"{title}（{unit}）", fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.2)
    for bar, (_, value) in zip(ax.patches, pairs):
        ax.annotate(f"{float(value):,.0f}",
                    (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    va="center", fontsize=8.5)
    return _finish(fig)


def chart_donut(title: str, items: list[tuple[str, Decimal]]) -> bytes:
    pairs = [(n, abs(v)) for n, v in items if v is not None and abs(v) > 0]
    if len(pairs) < 2:
        return b""
    names = [n for n, _ in pairs]
    values = [float(v) for _, v in pairs]
    fig, ax = plt.subplots(figsize=(5.5, 4.0))
    colors = PALETTE[: len(pairs)]
    wedges, texts, autotexts = ax.pie(
        values, labels=names, autopct="%1.1f%%", startangle=140,
        colors=colors, pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5),
        textprops=dict(fontsize=9),
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color("#1a2233")
    ax.set_title(title, fontsize=11, fontweight="bold")
    return _finish(fig)


def chart_cashflow_bars(ocf: Decimal | None, icf: Decimal | None,
                        fin_cf: Decimal | None) -> bytes:
    labels = ["经营", "投资", "筹资"]
    values = [ocf, icf, fin_cf]
    floats = [float(v) if v is not None else 0.0 for v in values]
    colors = [GREEN if v >= 0 else NEG for v in floats]
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    bars = ax.bar(labels, floats, color=colors, width=0.5)
    ax.axhline(0, color="#5b6478", linewidth=0.8)
    for bar, value in zip(bars, floats):
        ax.annotate(f"{value:,.0f}", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom" if value >= 0 else "top", fontsize=9)
    ax.set_title("现金流量净额（万元）", fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    return _finish(fig)


def chart_dupont(net_margin, asset_turnover, equity_multiplier, roe) -> bytes:
    factors = ["净利率", "总资产周转率", "权益乘数"]
    values = [
        float(net_margin * 100) if net_margin else 0.0,
        float(asset_turnover) if asset_turnover else 0.0,
        float(equity_multiplier) if equity_multiplier else 0.0,
    ]
    formatted = [
        f"{net_margin * 100:.2f}%" if net_margin else "—",
        f"{asset_turnover:.3f}" if asset_turnover else "—",
        f"{equity_multiplier:.3f}" if equity_multiplier else "—",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.8))
    for ax, label, value, text, color in zip(
        axes, factors, values, formatted, [BLUE, ORANGE, GREEN]
    ):
        ax.bar([label], [value], color=color, width=0.45)
        ax.set_title(f"{label}\n{text}", fontsize=10, fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xticks([])
        ax.set_ylim(0, max(value * 1.3, 0.1))
    fig.suptitle(
        f"ROE = {float(roe) * 100:.2f}%" if roe else "ROE 不可计算",
        fontsize=13, fontweight="bold", color=DARK, y=1.02,
    )
    return _finish(fig)
