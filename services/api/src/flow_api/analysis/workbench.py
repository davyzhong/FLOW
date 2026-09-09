"""U7/P07：四问分析工作台数据服务与 typed API。

从 config/analysis/objective_topics_v1.yaml 读取主题合同，结合
statement_report 归一化行，为每个主题产出"结果→趋势→结构→驱动→明细"
统一页面语法的预计算数据。主题不可用（缺 required_facts）时给出
unavailable_reasons，不补造数值（D049）。
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
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
            return yaml.safe_load(candidate.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"主题合同配置不存在：{resolved}")


def _facts_from_rows(  # noqa: E501
    rows: list[StatementNormalizedItem],
) -> dict[str, Decimal]:
    facts: dict[str, Decimal] = {}
    for row in rows:
        if not row.item_id:
            continue
        for column in ("value_current", "value_end", "value_prior", "value_begin"):
            value = getattr(row, column)
            if value is not None:
                facts.setdefault(row.item_id, value)
                break
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
    if cur is None or prev in (None, Decimal("0")):
        return None
    return ((cur - prev) / abs(prev)).quantize(Decimal("0.0001"))


def _ratio_pct(facts: dict[str, Decimal], num_id: str, den_id: str) -> Decimal | None:
    num = facts.get(num_id)
    den = facts.get(den_id)
    if num is None or den in (None, Decimal("0")):
        return None
    return (num / den).quantize(Decimal("0.0001"))


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
        "facts_available": sorted(facts.keys()),
    }


__all__ = ["build_four_question_workbench", "load_topics_catalog"]
