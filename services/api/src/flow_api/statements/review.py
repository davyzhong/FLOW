"""事实复核、人工更正与发布门禁（B05）。

- 更正只增不改（statement_correction 审计链）；发布状态的报表锁定，更正拒绝；
- 发布前对「原始行 + 已应用更正」的修正视图重新跑勾稽，关键不平衡阻断发布；
- 原始披露值永不被改写，更正以叠加层生效。
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementCorrection,
    StatementReport,
)
from flow_api.statements.extraction import (
    AShareTableExtractor,
    ExtractionResult,
    HkTraditionalExtractor,
)
from flow_api.statements.reconciliation import ReportQuality, evaluate_report_quality

# 数值列键 ↔ 披露原文列名
COLUMN_KEYS = ("value_end", "value_begin", "value_current", "value_prior")
COLUMN_LABELS = {
    "value_end": "期末余额",
    "value_begin": "期初余额",
    "value_current": "本期发生额",
    "value_prior": "上期发生额",
}
LABEL_TO_KEY = {v: k for k, v in COLUMN_LABELS.items()}


class ReviewError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ReviewBlockedError(ReviewError):
    pass


def _report_or_404(session: Session, report_id: UUID) -> StatementReport:
    report = session.get(StatementReport, report_id)
    if report is None:
        raise ReviewError("statement_report_not_found", "指定的财报报告不存在")
    return report


def corrected_statements(
    report: StatementReport, corrections_list: list[StatementCorrection] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """原始行叠加已记录更正后的修正视图（抽取器勾稽函数可直接消费）。

    corrections_list 显式传入以免命中会话内过期的关系缓存；缺省用 report.corrections。
    """

    corrections: dict[tuple[str, str, str], StatementCorrection] = {}
    for correction in corrections_list if corrections_list is not None else report.corrections:
        key = (correction.statement_type, correction.item_name, correction.column_key)
        corrections[key] = correction  # 同点多次更正取最新（created_at 递增）

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in report.items:
        row: dict[str, Any] = {"item": item.item_name}
        for column_key, label in COLUMN_LABELS.items():
            value = getattr(item, column_key)
            override = corrections.get((item.statement_type, item.item_name, column_key))
            if override is not None:
                value = override.new_value
            row[label] = float(value) if value is not None else None
        grouped[item.statement_type].append(row)
    return dict(grouped)


def evaluate_stored_report(
    report: StatementReport,
    *,
    corrections_applied: bool = True,
    corrections_list: list[StatementCorrection] | None = None,
) -> ReportQuality:
    """对库内报表重跑勾稽与覆盖评估（默认修正视图）。"""

    if corrections_applied:
        statements = corrected_statements(report, corrections_list)
    else:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in report.items:
            row: dict[str, Any] = {"item": item.item_name}
            for column_key, label in COLUMN_LABELS.items():
                value = getattr(item, column_key)
                row[label] = float(value) if value is not None else None
            grouped[item.statement_type].append(row)
        statements = dict(grouped)
    # 简化/繁体自适应：繁体版式用港股勾稽，其余用 A 股勾稽
    sample_names = {item["item"] for rows in statements.values() for item in rows}
    traditional = any("資產總額" in name or "營業成本" in name for name in sample_names)
    checks = (
        HkTraditionalExtractor()._reconcile(statements)
        if traditional
        else AShareTableExtractor()._reconcile(statements)
    )
    result = ExtractionResult(
        adapter_id="stored",
        unit_note=report.unit_note,
        statements=statements,
        checks=tuple(checks),
        warnings=(),
        page_count=0,
        source_sha256=report.source_sha256 or "",
    )
    return evaluate_report_quality(result, report_kind=report.report_kind)


class ReviewService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_correction(
        self,
        report_id: UUID,
        *,
        statement_type: str,
        item_name: str,
        column_key: str,
        new_value: str,
        reason: str,
        operator: str,
    ) -> StatementCorrection:
        report = _report_or_404(self._session, report_id)
        if report.status == "published":
            raise ReviewError("report_locked", "报表已发布，不得再更正")
        if column_key not in COLUMN_KEYS:
            raise ReviewError(
                "unknown_column", f"未知列：{column_key}（可用：{list(COLUMN_KEYS)}）"
            )
        if not reason.strip() or not operator.strip():
            raise ReviewError("correction_incomplete", "更正必须填写原因与操作者")
        item = next(
            (
                line
                for line in report.items
                if line.statement_type == statement_type and line.item_name == item_name
            ),
            None,
        )
        if item is None:
            raise ReviewError(
                "item_not_found", f"{statement_type} 中不存在行项目「{item_name}」"
            )
        try:
            parsed = Decimal(new_value.replace(",", "").strip()) if new_value.strip() else None
        except (InvalidOperation, AttributeError) as error:
            raise ReviewError("invalid_value", f"更正值不是可用数字：{new_value!r}") from error
        old_value = getattr(item, column_key)
        if parsed == old_value:
            raise ReviewError("no_change", "更正值与原值一致，无需更正")
        correction = StatementCorrection(
            report_id=report.id,
            statement_type=statement_type,
            item_name=item_name,
            column_key=column_key,
            old_value=old_value,
            new_value=parsed,
            reason=reason.strip(),
            operator=operator.strip(),
        )
        self._session.add(correction)
        self._session.flush()
        return correction

    def list_corrections(self, report_id: UUID) -> list[StatementCorrection]:
        _report_or_404(self._session, report_id)
        return list(
            self._session.scalars(
                select(StatementCorrection)
                .where(StatementCorrection.report_id == report_id)
                .order_by(StatementCorrection.created_at)
            )
        )

    def publish(self, report_id: UUID, *, operator: str) -> StatementReport:
        report = _report_or_404(self._session, report_id)
        if report.status == "published":
            raise ReviewError("report_locked", "报表已发布")
        if not operator.strip():
            raise ReviewError("correction_incomplete", "发布必须记录操作者")
        quality = evaluate_stored_report(
            report, corrections_list=self.list_corrections(report.id)
        )
        if not quality.publishable:
            raise ReviewBlockedError(
                "critical_imbalance",
                "存在关键勾稽不平衡，阻断发布：" + "；".join(quality.blockers),
            )
        report.status = "published"
        self._session.flush()
        return report


__all__ = [
    "ReviewBlockedError",
    "ReviewError",
    "ReviewService",
    "corrected_statements",
    "evaluate_stored_report",
]
