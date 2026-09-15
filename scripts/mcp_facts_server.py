#!/usr/bin/env python3
"""T10-B5：事实库只读 MCP server（stdio, JSON-RPC 2.0, 标准库实现）。

三个只读工具（无写入/发布/授权面）：
- get_facts(stock_code, period_label)：报告元数据 + 三表行项目（含页锚溯源）；
- get_metric(metric_code)：指标字典定义与公式；
- get_provenance(stock_code, period_label, item)：行项目的 PDF 页锚定位。

治理（B5 验收合同）：
- 只读：全部工具仅 SELECT；连接使用只读意图（应用角色无写权限由 DB 侧保证
  的部署前提写入 README，本进程不执行任何 DML）；
- 身份：启动要求 FLOW_MCP_TOKEN 环境变量（≥16 字符）；MCP 客户端初始化时
  必须以 `authorization` 字段回传同值，否则拒绝服务（fail-closed）；
- 每次工具调用在 stderr 打结构化审计行（工具/参数摘要/耗时/结果规模）。

协议：每行一个 JSON-RPC 2.0 消息（newline-delimited）；支持 initialize、
tools/list、tools/call；未知方法回 -32601。
"""

from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "services/api" / "src"))

SERVER_INFO = {"name": "flow-facts-mcp", "version": "1.0.0"}
PROTOCOL_VERSION = "2024-11-05"


def _decimal_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError


def _tool_get_facts(stock_code: str, period_label: str) -> dict:
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import (
        StatementLineItem,
        StatementReport,
    )

    with get_engine().connect() as conn:
        report = conn.execute(
            select(StatementReport).where(
                StatementReport.stock_code == stock_code,
                StatementReport.period_label == period_label,
            )
        ).first()
        if report is None:
            return {"error": "report_not_found"}
        items = conn.execute(
            select(
                StatementLineItem.statement_type,
                StatementLineItem.item_name,
                StatementLineItem.sort_order,
                StatementLineItem.value_end,
                StatementLineItem.value_begin,
                StatementLineItem.value_current,
                StatementLineItem.value_prior,
                StatementLineItem.page_number,
                StatementLineItem.page_anchor,
            )
            .where(StatementLineItem.report_id == report.id)
            .order_by(StatementLineItem.statement_type, StatementLineItem.sort_order)
        ).all()
    return {
        "company_name": report.company_name,
        "stock_code": report.stock_code,
        "period_label": report.period_label,
        "report_kind": report.report_kind,
        "version": report.version,
        "unit_note": report.unit_note,
        "source_ref": report.source_ref,
        "items": [
            {
                "statement_type": r[0],
                "item": r[1],
                "sort_order": r[2],
                "value_end": r[3],
                "value_begin": r[4],
                "value_current": r[5],
                "value_prior": r[6],
                "provenance": {"page": r[7], "anchor": r[8]},
            }
            for r in items
        ],
    }


def _tool_get_metric(metric_code: str) -> dict:
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.metric_library import MetricDictionaryEntry

    with get_engine().connect() as conn:
        rows = conn.execute(
            select(
                MetricDictionaryEntry.metric_code,
                MetricDictionaryEntry.name,
                MetricDictionaryEntry.definition,
                MetricDictionaryEntry.formula_text,
                MetricDictionaryEntry.unit,
                MetricDictionaryEntry.status,
                MetricDictionaryEntry.version,
            ).where(MetricDictionaryEntry.metric_code == metric_code)
        ).all()
    return {
        "metric_code": metric_code,
        "versions": [
            {
                "name": r[1],
                "definition": r[2],
                "formula_text": r[3],
                "unit": r[4],
                "status": r[5],
                "version": r[6],
            }
            for r in rows
        ],
    }


def _tool_get_provenance(stock_code: str, period_label: str, item: str) -> dict:
    from sqlalchemy import select

    from flow_api.infrastructure.db import get_engine
    from flow_api.infrastructure.models.statement import (
        StatementLineItem,
        StatementReport,
    )

    with get_engine().connect() as conn:
        report = conn.execute(
            select(StatementReport).where(
                StatementReport.stock_code == stock_code,
                StatementReport.period_label == period_label,
            )
        ).first()
        if report is None:
            return {"error": "report_not_found"}
        rows = conn.execute(
            select(
                StatementLineItem.statement_type,
                StatementLineItem.item_name,
                StatementLineItem.value_end,
                StatementLineItem.value_begin,
                StatementLineItem.value_current,
                StatementLineItem.value_prior,
                StatementLineItem.page_number,
                StatementLineItem.page_anchor,
            ).where(
                StatementLineItem.report_id == report.id,
                StatementLineItem.item_name.contains(item),
            )
        ).all()
    return {
        "source_ref": report.source_ref,
        "matches": [
            {
                "statement_type": r[0],
                "item": r[1],
                "values": {
                    "end": r[2],
                    "begin": r[3],
                    "current": r[4],
                    "prior": r[5],
                },
                "page": r[6],
                "anchor": r[7],
            }
            for r in rows
        ],
    }


TOOLS = [
    {
        "name": "get_facts",
        "description": "按公司代码与期间返回报告元数据与三表行项目（含页锚溯源）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_code": {"type": "string"},
                "period_label": {"type": "string"},
            },
            "required": ["stock_code", "period_label"],
        },
    },
    {
        "name": "get_metric",
        "description": "按指标代码返回指标字典定义（名称/口径/公式/单位/状态）",
        "inputSchema": {
            "type": "object",
            "properties": {"metric_code": {"type": "string"}},
            "required": ["metric_code"],
        },
    },
    {
        "name": "get_provenance",
        "description": "按公司、期间与行名（包含匹配）返回 PDF 页码溯源",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_code": {"type": "string"},
                "period_label": {"type": "string"},
                "item": {"type": "string"},
            },
            "required": ["stock_code", "period_label", "item"],
        },
    },
]

_TOOL_HANDLERS = {
    "get_facts": _tool_get_facts,
    "get_metric": _tool_get_metric,
    "get_provenance": _tool_get_provenance,
}


def audit(line: str) -> None:
    print(line, file=sys.stderr, flush=True)


def handle(request: dict) -> dict | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        token = (request.get("params") or {}).get("authorization")
        expected = os.environ.get("FLOW_MCP_TOKEN", "")
        if not expected or token != expected:
            audit(json.dumps({"event": "mcp.auth_rejected"}))
            return {
                "id": request_id,
                "error": {"code": -32001, "message": "unauthorized"},
            }
        return {
            "id": request_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        handler = _TOOL_HANDLERS.get(name)
        if handler is None:
            return {
                "id": request_id,
                "error": {"code": -32602, "message": f"unknown tool {name}"},
            }
        started = time.monotonic()
        arguments = params.get("arguments") or {}
        try:
            result = handler(**arguments)
        except TypeError as error:
            return {"id": request_id, "error": {"code": -32602, "message": str(error)}}
        duration_ms = int((time.monotonic() - started) * 1000)
        audit(
            json.dumps(
                {
                    "event": "mcp.tool_call",
                    "tool": name,
                    "args_keys": sorted(arguments),
                    "duration_ms": duration_ms,
                    "result_bytes": len(json.dumps(result, default=_decimal_default)),
                },
                ensure_ascii=False,
            )
        )
        return {
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, default=_decimal_default),
                    }
                ]
            },
        }
    if request_id is not None:
        return {"id": request_id, "error": {"code": -32601, "message": "method not found"}}
    return None


def main() -> int:
    if not os.environ.get("FLOW_MCP_TOKEN"):
        print("ERROR FLOW_MCP_TOKEN 未配置（fail-closed）", file=sys.stderr)
        return 2
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, default=_decimal_default), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
