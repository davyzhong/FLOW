"""把 P5 抽取的财报 YAML 载荷写入 statement_report / statement_line_item。

按 (stock_code, period_label, report_kind) 幂等：同身份重导入保留报表 id、
整体重建行项目。数值存披露原文的原始值，不换算单位。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport

# 披露原文列名 → 数值列。
COLUMN_ALIASES: dict[str, str] = {
    "期末余额": "value_end",
    "期初余额": "value_begin",
    "本期发生额": "value_current",
    "上期发生额": "value_prior",
    "本期金额": "value_current",
    "上期金额": "value_prior",
}

RESERVED_KEYS = {"item"}


class StatementImportError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _to_decimal(raw: Any, *, statement_type: str, item: str, column: str) -> Decimal:
    try:
        return Decimal(str(raw).replace(",", "").strip())
    except (InvalidOperation, AttributeError) as error:
        raise StatementImportError(
            "invalid_statement_value",
            f"{statement_type} 行「{item}」列「{column}」的值不是可用数字：{raw!r}",
        ) from error


def import_statement_report(
    session: Session,
    *,
    company_name: str,
    stock_code: str,
    report_kind: str,
    period_label: str,
    payload: dict[str, Any],
    source_ref: str,
    source_sha256: str | None = None,
) -> StatementReport:
    """按唯一身份幂等导入一份抽取财报；返回含行项目的 ORM 对象。"""

    if not all((company_name, stock_code, report_kind, period_label)):
        raise StatementImportError(
            "missing_report_identity",
            "company_name / stock_code / report_kind / period_label 均不能为空",
        )
    unit_note = payload.get("unit")
    statements = payload.get("statements")
    if not isinstance(unit_note, str) or not unit_note:
        raise StatementImportError("missing_unit", "payload 缺少 unit（披露单位说明）")
    if not isinstance(statements, dict) or not statements:
        raise StatementImportError("missing_statements", "payload 缺少 statements 或为空")

    report = session.scalar(
        select(StatementReport).where(
            StatementReport.stock_code == stock_code,
            StatementReport.period_label == period_label,
            StatementReport.report_kind == report_kind,
        )
    )
    if report is None:
        report = StatementReport(
            company_name=company_name,
            stock_code=stock_code,
            report_kind=report_kind,
            period_label=period_label,
        )
        session.add(report)
    report.unit_note = unit_note
    report.source_ref = source_ref
    report.source_sha256 = source_sha256

    # 同身份整体重建行项目，保证重导入幂等且不留旧行。
    for existing in report.items:
        session.delete(existing)
    report.items = []

    for statement_type, rows in statements.items():
        if not isinstance(rows, list):
            raise StatementImportError(
                "invalid_statements_payload", f"statements.{statement_type} 必须是行项目列表"
            )
        for sort_order, row in enumerate(rows):
            if not isinstance(row, dict) or "item" not in row:
                raise StatementImportError(
                    "invalid_statement_row", f"statements.{statement_type}[{sort_order}] 缺少 item"
                )
            item_name = str(row["item"]).strip()
            values: dict[str, Decimal] = {}
            for key, raw in row.items():
                if key in RESERVED_KEYS:
                    continue
                column = COLUMN_ALIASES.get(str(key))
                if column is None:
                    raise StatementImportError(
                        "unknown_statement_column",
                        f"statements.{statement_type} 行「{item_name}」出现未知列「{key}」",
                    )
                if raw is None:
                    continue
                values[column] = _to_decimal(
                    raw, statement_type=statement_type, item=item_name, column=str(key)
                )
            report.items.append(
                StatementLineItem(
                    statement_type=str(statement_type),
                    item_name=item_name,
                    sort_order=sort_order,
                    value_end=values.get("value_end"),
                    value_begin=values.get("value_begin"),
                    value_current=values.get("value_current"),
                    value_prior=values.get("value_prior"),
                )
            )
    session.flush()
    return report
