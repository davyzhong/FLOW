"""报表分析的只读仓储。"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
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
        # 列表只展示每个身份（公司/期间/种类）的最新版本；历史版本经详情与后续版本接口查询。
        latest_versions = (
            select(
                StatementReport.stock_code,
                StatementReport.period_label,
                StatementReport.report_kind,
                func.max(StatementReport.version).label("max_version"),
            )
            .group_by(
                StatementReport.stock_code,
                StatementReport.period_label,
                StatementReport.report_kind,
            )
            .subquery()
        )
        result = self._session.scalars(
            select(StatementReport)
            .options(selectinload(StatementReport.items))
            .join(
                latest_versions,
                (StatementReport.stock_code == latest_versions.c.stock_code)
                & (StatementReport.period_label == latest_versions.c.period_label)
                & (StatementReport.report_kind == latest_versions.c.report_kind)
                & (StatementReport.version == latest_versions.c.max_version),
            )
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
