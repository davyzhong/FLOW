# -*- coding: utf-8 -*-
"""客观财务分析报告渲染器 v2：完整报告（对比、结构图、杜邦、逐行附录）。

数据源：normalize_report 产出的 StatementNormalizedItem（本期/上年同期/期初期末）+
客观分析引擎条目（结构/趋势/同比/比率/杜邦的口径化结果）。报告结构参照受治理月报的
"结论先行 + 主题章节 + 数据边界 + 逐行附录"，全部为客观陈述，不生成业务因果。
所有动态值 html.escape；数值格式化（万亿/亿/万 + 百分比）集中在本模块。
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_PRINT_CSS = """
  @page { size: A4; margin: 16mm 14mm; }
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
         "Noto Sans CJK SC", sans-serif; color: #1a2233; font-size: 10.5pt;
         line-height: 1.5; margin: 0; background: #ffffff; }
  .cover { border-bottom: 2.5px solid #14337a; padding-bottom: 14px; margin-bottom: 16px; }
  .cover h1 { font-size: 21pt; margin: 0 0 8px; color: #14337a; }
  .cover .meta { color: #475069; font-size: 9.5pt; line-height: 1.7; }
  .disclaimer { background: #f0f4fc; border-left: 4px solid #14337a;
                padding: 8px 12px; font-size: 8.8pt; color: #37415c;
                margin: 0 0 16px; }
  h2 { font-size: 13.5pt; color: #14337a; border-left: 5px solid #14337a;
       padding-left: 9px; margin: 24px 0 10px; page-break-after: avoid; }
  h3 { font-size: 11.5pt; margin: 14px 0 6px; page-break-after: avoid; }
  p.summary { font-size: 10.5pt; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0 14px; }
  th, td { border: 1px solid #ccd3e0; padding: 4px 8px; text-align: left;
           vertical-align: top; font-size: 9pt; }
  th { background: #e9eef9; font-weight: 600; }
  tr { page-break-inside: avoid; }
  td.num { text-align: right; font-family: "JetBrains Mono", Menlo, monospace;
           white-space: nowrap; }
  td.up { color: #a1260d; }  td.down { color: #0a7f3f; }
  .bar-row { display: flex; align-items: center; margin: 3px 0;
             page-break-inside: avoid; }
  .bar-label { width: 190px; font-size: 8.8pt; text-align: right;
               padding-right: 8px; color: #37415c; }
  .bar-track { flex: 1; background: #edf1f8; height: 13px; position: relative; }
  .bar-fill { height: 100%; background: #2f6bd8; }
  .bar-fill.prior { background: #9db6e8; }
  .bar-value { width: 200px; font-size: 8.6pt; padding-left: 8px;
               font-family: "JetBrains Mono", Menlo, monospace; }
  .dupont { border: 1px solid #ccd3e0; padding: 10px 12px; margin: 8px 0 14px;
            page-break-inside: avoid; }
  .dupont .factor { margin: 4px 0; font-size: 10pt; }
  .dupont .factor b { color: #14337a; }
  .reason { color: #9a6700; font-size: 8.8pt; }
  .refs { color: #6b7280; font-size: 8pt; font-family: "JetBrains Mono", Menlo, monospace; }
  .muted { color: #6b7280; }
  .footer { margin-top: 26px; padding-top: 8px; border-top: 1px solid #ccd3e0;
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


def _fmt_amount(value: Any) -> str:
    d = _dec(value)
    if d is None:
        return "—"
    negative = d < 0
    d = abs(d)
    for divisor, unit in ((Decimal(1_000_000_000), "亿"), (Decimal(10_000), "万")):
        if d >= divisor:
            text = f"{d / divisor:,.2f} {unit}"
            break
    else:
        text = f"{d:,.0f}"
    return ("-" + text) if negative else text


def _fmt_pct(ratio: Decimal | None, digits: int = 2) -> str:
    if ratio is None:
        return "—"
    return f"{ratio * 100:.{digits}f}%"


def _safe_div(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator in (None, Decimal(0)):
        return None
    return numerator / denominator


def _change_pct(current: Decimal | None, prior: Decimal | None) -> Decimal | None:
    if current is None or prior in (None, Decimal(0)):
        return None
    return (current - prior) / abs(prior)


class _Facts:
    """按 item_id 语义键取数的归一化事实视图。

    利润表/现金流量表：本期 = value_current，上年同期 = value_prior；
    资产负债表：期末 = value_end，期初 = value_begin。
    金额单位按报告 unit_note（千元/百万元/元）换算为"亿"展示。
    """

    def __init__(self, items: list[Any], unit_note: str = ""):
        self.statements: set[str] = set()
        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_name: dict[str, dict[str, Any]] = {}
        self.names_by_statement: dict[str, list[str]] = {}
        for item in items:
            self.statements.add(item.statement_type)
            self.by_name.setdefault(item.statement_type, []).append(item.item_name)
            slot = self.by_id.setdefault(item.item_id or f"name:{item.item_name}", {})
            slot["current"] = _dec(item.value_current)
            slot["prior"] = _dec(item.value_prior)
            slot["begin"] = _dec(item.value_begin)
            slot["end"] = _dec(item.value_end)
            slot["statement_type"] = item.statement_type
            self.names_by_statement.setdefault(item.statement_type, []).append(
                item.item_name
            )
        self.unit_scale = self._unit_scale(unit_note)

    @staticmethod
    def _unit_scale(unit_note: str) -> Decimal:
        text = unit_note or ""
        if "百万" in text:
            return Decimal(100)        # 百万元 → 亿
        if "千元" in text or " thousand" in text:
            return Decimal(100_000)    # 千元 → 亿
        return Decimal(100_000_000)    # 元 → 亿

    def amount(self, item_id: str, column: str) -> Decimal | None:
        slot = self.by_id.get(item_id)
        return slot.get(column) if slot else None

    def fmt(self, item_id: str, column: str) -> str:
        value = self.amount(item_id, column)
        return "—" if value is None else _fmt_scaled(value, self.unit_scale)

    def scaled(self, item_id: str, column: str) -> Decimal | None:
        value = self.amount(item_id, column)
        if value is None:
            return None
        return value / self.unit_scale  # 换算为"亿"


def _fmt_scaled(value_scaled_yi: Decimal) -> str:
    """把已换算为"亿"的金额格式化（负数带 -，绝对值小于 0.005 亿显示万元）。"""
    negative = value_scaled_yi < 0
    d = abs(value_scaled_yi)
    if d >= Decimal("0.01"):
        text = f"{d:,.2f} 亿"
    else:
        text = f"{d * 10000:,.0f} 万"
    return ("-" + text) if negative else text


def _fmt_amount_raw(value: Any) -> str:
    d = _dec(value)
    if d is None:
        return "—"
    return f"{d:,.0f}"


def render_objective_report_v2(
    report: Any,
    result: Any,
    normalized_items: list[Any],
    *,
    generated_at: datetime,
) -> str:
    """渲染完整客观分析报告 v2。

    结构：封面 → 结论摘要 → 盈利与现金 → 资产与资本结构（含偿债）→ 杜邦分解 →
    客观引擎条目（口径化）→ 数据边界与不可算 → 附录（逐行对比）→ 页脚。
    """
    generated = generated_at.strftime("%Y-%m-%d %H:%M")
    facts = _Facts(normalized_items)

    summary_parts = []
    for key, label in (("revenue", "营业收入"), ("net_profit_attr", "净利润"),
                       ("ocf", "经营现金流净额"), ("total_assets", "资产总计")):
        slot = facts.get(key)
        if slot and _has(slot.get("current")):
            change = _change_pct(slot.get("current"), slot.get("prior"))
            summary_parts.append(
                f"{label} {_fmt_amount(slot.get('current'))}"
                + (f"（同比 {_fmt_pct(abs(change))}）" if change is not None else "")
            )
    summary_text = "；".join(summary_parts) or "—"

    ocf = facts.value("ocf", "current")
    net_profit = facts.value("net_profit_attr", "current")
    ocf_lines: list[str] = []
    if _has(ocf):
        ocf_lines.append(f"<li>经营活动现金流净额：{_fmt_amount(ocf)}</li>")
    if _has(net_profit) and _has(ocf):
        ratio = _safe_div(ocf, net_profit)
        if ratio is not None:
            direction = "高于" if ratio >= 1 else "低于"
            ocf_lines.append(
                f"<li>净现比（经营现金流 ÷ 归母净利润）：{_fmt_pct(abs(ratio))}，"
                f"{direction} 1 倍</li>"
            )
    debt_ratio = _safe_div(facts.value("total_liab", "current"),
                           facts.value("total_assets", "current"))
    current_ratio = _safe_div(facts.value("current_assets", "current"),
                              facts.value("current_liab", "current"))
    solvency_lines = []
    if debt_ratio is not None:
        solvency_lines.append(f"<li>资产负债率（期末）：{_fmt_pct(debt_ratio)}</li>")
    if current_ratio is not None:
        solvency_lines.append(f"<li>流动比率（期末）：{current_ratio:.2f}</li>")

    chapter_profit = (
        _cmp_bar("营业收入", facts.value("revenue", "current"),
                 facts.value("revenue", "prior"))
        + _cmp_bar("归母净利润", net_profit, facts.value("net_profit_attr", "prior"))
        + _expense_structure_chart(facts, facts.value("revenue", "current"))
    )
    chapter_balance = (
        _cmp_bar("资产总计", facts.value("total_assets", "current"),
                 facts.value("total_assets", "prior"))
        + _dupont_section(facts)
    )

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
        + "".join(f"<li>{_esc(name)}：数据不足，未计算</li>" for name in not_computable)
        + "".join(
            f"<li>{_esc(name)}：该报告未披露对应数据，相关分析不适用</li>"
            for name in ("资产负债表", "现金流量表")
            if name not in facts.statements
        )
        + "</ul>"
    )

    statement_order = [
        s for s in ("合并利润表", "合并资产负债表", "合并现金流量表",
                    "合并利润表（IFRS）", "综合损益表", "综合财务状况表")
        if s in facts.statements
    ]
    appendix = _appendix(facts, statement_order) or "<p class='muted'>（无逐行数据）</p>"

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

<h2>摘要</h2>
<p class="summary">{_esc(summary_text)}。</p>

<h2>一、盈利与现金</h2>
{chapter_profit}
<ul>{''.join(f'<li>{_esc(line)}</li>' for line in ocf_lines)}</ul>

<h2>二、资产、资本与偿债</h2>
{chapter_balance}
<ul>{''.join(f'<li>{_esc(line)}</li>' for line in solvency_lines)}</ul>

<h2>三、客观分析引擎条目（口径化结果）</h2>
<table>
<thead><tr><th>条目</th><th>状态</th><th>值</th><th>口径说明 / 来源引用</th></tr></thead>
<tbody>{''.join(engine_rows)}</tbody>
</table>

<div class="pagebreak"></div>
<h2>四、数据边界与不可算项</h2>
{boundary}
<p class="muted">未披露的数据不做推断；上述边界以披露原文为准。</p>

<h2>附录：归一化报表逐行对比</h2>
{appendix}

<div class="footer">
生成：FLOW 客观财务分析引擎（目录 {_esc(result.catalog_id)}）· 生成时间 {generated} ·
报告内容为客观计算结果，引用数据以披露原文为准。
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
    """兼容入口：默认输出 v2 完整报告。"""
    return render_objective_report_v2(
        report, result, normalized_items, generated_at=generated_at
    )


__all__ = ["render_objective_report", "render_objective_report_v2"]
