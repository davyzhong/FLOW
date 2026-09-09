"""经营轨六主题概览 HTML 渲染（O3）。

数据边界与 objective_renderers 相同：只消费 typed 概览（引擎已算好的
确定性结果），不重算、不补造；复用 objective 的 Chromium 打印链。
叙事按借鉴 #13 客观部分组织：现状判断 → 质量核对 → 口径与溯源；
行动章显式标注不在客观报告范围（U5 门禁，借鉴 #9）。
"""

from __future__ import annotations

from flow_api.operations.engine import OperationsOverview

_DIRECTION_LABEL = {"negative": "关注", "warning": "提示复核"}


def render_operations_html(overview: OperationsOverview) -> str:
    blocks: list[str] = []
    for theme in overview.themes:
        if theme.status == "not_applicable":
            blocks.append(
                f"<section class='theme na'><h2>{theme.name}</h2>"
                f"<p class='muted'>待内部数据（{theme.reason}）——"
                "披露缺失与内部数据缺口如实标注，不推测填补。</p></section>"
            )
            continue
        rows = []
        for metric in theme.metrics:
            if metric.status == "computed":
                caliber = (
                    f"<div class='caliber'>口径：{metric.caliber_note}</div>"
                    if metric.caliber_note
                    else ""
                )
                rows.append(
                    f"<tr><td>{metric.name}</td>"
                    f"<td class='num'>{metric.value}</td>"
                    f"<td>{metric.basis or '—'}{caliber}</td></tr>"
                )
            else:
                rows.append(
                    f"<tr><td>{metric.name}</td>"
                    f"<td class='muted'>暂不可算（{metric.reason}）</td>"
                    f"<td class='muted'>缺失不补造</td></tr>"
                )
        blocks.append(
            f"<section class='theme'><h2>{theme.name}</h2>"
            f"<table><tr><th>指标</th><th>值</th><th>比较基准与口径</th></tr>"
            f"{''.join(rows)}</table></section>"
        )

    watch_items = "".join(
        f"<li data-direction='{item['direction']}'>"
        f"<span class='tag'>{_DIRECTION_LABEL.get(item['direction'], item['direction'])}</span>"
        f"{item['message']}</li>"
        for item in overview.management_watch
    )
    watch_block = (
        f"<h2>管理关注（≤3 条，提示复核）</h2><ul class='watch'>{watch_items}</ul>"
        if overview.management_watch
        else "<h2>管理关注</h2><p class='muted'>本期无确定性提示信号。</p>"
    )

    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<title>经营分析概览</title>"
        "<style>body{font-family:'PingFang SC',sans-serif;margin:32px;color:#1e293b}"
        "table{border-collapse:collapse;width:100%;margin:12px 0}"
        "td,th{border-bottom:1px solid #eee;padding:6px 10px;text-align:left}"
        "th{color:#475569;font-weight:600}"
        ".num{text-align:right;font-variant-numeric:tabular-nums}"
        "h1{font-size:22px}h2{font-size:16px;margin-top:24px}"
        ".muted{color:#64748b;font-size:13px}"
        ".caliber{color:#64748b;font-size:12px}"
        ".watch{list-style:none;padding:0;display:flex;flex-direction:column;gap:8px}"
        ".watch li{border:1px solid #e2e8f0;border-left-width:4px;border-radius:6px;"
        "padding:8px 12px;font-size:14px}"
        ".watch li[data-direction='warning']{border-left-color:#d97706}"
        ".watch li[data-direction='negative']{border-left-color:#b91c1c}"
        ".tag{display:inline-block;margin-right:8px;font-size:12px;font-weight:600;"
        "color:#475569}"
        ".scope{border:1px solid #cbd5e1;border-radius:6px;padding:10px 14px;"
        "color:#475569;font-size:13px;margin-top:24px}</style></head><body>"
        "<h1>经营分析概览</h1>"
        f"<div class='muted'>目录：{overview.catalog_id}（L1 结果层，"
        "数据可得性分层见 D050）</div>"
        + "".join(blocks)
        + watch_block
        + "<div class='scope'><strong>范围说明：</strong>本报告只承载客观事实与"
        "可复算的确定性信号；原因推断与<b>行动</b>建议<b>不在客观报告范围</b>"
        "（主观内容需证据门槛，见 U5 门禁）。</div>"
        "</body></html>"
    )


__all__ = ["render_operations_html"]
