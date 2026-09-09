"""经营轨 L1 指标计算（O2，D050/OP 方法论）。

复用纪律：条目数值全部来自 D01 客观引擎（objective_finance_v1）的确定性
计算，本模块只做主题分组、数据可得性分层（OP-0）与联动信号组装，
不另建第二套口径、不引入新财务数字。

分层（OP-0）：financial_report 主题消费 D01 条目出数；
internal_process / internal_events 主题一律 not_applicable（typed 原因），
缺失不补造、无量价数据不生成量价链。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from flow_api.analysis.objective import (
    ObjectiveAnalysisService,
    ObjectiveStatus,
)
from flow_api.analysis.workbench import management_watch

THEME_ENTRIES: dict[str, tuple[str, ...]] = {
    "growth_quality": ("revenue_yoy", "net_profit_yoy", "asset_trend"),
    "profit_quality": (
        "gross_margin",
        "net_margin",
        "ocf_to_net_profit",
        "dupont_three_factor",
    ),
    "cost_structure": ("gross_margin",),
    "operational_efficiency": ("current_ratio", "debt_asset_ratio"),
    # revenue_structure：L1 需分部/产品线披露，当前财报样本无分部表 → typed 缺失
    "revenue_structure": (),
    "users_channels": (),
}

THEME_UNAVAILABLE_REASON: dict[str, str] = {
    "revenue_structure": "segment_disclosure_missing",
    "users_channels": "internal_data_required",
}

_THEME_NAMES = {
    "growth_quality": "增长质量",
    "revenue_structure": "收入结构",
    "cost_structure": "成本费用结构",
    "profit_quality": "盈利质量",
    "users_channels": "用户与渠道",
    "operational_efficiency": "运营效率",
}


class OperationsMetricItem(BaseModel):
    """事实卡片（D01 事实合同）：值、比较基准、口径、来源引用缺一不可。"""

    model_config = ConfigDict(extra="forbid")

    entry_id: str
    name: str
    status: str
    value: str | None = None
    basis: str = ""
    caliber_note: str = ""
    reason: str | None = None


class OperationsTheme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme_id: str
    name: str
    availability: Literal["financial_report", "internal_process", "internal_events"]
    status: Literal["available", "not_applicable"]
    reason: str | None = None
    metrics: list[OperationsMetricItem]


class OperationsOverview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    catalog_id: str
    themes: list[OperationsTheme]
    management_watch: list[dict[str, str]]


def _facts_from_normalized(rows: list[Any]) -> dict[str, Decimal]:
    facts: dict[str, Decimal] = {}
    for row in rows:
        if row.item_id is None:
            continue
        current = row.value_current if row.value_current is not None else row.value_end
        prior = row.value_prior if row.value_prior is not None else row.value_begin
        if current is not None:
            facts.setdefault(row.item_id, current)
        if prior is not None:
            facts.setdefault(f"{row.item_id}__prev", prior)
    return facts


def build_operations_overview(session: Any, *, report_id: str | UUID) -> OperationsOverview:
    """六主题经营概览：D01 条目按主题分组 + 分层判定 + 联动信号（≤3）。"""

    analysis = ObjectiveAnalysisService(session).analyze(report_id)
    entry_by_id = {entry.entry_id: entry for entry in analysis.entries}

    themes: list[OperationsTheme] = []
    for theme_id in (
        "growth_quality",
        "revenue_structure",
        "cost_structure",
        "profit_quality",
        "users_channels",
        "operational_efficiency",
    ):
        entry_ids = THEME_ENTRIES.get(theme_id, ())
        if not entry_ids:
            themes.append(
                OperationsTheme(
                    theme_id=theme_id,
                    name=_THEME_NAMES[theme_id],
                    availability="internal_process"
                    if theme_id == "users_channels"
                    else "financial_report",
                    status="not_applicable",
                    reason=THEME_UNAVAILABLE_REASON.get(theme_id),
                    metrics=[],
                )
            )
            continue
        metrics = []
        for entry_id in entry_ids:
            entry = entry_by_id.get(entry_id)
            if entry is None:
                metrics.append(
                    OperationsMetricItem(
                        entry_id=entry_id,
                        name=entry_id,
                        status=ObjectiveStatus.NOT_COMPUTABLE.value,
                        reason="entry_missing",
                    )
                )
                continue
            metrics.append(
                OperationsMetricItem(
                    entry_id=entry.entry_id,
                    name=entry.name,
                    status=entry.status.value,
                    value=entry.value,
                    basis=entry.basis,
                    caliber_note=entry.caliber_note,
                    reason=entry.reason,
                )
            )
        themes.append(
            OperationsTheme(
                theme_id=theme_id,
                name=_THEME_NAMES[theme_id],
                availability="financial_report",
                status="available",
                metrics=metrics,
            )
        )

    from sqlalchemy import select

    from flow_api.infrastructure.models.statement import StatementNormalizedItem

    rows = list(
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report_id
            )
        )
    )
    facts = _facts_from_normalized(rows)

    return OperationsOverview(
        report_id=str(report_id),
        catalog_id=analysis.catalog_id,
        themes=themes,
        management_watch=management_watch(facts),
    )


__all__ = ["build_operations_overview", "OperationsOverview", "OperationsTheme"]
