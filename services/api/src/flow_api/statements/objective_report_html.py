"""客观财务分析报告渲染器 v3：KPI 卡片 + matplotlib 图表 + 多章节富报告。

图表由 objective_report_charts 生成（PNG base64 内嵌），PDF 由固定 Chromium 打印。
章节契约：封面身份块 → 摘要 → 盈利与现金 → 成本与费用 → 资产、资本与偿债 →
杜邦分解 → 客观分析引擎条目 → 数据边界与不可算项 → 附录逐行对比 → 页脚。
所有动态值 html.escape；金额格式化按报告 unit_note 换算（亿/万）。
"""

from __future__ import annotations

import base64
import html
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from flow_api.statements.objective_report_charts import (
    bar_compare,
    cashflow_bars,
    donut,
    dupont_chart,
    hbar_structure,
)

_PRINT_CSS = """
  @page { size: A4; margin: 14mm 12mm; }
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
         "Noto Sans CJK SC", sans-serif; color: #1a2233; font-size: 10pt;
         line-height: 1.5; margin: 0; background: #ffffff; }
  .cover { border-bottom: 2.5px solid #14337a; padding-bottom: 12px; margin-bottom: 14px; }
  .cover h1 { font-size: 20pt; margin: 0 0 6px; color: #14337a; }
  .cover .meta { color: #475069; font-size: 9.5pt; line-height: 1.7; }
  .disclaimer { background: #f0f4fc; border-left: 4px solid #14337a;
                padding: 7px 11px; font-size: 8.6pt; color: #37415c;
                margin: 0 0 14px; }
  h2 { font-size: 13pt; color: #14337a; border-left: 5px solid #14337a;
       padding-left: 9px; margin: 20px 0 8px; page-break-after: avoid; }
  h3 { font-size: 11pt; margin: 12px 0 5px; page-break-after: avoid; }
  p { margin: 4px 0; }
  .kpi-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 12px; }
  .kpi { flex: 1 1 21%; min-width: 130px; border: 1px solid #d5dae3;
         border-top: 3px solid #2f6bd8; padding: 7px 10px; }
  .kpi .label { font-size: 8.5pt; color: #5b6478; }
  .kpi .value { font-size: 13pt; font-weight: 700; color: #14337a;
                font-family: "JetBrains Mono", Menlo, monospace; }
  .delta.up { color: #a1260d; }  .delta.down { color: #0a7f3f; }
  .chart { margin: 10px 0 14px; page-break-inside: avoid; text-align: center; }
  .chart img { max-width: 100%; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0 14px; }
  th, td { border: 1px solid #ccd3e0; padding: 4px 8px; text-align: left;
           vertical-align: top; font-size: 9pt; }
  th { background: #e9eef9; font-weight: 600; }
  td { background: #ffffff; }
  tr { page-break-inside: avoid; }
  td.num { text-align: right; font-family: "JetBrains Mono", Menlo, monospace;
           white-space: nowrap; }
  .reason { color: #9a6700; font-size: 8.8pt; }
  .refs { color: #6b7280; font-size: 8pt; font-family: "JetBrains Mono", Menlo, monospace; }
  .muted { color: #6b7280; }
  .footer { margin-top: 24px; padding-top: 8px; border-top: 1px solid #ccd3e0;
            color: #6b7280; font-size: 8.3pt; }
  .pagebreak { page-break-before: always; }
"""


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _has(value: Any) -> bool:
    return value is not None


def _fmt_yi(value_scaled_yi: Decimal | None) -> str:
    if value_scaled_yi is None:
        return "—"
    negative = value_scaled_yi < 0
    d = abs(value_scaled_yi)
    text = f"{d:,.2f} 亿" if d >= Decimal("0.01") else f"{d * 10000:,.0f} 万"
    return ("-" + text) if negative else text


def _fmt_pct(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.2f}%"


def _fmt_pct_raw(value: Decimal) -> str:
    return f"{value * 100:.1f}%"


def _safe_div(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _change_pct(current: Decimal | None, prior: Decimal | None) -> Decimal | None:
    if current is None or prior is None or prior == 0:
        return None
    return (current - prior) / abs(prior)


def _kpi_card(label: str, value: str, delta: str = "", tone: str = "") -> str:
    return (
        f'<div class="kpi"><div class="label">{_esc(label)}</div>'
        f'<div class="value">{_esc(value)}</div>'
        f'<div class="delta {_esc(tone)}">{_esc(delta)}</div></div>'
    )


def _delta_badge(current: Decimal | None, prior: Decimal | None) -> str:
    delta = _change_pct(current, prior)
    if delta is None:
        return "—"
    arrow = "▲" if delta >= 0 else "▼"
    return f"{_fmt_pct_raw(abs(delta))} {arrow}"


def _delta_tone(current: Decimal | None, prior: Decimal | None) -> str:
    delta = _change_pct(current, prior)
    if delta is None:
        return ""
    return "up" if delta >= 0 else "down"


class _Facts:
    """item_id 语义取数视图（含单位换算与格式化）。"""

    def __init__(self, items: list[Any], unit_note: str = ""):
        self.statements: set[str] = set()
        self.names_by_statement: dict[str, list[str]] = {}
        self.by_id: dict[str, dict[str, Any]] = {}
        for item in items:
            self.statements.add(item.statement_type)
            self.names_by_statement.setdefault(item.statement_type, []).append(
                item.item_name
            )
            key = item.item_id or f"name:{item.statement_type}:{item.item_name}"
            slot = self.by_id.setdefault(key, {})
            slot["current"] = _dec(item.value_current)
            slot["prior"] = _dec(item.value_prior)
            slot["begin"] = _dec(item.value_begin)
            slot["end"] = _dec(item.value_end)
        text = unit_note or ""
        if "百万" in text:
            self.scale = Decimal(100)
        elif "千元" in text:
            self.scale = Decimal(100_000)
        else:
            self.scale = Decimal(100_000_000)

    def raw(self, item_id: str, column: str) -> Decimal | None:
        slot = self.by_id.get(item_id)
        return slot.get(column) if slot else None

    def fmt(self, value: Decimal | None, column: str = "") -> str:
        return _fmt_yi(value / self.scale) if value is not None else "—"


def _b64(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def _img(png: bytes, alt: str) -> str:
    """非空 PNG → 居中图表块；空字节 → 空串（图表缺失时整块隐藏）。"""
    if not png:
        return ""
    return f'<div class="chart"><img alt="{_esc(alt)}" src="{_b64(png)}"></div>'


def render_objective_report_v3(
    report: Any,
    result: Any,
    normalized_items: list[Any],
    *,
    generated_at: datetime,
) -> str:
    """渲染完整客观分析报告 v3（KPI 卡片 + matplotlib 图表 + 多章节）。"""
    facts = _Facts(normalized_items, getattr(report, "unit_note", "") or "")
    generated = generated_at.strftime("%Y-%m-%d %H:%M")

    def raw(item_id: str, column: str) -> Decimal | None:
        return facts.raw(item_id, column)

    revenue, revenue_prior = raw("is.revenue", "current"), raw("is.revenue", "prior")
    net_profit, net_profit_prior = (
        raw("is.attr_net_profit", "current") or raw("is.net_profit", "current"),
        raw("is.attr_net_profit", "prior") or raw("is.net_profit", "prior"),
    )
    cogs = raw("is.cogs", "current")
    ocf, icf, fin_cf = (
        raw("cf.ocf", "current"),
        raw("cf.icf", "current"),
        raw("cf.fin_cf", "current"),
    )
    total_assets, total_liab = raw("bs.total_assets", "end"), raw("bs.total_liab", "end")
    equity, current_assets, current_liab = (
        raw("bs.equity", "end"),
        raw("bs.current_assets", "end"),
        raw("bs.current_liab", "end"),
    )

    gross_margin = (
        _safe_div(revenue - cogs, revenue)
        if (revenue is not None and cogs is not None)
        else None
    )
    net_margin = _safe_div(net_profit, revenue)
    roe = _safe_div(net_profit, equity)
    asset_turnover = _safe_div(revenue, total_assets)
    equity_multiplier = _safe_div(total_assets, equity)
    debt_ratio = _safe_div(total_liab, total_assets)
    current_ratio = _safe_div(current_assets, current_liab)
    ocf_ratio = _safe_div(ocf, net_profit)
    revenue_yoy = _change_pct(revenue, revenue_prior)
    profit_yoy = _change_pct(net_profit, net_profit_prior)

    # ---- 图表（matplotlib → PNG base64）----
    try:
        chart_revenue = bar_compare("营业收入", revenue, revenue_prior)
    except ValueError:
        chart_revenue = b""
    try:
        chart_profit = bar_compare(
            "归母净利润", net_profit, net_profit_prior, color="#e08a3c"
        )
    except ValueError:
        chart_profit = b""
    try:
        chart_cashflow = cashflow_bars(
            ocf, icf, fin_cf, unit_note=getattr(report, "unit_note", "")
        )
    except ValueError:
        chart_cashflow = b""
    try:
        chart_dupont = dupont_chart(net_margin, asset_turnover, equity_multiplier, roe)
    except ValueError:
        chart_dupont = b""

    excluded_assets = (
        "bs.total_assets", "bs.total_liab", "bs.equity",
        "bs.current_assets", "bs.current_liab", "bs.noncurrent_liab",
        "bs.attr_equity",
    )
    asset_items = sorted(
        (
            (name[len("bs."):], slot.get("end"))
            for name, slot in facts.by_id.items()
            if name.startswith("bs.")
            and name not in excluded_assets
            and _has(slot.get("end"))
        ),
        key=lambda pair: abs(pair[1] or 0),
        reverse=True,
    )
    try:
        chart_assets = donut("资产结构（期末，占总资产）", asset_items[:6])
    except ValueError:
        chart_assets = b""
    try:
        chart_capital = donut(
            "资本结构（期末）",
            [
                ("流动负债", current_liab),
                ("非流动负债", raw("bs.noncurrent_liab", "end")),
                ("所有者权益", equity),
            ],
        )
    except ValueError:
        chart_capital = b""
    expense_bars = [
        (label, value)
        for item_id, label in (
            ("is.selling_exp", "销售费用"),
            ("is.admin_exp", "管理费用"),
            ("is.rnd_exp", "研发费用"),
            ("is.fin_exp", "财务费用"),
        )
        for value in [raw(item_id, "current")]
        if value is not None
    ]
    chart_expenses = (
        hbar_structure(
            "期间费用（本期）", expense_bars, unit_note=getattr(report, "unit_note", "")
        )
        if expense_bars
        else b""
    )

    # ---- KPI 卡片 ----
    kpis = "".join([
        _kpi_card(
            "营业收入",
            _fmt_yi(revenue / facts.scale) if revenue is not None else "—",
            _delta_badge(revenue, revenue_prior),
            _delta_tone(revenue, revenue_prior),
        ),
        _kpi_card(
            "归母净利润",
            _fmt_yi(net_profit / facts.scale) if net_profit is not None else "—",
            _delta_badge(net_profit, net_profit_prior),
            _delta_tone(net_profit, net_profit_prior),
        ),
        _kpi_card("毛利率", _fmt_pct(gross_margin)),
        _kpi_card("净利率", _fmt_pct(net_margin)),
        _kpi_card("资产负债率", _fmt_pct(debt_ratio)),
        _kpi_card("流动比率", f"{current_ratio:.2f}" if current_ratio is not None else "—"),
        _kpi_card("净现比", f"{abs(ocf_ratio):.2f}" if ocf_ratio is not None else "—"),
        _kpi_card("ROE（期末权益口径）", _fmt_pct(roe)),
    ])

    # ---- 摘要叙述（纯客观） ----
    summary_sentences: list[str] = []
    if revenue is not None:
        text = f"本期营业收入 {_fmt_yi(revenue / facts.scale)}"
        if revenue_yoy is not None:
            direction = "增" if revenue_yoy >= 0 else "减"
            text += f"，同比 {_fmt_pct_raw(abs(revenue_yoy))}（{direction}）"
        summary_sentences.append(text + "。")
    if net_profit is not None:
        text = f"归母净利润 {_fmt_yi(net_profit / facts.scale)}"
        if profit_yoy is not None:
            direction = "增" if profit_yoy >= 0 else "减"
            text += f"，同比 {_fmt_pct_raw(abs(profit_yoy))}（{direction}）"
        summary_sentences.append(text + "。")
    if ocf is not None:
        summary_sentences.append(f"经营活动现金流净额 {_fmt_yi(ocf / facts.scale)}。")
    if total_assets is not None:
        summary_sentences.append(f"期末资产总计 {_fmt_yi(total_assets / facts.scale)}。")

    # ---- 费用表 ----
    expense_rows = []
    for item_id, label in (
        ("is.cogs", "营业成本"),
        ("is.selling_exp", "销售费用"),
        ("is.admin_exp", "管理费用"),
        ("is.rnd_exp", "研发费用"),
        ("is.fin_exp", "财务费用"),
    ):
        current = raw(item_id, "current")
        prior = raw(item_id, "prior")
        if current is None and prior is None:
            continue
        share = (
            _fmt_pct(_safe_div(current, revenue))
            if (current is not None and revenue)
            else "—"
        )
        expense_rows.append(
            f"<tr><td>{_esc(label)}</td>"
            f"<td class='num'>{facts.fmt(current)}</td>"
            f"<td class='num'>{facts.fmt(prior)}</td>"
            f"<td class='num'>{share}</td>"
            f"<td class='delta {_esc(_delta_tone(current, prior))}'>"
            f"{_esc(_delta_badge(current, prior))}</td></tr>"
        )

    # ---- 引擎条目 ----
    engine_rows = []
    not_computable: list[str] = []
    for entry in result.entries:
        engine_rows.append(
            "<tr>"
            f"<td>{_esc(entry.name)}</td>"
            f"<td class='status-{_esc(entry.status.value)}'>{_esc(entry.status.value)}</td>"
            f"<td class='value'>{_esc(entry.value) if entry.value else '—'}</td>"
            f"<td>{_esc(entry.caliber_note)}"
            + (f'<div class="reason">{_esc(entry.reason)}</div>' if entry.reason else "")
            + f"<div class='refs'>{_esc('、'.join(entry.refs))}</div></td>"
            "</tr>"
        )
        if entry.status.value == "not_computable":
            not_computable.append(entry.name)

    boundary = (
        "<ul>"
        + "".join(
            f"<li>{_esc(name)}：数据不足，未计算</li>" for name in not_computable
        )
        + "</ul>"
    )

    # ---- 杜邦三因子（HTML 文本，与图表同源） ----
    dupont_rows = "".join(
        f"<tr><td>{label}</td><td class='num'>{value}</td></tr>"
        for label, value in (
            ("净利率（归母净利润 ÷ 营业收入）", _fmt_pct(net_margin)),
            ("总资产周转率（营业收入 ÷ 期末总资产）",
             f"{asset_turnover:.3f}" if asset_turnover is not None else "—"),
            ("权益乘数（期末总资产 ÷ 期末权益）",
             f"{equity_multiplier:.3f}" if equity_multiplier is not None else "—"),
            ("ROE（期末权益口径）", _fmt_pct(roe)),
        )
    )

    # ---- 附录（直接按归一化行渲染，item_id 或名称键均可，全部转义） ----
    appendix_blocks = []
    for statement in sorted({item.statement_type for item in normalized_items}):
        rows = []
        for item in normalized_items:
            if item.statement_type != statement:
                continue
            current = _dec(item.value_current)
            prior = _dec(item.value_prior)
            if current is None:
                current = _dec(item.value_end)
            if prior is None:
                prior = _dec(item.value_begin)
            delta = _change_pct(current, prior)
            delta_text = (
                f'<td class="num delta {"up" if (delta or 0) >= 0 else "down"}">'
                f"{_fmt_pct(abs(delta))}</td>"
                if delta is not None
                else "<td>—</td>"
            )
            rows.append(
                f"<tr><td>{_esc(item.item_name)}</td>"
                f"<td class='num'>"
                f"{_fmt_yi(current / facts.scale) if current is not None else '—'}</td>"
                f"<td class='num'>"
                f"{_fmt_yi(prior / facts.scale) if prior is not None else '—'}</td>"
                f"{delta_text}</tr>"
            )
        if rows:
            appendix_blocks.append(
                f"<h3>{_esc(statement)}</h3>"
                "<table><thead><tr><th>项目</th><th>本期/期末</th>"
                "<th>上年同期/期初</th><th>变动</th></tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table>"
            )
    appendix = "".join(appendix_blocks) or "<p class='muted'>（无逐行数据）</p>"

    unit = _esc(getattr(report, "unit_note", "") or "（按披露原文）")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{_esc(report.company_name)} {_esc(report.period_label)} 客观财务分析报告</title>
<style>{_PRINT_CSS}</style>
</head>
<body>
<div class="cover">
  <h1>客观财务分析报告｜{_esc(report.company_name)}</h1>
  <div class="meta">
    股票代码 {_esc(report.stock_code)} · 报告类型 {_esc(report.report_kind)} ·
    期间 {_esc(report.period_label)} · 单位 {unit}<br>
    分析目录 {_esc(result.catalog_id)} · 生成时间 {generated}（Asia/Shanghai）
  </div>
</div>

<p class="disclaimer">
本报告由 FLOW 客观财务分析引擎基于已归一化的披露事实自动计算：只包含结构、趋势、同比、
比率与可复算数学分解；每项结果携带口径与来源引用；数据不足时显式标注 not_computable；
<strong>数学贡献不代表业务因果，本报告不构成投资建议。</strong>（D049 客观财务分析）
</p>

<div class="kpi-row">{kpis}</div>

<h2>摘要</h2>
{''.join(f'<p class="summary">{_esc(s)}</p>' for s in summary_sentences)
 or '<p class="muted">关键项目缺失。</p>'}

<h2>一、盈利与现金</h2>
{_img(chart_revenue, "营业收入对比")}
{_img(chart_profit, "归母净利润对比")}
<h3>盈利比率</h3>
<table><thead><tr><th>指标</th><th>数值</th></tr></thead><tbody>
<tr><td>毛利率</td><td class="num">{_fmt_pct(gross_margin)}</td></tr>
<tr><td>净利率</td><td class="num">{_fmt_pct(net_margin)}</td></tr>
<tr><td>净现比（经营现金流÷归母净利润）</td>
<td class="num">{f'{abs(ocf_ratio):.2f}' if ocf_ratio is not None else '—'}</td></tr>
<tr><td>ROE（期末权益口径）</td><td class="num">{_fmt_pct(roe)}</td></tr>
</tbody></table>
<h3>现金流量</h3>
{_img(chart_cashflow, "现金流量净额")}
<ul>
<li>经营活动现金流净额：{_fmt_yi(ocf / facts.scale) if ocf is not None else '—'}</li>
<li>投资活动现金流净额：{_fmt_yi(icf / facts.scale) if icf is not None else '—'}</li>
<li>筹资活动现金流净额：{_fmt_yi(fin_cf / facts.scale) if fin_cf is not None else '—'}</li>
</ul>

<h2>二、成本与费用结构</h2>
{_img(chart_expenses, "期间费用与成本结构")}
<table>
<thead><tr><th>项目</th><th>本期</th><th>上年同期</th><th>占收入</th><th>变动</th></tr></thead>
<tbody>{''.join(expense_rows)}</tbody>
</table>

<h2>三、资产、资本与偿债</h2>
{_img(chart_assets, "资产结构")}
{_img(chart_capital, "资本结构")}
<ul>
<li>资产负债率（期末）：{_fmt_pct(debt_ratio)}</li>
<li>流动比率（期末）：{f'{current_ratio:.2f}'
if current_ratio is not None else '—'}</li>
</ul>

<h2>四、杜邦分解</h2>
{_img(chart_dupont, "杜邦分解")}
<table><thead><tr><th>因子</th><th>数值</th></tr></thead><tbody>
{dupont_rows}
</tbody></table>
<p class="muted">口径：期末权益与总资产（未做平均余额），与平均余额口径不可直接比较。</p>

<h2>五、客观分析引擎条目（口径化结果）</h2>
<table>
<thead><tr><th>条目</th><th>状态</th><th>值</th><th>口径说明 / 来源引用</th></tr></thead>
<tbody>{''.join(engine_rows)}</tbody>
</table>

<div class="pagebreak"></div>
<h2>六、数据边界与不可算项</h2>
{boundary}
<p class="muted">未披露的数据不做推断；上述边界以披露原文为准。</p>

<h2>附录：归一化报表逐行对比</h2>
{appendix}

<div class="footer">
生成：FLOW 客观财务分析引擎（目录 {_esc(result.catalog_id)}）· 生成时间 {generated} ·
图表由 matplotlib 渲染，数据以披露原文为准。
</div>
</body>
</html>
"""


def render_objective_report(
    report: Any,
    result: Any,
    normalized_items: list[Any],
    *,
    generated_at: datetime,
) -> str:
    """兼容入口：默认输出 v3 富报告。"""
    return render_objective_report_v3(
        report, result, normalized_items, generated_at=generated_at
    )


__all__ = ["render_objective_report", "render_objective_report_v3"]
