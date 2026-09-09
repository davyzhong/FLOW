"""U7/P07：四问分析工作台数据服务与 typed API。

从 config/analysis/objective_topics_v1.yaml 读取主题合同，结合
statement_report 归一化行，为每个主题产出"结果→趋势→结构→驱动→明细"
统一页面语法的预计算数据。主题不可用（缺 required_facts）时给出
unavailable_reasons，不补造数值（D049）。
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementNormalizedItem,
    StatementReport,
)

_TOPICS_PATH = Path(__file__).resolve().parents[4] / "config/analysis/objective_topics_v1.yaml"


def load_topics_catalog(path: Path | None = None) -> dict[str, Any]:
    resolved = Path(path) if path else _TOPICS_PATH
    for candidate in (
        resolved,
        *(parent / "config/analysis/objective_topics_v1.yaml" for parent in resolved.parents),
    ):
        if candidate.is_file():
            return cast(dict[str, Any], yaml.safe_load(candidate.read_text(encoding="utf-8")))
    raise FileNotFoundError(f"主题合同配置不存在：{resolved}")


def _facts_from_rows(  # noqa: E501
    rows: list[StatementNormalizedItem],
) -> dict[str, Decimal]:
    facts: dict[str, Decimal] = {}
    for row in rows:
        if not row.item_id:
            continue
        current = row.value_current if row.value_current is not None else row.value_end
        prior = row.value_prior if row.value_prior is not None else row.value_begin
        if current is not None:
            facts.setdefault(row.item_id, current)
        if prior is not None:
            facts.setdefault(f"{row.item_id}__prev", prior)
    return facts


def _metric_value(
    facts: dict[str, Decimal], numerator: str, denominator: str | None
) -> Decimal | None:
    num = facts.get(numerator)
    den = facts.get(denominator) if denominator else Decimal("1")
    if num is None or den is None or den == 0:
        return None
    return (num / den).quantize(Decimal("0.0001"))


# 四问主指标的确定性计算（全部来自归一化行 item_id；不引入新口径）
_METRIC_CALCS = {
    "revenue": lambda f: _metric_value(f, "is.revenue", None),
    "revenue_growth": lambda f: _growth(f, "is.revenue"),
    "gross_margin": lambda f: _ratio_pct(f, "is.gross_profit", "is.revenue"),
    "net_margin": lambda f: _ratio_pct(f, "is.net_profit", "is.revenue"),
    "operating_margin": lambda f: _ratio_pct(f, "is.operating_profit", "is.revenue"),
    "dso_days": lambda f: _metric_value(f, "bs.ar", "is.revenue"),
    "total_asset_turnover": lambda f: _metric_value(f, "is.revenue", "bs.total_assets"),
    "debt_asset_ratio": lambda f: _ratio_pct(f, "bs.total_liab", "bs.total_assets"),
    "ocf": lambda f: _metric_value(f, "cf.ocf", None),
    "ocf_net_profit_ratio": lambda f: _ratio_pct(f, "cf.ocf", "is.net_profit"),
}


def _growth(facts: dict[str, Decimal], item_id: str) -> Decimal | None:
    cur = facts.get(item_id)
    prev = facts.get(f"{item_id}__prev")
    if cur is None or prev is None or prev == Decimal("0"):
        return None
    return ((cur - prev) / abs(prev)).quantize(Decimal("0.0001"))


def _ratio_pct(facts: dict[str, Decimal], num_id: str, den_id: str) -> Decimal | None:
    num = facts.get(num_id)
    den = facts.get(den_id)
    if num is None or den is None or den == Decimal("0"):
        return None
    return (num / den).quantize(Decimal("0.0001"))


def management_watch(facts: dict[str, Decimal]) -> list[dict[str, str]]:
    """管理关注（借鉴 #5）：≤3 条、条条带值带向，确定性规则、无普适阈值。

    信号全部为「提示复核」语义（C14）：不解释原因、不输出正面表扬、
    缺口径时静默跳过（不编造）。
    """

    watches: list[dict[str, str]] = []
    revenue_growth = _growth(facts, "is.revenue")
    ar_growth = _growth(facts, "bs.ar")
    if revenue_growth is not None and ar_growth is not None and ar_growth > revenue_growth:
        watches.append(
            {
                "code": "ar_outpacing_revenue",
                "message": (
                    f"应收账款增速 {ar_growth} 高于营业收入增速 {revenue_growth}，"
                    "建议核对回款与账龄（联动提示，不构成原因判断）"
                ),
                "direction": "warning",
            }
        )
    cash_ratio = _ratio_pct(facts, "cf.ocf", "is.net_profit")
    if cash_ratio is not None and cash_ratio < Decimal("1"):
        watches.append(
            {
                "code": "cash_content_below_one",
                "message": f"净利润现金含量 {cash_ratio}，经营现金流低于净利润",
                "direction": "negative",
            }
        )
    if revenue_growth is not None and revenue_growth < Decimal("0"):
        watches.append(
            {
                "code": "revenue_decline",
                "message": f"营业收入同比 {revenue_growth}，同比下降",
                "direction": "negative",
            }
        )
    leverage_current = _ratio_pct(facts, "bs.total_liab", "bs.total_assets")
    leverage_prior = _ratio_pct(
        facts, "bs.total_liab__prev", "bs.total_assets__prev"
    )
    if (
        leverage_current is not None
        and leverage_prior is not None
        and leverage_current > leverage_prior
    ):
        watches.append(
            {
                "code": "leverage_rising",
                "message": f"资产负债率较上期上升至 {leverage_current}",
                "direction": "warning",
            }
        )
    return watches[:3]


class ManagementWatchItem(BaseModel):
    """管理关注条目：确定性信号，带值带向，不解释原因。"""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    direction: Literal["negative", "warning"]


class WorkbenchMetricItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_code: str
    available: bool
    value: str | None = None
    unavailable_reason: str | None = None


class WorkbenchQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    name: str
    metrics: list[WorkbenchMetricItem]


class WorkbenchReportIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    company_name: str
    period_label: str
    unit_note: str


class WorkbenchResponse(BaseModel):
    """四问工作台响应：只读投影 + 管理关注（≤3 条）。"""

    model_config = ConfigDict(extra="forbid")

    workbench_id: str
    report: WorkbenchReportIdentity
    questions: list[WorkbenchQuestion]
    management_watch: list[ManagementWatchItem]
    facts_available: list[str]


def build_four_question_workbench(
    session: Session,
    *,
    report_id: str | UUID,
    mapping_version: str = "v1",
) -> dict[str, Any]:
    report = session.get(StatementReport, UUID(str(report_id)))
    if report is None:
        raise KeyError("statement_report_not_found")
    rows = list(
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report.id,
                StatementNormalizedItem.mapping_version == mapping_version,
            )
        )
    )
    facts = _facts_from_rows(rows)
    catalog = load_topics_catalog()

    questions = []
    for question_key, question_def in catalog.get("questions", {}).items():
        metric_items = []
        for entry in catalog.get("essential_metrics", []):
            if entry.get("question") != question_key:
                continue
            code = entry["metric_code"]
            calc = _METRIC_CALCS.get(code)
            value = calc(facts) if calc else None
            item: dict[str, Any] = {
                "metric_code": code,
                "available": value is not None,
            }
            if value is not None:
                item["value"] = str(value)
            if not entry.get("unavailable_when"):
                item["unavailable_reason"] = entry.get("metric_code")
            metric_items.append(item)
        questions.append(
            {
                "key": question_key,
                "name": question_def["name"],
                "metrics": metric_items,
            }
        )

    return {
        "workbench_id": catalog["topics_catalog_id"],
        "report": {
            "report_id": str(report.id),
            "company_name": report.company_name,
            "period_label": report.period_label,
            "unit_note": report.unit_note,
        },
        "questions": questions,
        "management_watch": management_watch(facts),
        "facts_available": sorted(facts.keys()),
    }


__all__ = [
    "ManagementWatchItem",
    "WorkbenchMetricItem",
    "WorkbenchQuestion",
    "WorkbenchReportIdentity",
    "WorkbenchResponse",
    "build_four_question_workbench",
    "load_topics_catalog",
    "management_watch",
]
