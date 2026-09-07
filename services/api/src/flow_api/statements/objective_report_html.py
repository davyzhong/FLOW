# -*- coding: utf-8 -*-
"""客观财务分析报告的打印友好 HTML 渲染器（P08 真实 PDF 的格式基线）。

设计目标：一份 HTML 即是一份完整可打印报告——A4 打印 CSS、封面身份块、
逐条目 值/口径/来源引用、not_computable 显式原因、D049 客观性声明。
所有动态值经 html.escape 转义。
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any

_KIND_ORDER = ("structure", "capital", "trend", "yoy", "ratio", "dupont")
_KIND_LABELS = {
    "structure": "财务结构",
    "capital": "资本结构",
    "trend": "趋势变动",
    "yoy": "同比",
    "ratio": "比率",
    "dupont": "杜邦分解",
}

_PRINT_CSS = """
  @page { size: A4; margin: 18mm 16mm; }
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
         "Noto Sans CJK SC", sans-serif; color: #1a2233; font-size: 11pt;
         line-height: 1.55; margin: 0; background: #ffffff; }
  .cover { border-bottom: 2px solid #1d4ed8; padding-bottom: 12px; margin-bottom: 18px; }
  .cover h1 { font-size: 20pt; margin: 0 0 6px; }
  .cover .meta { color: #475069; font-size: 9.5pt; }
  .disclaimer { background: #f4f6fb; border-left: 4px solid #1d4ed8;
                padding: 8px 12px; font-size: 9pt; color: #37415c; margin: 0 0 18px; }
  h2 { font-size: 13pt; border-left: 4px solid #1d4ed8; padding-left: 8px;
       margin: 22px 0 8px; page-break-after: avoid; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0 14px;
          page-break-inside: avoid; }
  th, td { border: 1px solid #d5dae3; padding: 5px 8px; text-align: left;
           vertical-align: top; font-size: 9.5pt; }
  th { background: #eef2fb; font-weight: 600; }
  td { background: #ffffff; }
  td.value { font-family: "JetBrains Mono", Menlo, monospace; white-space: nowrap; }
  .status-computed { color: #1a7f37; font-weight: 600; }
  .status-not_computable, .status-not_applicable { color: #9a6700; font-weight: 600; }
  .reason { color: #9a6700; font-size: 9pt; }
  .refs { color: #5b6478; font-size: 8.5pt; font-family: "JetBrains Mono", Menlo, monospace; }
  .footer { margin-top: 24px; padding-top: 8px; border-top: 1px solid #d5dae3;
            color: #6b7280; font-size: 8.5pt; }
"""


def render_objective_html(
    report: Any,
    result: Any,
    *,
    generated_at: datetime,
) -> str:
    """把客观分析结果渲染为可独立打印的 HTML 报告。

    report：具备 company_name/stock_code/report_kind/period_label/unit_note 属性；
    result：ObjectiveAnalysisResult（entries 携带值、口径、来源引用与状态）。
    generated_at 由调用方固定传入（可复现）。
    """
    esc = html.escape
    generated = generated_at.strftime("%Y-%m-%d %H:%M")
    unit = esc(getattr(report, "unit_note", "") or "")

    groups: dict[str, list[Any]] = {}
    for entry in result.entries:
        groups.setdefault(entry.kind, []).append(entry)
    ordered_kinds = [k for k in _KIND_ORDER if k in groups] + [
        k for k in groups if k not in _KIND_ORDER
    ]

    rows: list[str] = []
    for kind in ordered_kinds:
        label = _KIND_LABELS.get(kind, esc(kind))
        rows.append(f"<h2>{esc(label)}</h2>")
        rows.append("<table><thead><tr><th>指标</th><th>状态</th><th>值</th>"
                    "<th>比较基准</th><th>口径说明</th><th>来源引用</th></tr></thead><tbody>")
        for entry in groups[kind]:
            reason = (
                f'<div class="reason">原因：{esc(entry.reason)}</div>'
                if entry.reason
                else ""
            )
            parts = ""
            if entry.parts:
                cells = "".join(
                    f"<td class='value'>{esc(part.get('label', ''))} "
                    f"{esc(part.get('value', ''))}</td>"
                    for part in entry.parts
                )
                parts = f"<tr><td colspan='6'>分解：{cells}</td></tr>"
            rows.append(
                "<tr>"
                f"<td>{esc(entry.name)}</td>"
                f"<td class='status-{esc(entry.status.value)}'>{esc(entry.status.value)}</td>"
                f"<td class='value'>{esc(entry.value) if entry.value else '—'}</td>"
                f"<td>{esc(entry.basis)}</td>"
                f"<td>{esc(entry.caliber_note)}{reason}</td>"
                f"<td class='refs'>{esc('、'.join(entry.refs))}</td>"
                "</tr>"
            )
            if parts:
                rows.append(parts)
        rows.append("</tbody></table>")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{esc(report.company_name)} {esc(report.period_label)} 客观财务分析</title>
<style>{_PRINT_CSS}</style>
</head>
<body>
<div class="cover">
  <h1>客观财务分析报告｜{esc(report.company_name)}</h1>
  <div class="meta">
    股票代码 {esc(report.stock_code)} · 报告类型 {esc(report.report_kind)} ·
    期间 {esc(report.period_label)} · 单位 {unit or '（按披露原文）'}<br>
    分析目录 {esc(result.catalog_id)} · 生成时间 {generated}（Asia/Shanghai）
  </div>
</div>

<p class="disclaimer">
本报告由 FLOW 客观财务分析引擎基于已归一化的披露事实自动计算，仅包含结构、趋势、同比、
比率与可复算数学分解；每条结果携带口径与来源引用，数据不足时显式标注 not_computable。
<strong>数学贡献不代表业务因果，本报告不构成投资建议。</strong>（D049 客观财务分析）
</p>

{''.join(rows)}

<div class="footer">
生成：FLOW 客观财务分析引擎（目录 {esc(result.catalog_id)}）· 生成时间 {generated} ·
来源以各条目"来源引用"与原文 PDF 为准。
</div>
</body>
</html>
"""
