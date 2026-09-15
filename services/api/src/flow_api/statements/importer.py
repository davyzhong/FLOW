"""把 P5 抽取的财报 YAML 载荷写入 statement_report / statement_line_item。

版本规则（B03）：同一 (stock_code, period_label, report_kind) 身份下——
内容哈希相同则幂等重建行项目（报表 id 不变）；内容不同视为重述，
递增 version 新建报表行，旧版及其行项目完整保留。
数值存披露原文的原始值，不换算单位。
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import UUID

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


def _content_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _to_decimal(raw: Any, *, statement_type: str, item: str, column: str) -> Decimal:
    try:
        return Decimal(str(raw).replace(",", "").strip())
    except (InvalidOperation, AttributeError) as error:
        raise StatementImportError(
            "invalid_statement_value",
            f"{statement_type} 行「{item}」列「{column}」的值不是可用数字：{raw!r}",
        ) from error


def load_provenance_index(
    answer_set_path: Path,
) -> dict[tuple[str, str, str, str], set[tuple[Decimal, int, str]]]:
    """T09-L1 答案集 → 溯源索引：(statement, item, column) → {(value, page, anchor)}。

    调用方按报告身份（stock_code/period_label/report_kind）分桶；值相等才
    认领页锚——同名行（流动/非流动借款）靠值区分。
    """
    import yaml

    payload = yaml.safe_load(Path(answer_set_path).read_text(encoding="utf-8"))
    index: dict[tuple[str, str, str, str], set[tuple[Decimal, int, str]]] = {}
    for entry in payload.get("entries", []):
        normalized_column = COLUMN_ALIASES.get(entry["column"], entry["column"])
        key = (entry["statement"], entry["item"], normalized_column, entry["stock_code"])
        index.setdefault(key, set()).add(
            (Decimal(str(entry["value"])), int(entry["page"]), str(entry.get("match_mode", "weak")))
        )
    return index


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
    provenance_index: dict[tuple[str, str, str, str], set[tuple[Decimal, int, str]]] | None = None,
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
        select(StatementReport)
        .where(
            StatementReport.stock_code == stock_code,
            StatementReport.period_label == period_label,
            StatementReport.report_kind == report_kind,
        )
        .order_by(StatementReport.version.desc())
        .limit(1)
    )
    content_sha256 = _content_hash(payload)
    superseded_id: UUID | None = None
    if report is not None and report.content_sha256 != content_sha256:
        # 重述：旧版完整保留，新版本从既有最大版本号递增并显式指向旧版。
        superseded_id = report.id
        report = None
    if report is None:
        latest_version = session.scalar(
            select(StatementReport.version)
            .where(
                StatementReport.stock_code == stock_code,
                StatementReport.period_label == period_label,
                StatementReport.report_kind == report_kind,
            )
            .order_by(StatementReport.version.desc())
            .limit(1)
        )
        report = StatementReport(
            company_name=company_name,
            stock_code=stock_code,
            report_kind=report_kind,
            period_label=period_label,
            version=(latest_version or 0) + 1,
            supersedes_id=superseded_id,
        )
        session.add(report)
    report.unit_note = unit_note
    report.source_ref = source_ref
    report.source_sha256 = source_sha256
    report.content_sha256 = content_sha256

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
            page_number: int | None = None
            page_anchor: str | None = None
            if provenance_index is not None:
                # B3 溯源认领：列族+值相等的答案集条目提供页锚（值不同不认领，
                # 同名行靠值区分；无答案集或未命中则保持 NULL，不伪造定位）。
                for column, value in values.items():
                    candidates = provenance_index.get(
                        (str(statement_type), item_name, column, stock_code),
                        set(),
                    )
                    for entry_value, entry_page, entry_anchor in candidates:
                        if entry_value == value:
                            page_number = entry_page
                            page_anchor = entry_anchor
                            break
                    if page_number is not None:
                        break
            report.items.append(
                StatementLineItem(
                    statement_type=str(statement_type),
                    item_name=item_name,
                    sort_order=sort_order,
                    value_end=values.get("value_end"),
                    value_begin=values.get("value_begin"),
                    value_current=values.get("value_current"),
                    value_prior=values.get("value_prior"),
                    page_number=page_number,
                    page_anchor=page_anchor,
                )
            )
    session.flush()
    return report
