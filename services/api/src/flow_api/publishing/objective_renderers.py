"""从冻结载荷（objective.v1）渲染 HTML / XLSX 报告。

数据边界：渲染只消费冻结 payload（不可变），任何数值都是载荷原值的
格式化投影；不重算、不补造（D043/D049）。PDF 复用既有 Chromium 打印链。
"""

from __future__ import annotations

import io
from typing import Any, cast

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

_GOLDEN_SCALE_NOTE = "单位以 unit_note 为准，数值为披露原值的字符串投影"


def _source_lines(payload: dict[str, Any]) -> list[str]:
    source = payload.get("source", {})
    return [
        f"公司：{source.get('company_name', '')}（{source.get('stock_code', '')}）",
        f"期间：{source.get('period_label', '')} {source.get('report_kind', '')}",
        f"来源：{source.get('source_ref', '')}",
        f"单位：{source.get('unit_note', '')}",
    ]


def _statements(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return cast(dict[str, list[dict[str, Any]]], payload.get("statements", {}))


def render_html_from_payload(payload: dict[str, Any]) -> str:
    """极简 HTML：四表逐行原值 + 来源身份头。用于快照预览与打印输入。"""

    blocks = []
    for statement_type, rows in _statements(payload).items():
        row_html = "".join(
            f"<tr><td>{row['item']}</td><td class='num'>{row.get('value_current') or ''}</td>"
            f"<td class='num'>{row.get('value_prior') or ''}</td></tr>"
            for row in rows
        )
        blocks.append(f"<h2>{statement_type}</h2><table>{row_html}</table>")
    frozen_at = payload.get("frozen_at", "")
    src_block = "".join(
        f"<div>{line}</div>" for line in _source_lines(payload)
    )
    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<title>客观财报分析报告</title>"
        "<style>body{font-family:'PingFang SC',sans-serif;margin:32px;color:#1e293b}"
        "table{border-collapse:collapse;width:100%;margin:12px 0}"
        "td{border-bottom:1px solid #eee;padding:6px 10px}"
        ".num{text-align:right;font-variant-numeric:tabular-nums}"
        "h1{font-size:22px}h2{font-size:16px;margin-top:24px}"
        ".src{color:#64748b;font-size:13px;margin-bottom:18px}</style></head><body>"
        "<h1>客观财报分析报告</h1>"
        f"<div class='src'>{src_block}冻结时间：{frozen_at}</div>"
        f"{''.join(blocks)}</body></html>"
    )


def render_xlsx_bytes_from_payload(payload: dict[str, Any]) -> bytes:
    """XLSX：口径与证据页 + 各报表逐行原值（金额列右对齐）。"""

    wb = Workbook()
    evidence = cast(Worksheet, wb.active)
    evidence.title = "口径与证据"
    evidence["A1"] = "FLOW 客观财报分析（冻结载荷投影）"
    evidence["A1"].font = Font(bold=True)
    for idx, line in enumerate(_source_lines(payload), start=3):
        evidence[f"A{idx}"] = line
    evidence[f"A{len(_source_lines(payload)) + 4}"] = (
        f"冻结时间：{payload.get('frozen_at', '')}"
    )
    note_row = len(_source_lines(payload)) + 6
    evidence[f"A{note_row}"] = _GOLDEN_SCALE_NOTE

    for statement_type, rows in _statements(payload).items():
        ws = wb.create_sheet(statement_type[:28])
        ws.append(["项目", "期末/本期", "期初/上期"])
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in rows:
            ws.append([row["item"], row.get("value_current"), row.get("value_prior")])
        for column, width in (("A", 42), ("B", 20), ("C", 20)):
            ws.column_dimensions[column].width = width
        for data_row in ws.iter_rows(min_row=2):
            for cell in data_row[1:]:
                cell.alignment = Alignment(horizontal="right")

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
