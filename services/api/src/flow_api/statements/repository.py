"""报表分析的只读仓储。"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from flow_api.infrastructure.models.statement import StatementReport

StatementUnavailableCode = Literal["statement_report_not_found"]


class StatementReportUnavailableError(Exception):
    def __init__(self, code: StatementUnavailableCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StatementReportRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_reports(self) -> list[StatementReport]:
        result = self._session.scalars(
            select(StatementReport)
            .options(selectinload(StatementReport.items))
            .order_by(StatementReport.created_at, StatementReport.company_name)
        )
        return list(result)

    def get_report(self, report_id: UUID) -> StatementReport:
        report = self._session.scalar(
            select(StatementReport)
            .options(selectinload(StatementReport.items))
            .where(StatementReport.id == report_id)
        )
        if report is None:
            raise StatementReportUnavailableError(
                "statement_report_not_found", "指定的财报报告不存在"
            )
        return report
