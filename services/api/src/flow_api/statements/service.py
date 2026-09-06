"""报表分析服务：ORM → 领域模型（frozen），固定报表展示顺序。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import StatementLineItem, StatementReport
from flow_api.statements.models import (
    StatementLine,
    StatementReportDetail,
    StatementReportList,
    StatementReportSummary,
    StatementSection,
)
from flow_api.statements.repository import (
    StatementReportRepository,
    StatementReportUnavailableError,
)

# 披露惯例顺序：资产负债表 → 利润表 → 现金流量表 → 其他（按名称）。
_STATEMENT_ORDER = {"合并资产负债表": 0, "合并利润表": 1, "合并现金流量表": 2}


def _statement_sort_key(statement_type: str) -> tuple[int, str]:
    return (_STATEMENT_ORDER.get(statement_type, len(_STATEMENT_ORDER)), statement_type)


def _summary_from(
    report: StatementReport, items: list[StatementLineItem]
) -> StatementReportSummary:
    return StatementReportSummary(
        id=report.id,
        company_name=report.company_name,
        stock_code=report.stock_code,
        report_kind=report.report_kind,
        period_label=report.period_label,
        version=report.version,
        status=report.status,
        unit_note=report.unit_note,
        source_ref=report.source_ref,
        source_sha256=report.source_sha256,
        statement_types=tuple(sorted({i.statement_type for i in items}, key=_statement_sort_key)),
        line_item_count=len(items),
        created_at=report.created_at,
    )


class StatementService:
    def list_reports(self, session: Session) -> StatementReportList:
        reports = StatementReportRepository(session).list_reports()
        return StatementReportList(
            reports=tuple(
                _summary_from(report, list(report.items)) for report in reports
            )
        )

    def get_report(self, session: Session, report_id: UUID) -> StatementReportDetail:
        try:
            report = StatementReportRepository(session).get_report(report_id)
        except StatementReportUnavailableError:
            raise
        items = sorted(
            report.items, key=lambda i: (_statement_sort_key(i.statement_type), i.sort_order)
        )
        sections: list[StatementSection] = []
        for statement_type in dict.fromkeys(i.statement_type for i in items):
            sections.append(
                StatementSection(
                    statement_type=statement_type,
                    items=tuple(
                        StatementLine(
                            item_name=i.item_name,
                            sort_order=i.sort_order,
                            value_end=i.value_end,
                            value_begin=i.value_begin,
                            value_current=i.value_current,
                            value_prior=i.value_prior,
                        )
                        for i in items
                        if i.statement_type == statement_type
                    ),
                )
            )
        return StatementReportDetail(
            **_summary_from(report, list(report.items)).model_dump(),
            sections=tuple(sections),
        )


__all__ = ["StatementService", "StatementReportUnavailableError"]
