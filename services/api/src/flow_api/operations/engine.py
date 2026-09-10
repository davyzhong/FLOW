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
from pathlib import Path
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

# 字典口径求值的指标（code → 指标字典 formula，与指标库同一口径来源）
DICTIONARY_METRICS: dict[str, tuple[str, ...]] = {
    "operational_efficiency": (
        "inventory_turnover",
        "ar_turnover",
        "ap_turnover",
        "dso_days",
        "current_asset_turnover",
    ),
    "growth_quality": ("revenue_growth", "net_profit_growth", "operating_profit_growth"),
}

THEME_UNAVAILABLE_REASON: dict[str, str] = {
    "revenue_structure": "segment_disclosure_missing",
    "users_channels": "internal_data_required",
}

# formula_ref 条目的财报直接执行：标准 item_id 组合（与指标字典 definition
# 同一口径，仅取数角色为财报归一化事实）。D01 引擎对 formula_ref 有意不算
# （归 D02 统一快照）；O2 在快照未建时按同一口径直算，避免主题空转。
FACT_DIRECT_CALCS: dict[str, tuple[str, str, str]] = {
    # code: (numerator_item, denominator_item, label)
    "gross_margin": ("is.gross_profit", "is.revenue", "毛利率"),
    "net_margin": ("is.net_profit", "is.revenue", "净利率"),
    "current_ratio": ("bs.current_assets", "bs.current_liab", "流动比率"),
    "debt_asset_ratio": ("bs.total_liab", "bs.total_assets", "资产负债率"),
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
    source: Literal["d01_entry", "metric_dictionary", "fact_direct"] = "d01_entry"


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


def _facts_with_roles(rows: list[Any]) -> dict[tuple[str, str], Decimal]:
    """role 键事实（与 D01 引擎同构）：end/begin/cur/prior。"""

    facts: dict[tuple[str, str], Decimal] = {}
    for row in rows:
        if row.item_id is None:
            continue
        for column, role in (
            ("value_end", "end"),
            ("value_begin", "begin"),
            ("value_current", "cur"),
            ("value_prior", "prior"),
        ):
            value = getattr(row, column)
            if value is not None:
                facts.setdefault((row.item_id, role), value)
    return facts


def _eval_formula(
    formula: Any, facts: dict[tuple[str, str], Decimal]
) -> Decimal | None:
    """指标字典公式递归求值（div/add/sub/mul/sum/avg/prior/identity）。

    叶子（item_id）按 cur→end→prior→begin 宽容取值；财报点值下 trailing12
    无窗口事实 → not_computable（不近似、不编造）。任何缺口 → None。
    """

    if formula is None:
        return None
    if isinstance(formula, (int, float)):
        return Decimal(str(formula))
    if isinstance(formula, str):
        for role in ("cur", "end", "prior", "begin"):
            value = facts.get((formula, role))
            if value is not None:
                return value
        return None
    op = formula.get("op")
    args = formula.get("args", [])
    if op == "prior":
        leaf = args[0]
        if not isinstance(leaf, str):
            return None
        return facts.get((leaf, "prior"))
    if op == "avg":
        leaf = args[0]
        if not isinstance(leaf, str):
            return None
        end = facts.get((leaf, "end"))
        begin = facts.get((leaf, "begin"))
        if end is None or begin is None:
            return None
        return (end + begin) / Decimal("2")
    if op == "trailing12":
        return None
    values = [_eval_formula(arg, facts) for arg in args]
    if any(value is None for value in values):
        return None
    decimals = [value for value in values if value is not None]
    if op == "div":
        numerator, denominator = decimals[0], decimals[1]
        if denominator == 0:
            return None
        return (numerator / denominator).quantize(Decimal("0.0001"))
    if op in ("add", "sum"):
        result = Decimal("0")
        for value in decimals:
            result += value
        return result
    if op == "sub":
        result = decimals[0]
        for value in decimals[1:]:
            result -= value
        return result
    if op == "mul":
        result = Decimal("1")
        for value in decimals:
            result *= value
        return result
    if op == "identity":
        return decimals[0]
    return None


def _load_metric_formulas() -> dict[str, tuple[dict[str, Any], str]]:
    import yaml

    relative = Path("config/metrics/metric_dictionary_v1.yaml")
    data: dict[str, Any] | None = None
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_file():
            data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            break
    if data is None:
        return {}
    formulas: dict[str, tuple[dict[str, Any], str]] = {}
    for group in ("metrics_general", "metrics_logistics"):
        for entry in data.get(group, []):
            formula = entry.get("formula")
            if isinstance(formula, dict):
                formulas[entry["metric_code"]] = (formula, entry.get("name", entry["metric_code"]))
    return formulas


def build_operations_overview(session: Any, *, report_id: str | UUID) -> OperationsOverview:
    """六主题经营概览：D01 条目按主题分组 + 分层判定 + 联动信号（≤3）。"""

    analysis = ObjectiveAnalysisService(session).analyze(report_id)
    entry_by_id = {entry.entry_id: entry for entry in analysis.entries}

    from sqlalchemy import select

    from flow_api.infrastructure.models.statement import StatementNormalizedItem

    rows = list(
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report_id
            )
        )
    )

    role_facts = _facts_with_roles(rows)

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
            if (
                entry.status == ObjectiveStatus.NOT_APPLICABLE
                and entry.entry_id in FACT_DIRECT_CALCS
                and role_facts is not None
            ):
                numerator_item, denominator_item, label = FACT_DIRECT_CALCS[
                    entry.entry_id
                ]
                numerator = role_facts.get((numerator_item, "cur"))
                denominator = role_facts.get((denominator_item, "cur"))
                if (
                    numerator is not None
                    and denominator is not None
                    and denominator != 0
                ):
                    value = (numerator / denominator).quantize(Decimal("0.0001"))
                    metrics.append(
                        OperationsMetricItem(
                            entry_id=entry.entry_id,
                            name=label,
                            status=ObjectiveStatus.COMPUTED.value,
                            value=str(value),
                            basis="本期归一化事实（财报直接口径）",
                            caliber_note=f"{numerator_item} ÷ {denominator_item}",
                            source="fact_direct",
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
        dictionary_codes = DICTIONARY_METRICS.get(theme_id, ())
        if dictionary_codes:
            formulas = _load_metric_formulas()
            for code in dictionary_codes:
                if code in {m.entry_id for m in metrics}:
                    continue
                formula = formulas.get(code)
                if formula is None:
                    metrics.append(
                        OperationsMetricItem(
                            entry_id=code,
                            name=code,
                            status=ObjectiveStatus.NOT_COMPUTABLE.value,
                            reason="metric_not_in_dictionary",
                            source="metric_dictionary",
                        )
                    )
                    continue
                formula_dict, name = formula
                dictionary_value: Decimal | None = _eval_formula(
                    formula_dict, role_facts
                )
                metrics.append(
                    OperationsMetricItem(
                        entry_id=code,
                        name=name,
                        status=ObjectiveStatus.COMPUTED.value
                        if dictionary_value is not None
                        else ObjectiveStatus.NOT_COMPUTABLE.value,
                        value=str(dictionary_value)
                        if dictionary_value is not None
                        else None,
                        basis="指标字典公式（财报归一化事实）",
                        reason=None
                        if dictionary_value is not None
                        else "fact_missing",
                        source="metric_dictionary",
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

    facts = _facts_from_normalized(rows)

    return OperationsOverview(
        report_id=str(report_id),
        catalog_id=analysis.catalog_id,
        themes=themes,
        management_watch=management_watch(facts),
    )


__all__ = ["build_operations_overview", "OperationsOverview", "OperationsTheme"]
