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
from flow_api.operations.facts import (
    OperatingFact,
    load_cainiao_operating_facts,
    previous_comparable_period,
)

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

# 分部系列数据集（L1：公开分部报告披露，可溯源）。按公司键约定路径读取；
# 数据集不存在时 revenue_structure 回退 typed 缺失，不编造。
SEGMENT_SERIES_BY_STOCK: dict[str, Path] = {
    "CAINIAO": Path("docs/implementation/p5/cainiao_segment_series.yaml"),
}

OPERATING_FACTS_BY_STOCK: dict[str, Path] = {
    "CAINIAO": Path("docs/implementation/p5/cainiao_operating_metrics.yaml"),
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
    source: Literal[
        "d01_entry", "metric_dictionary", "fact_direct", "operating_fact"
    ] = "d01_entry"
    period_label: str = ""
    period_type: str = ""
    assurance: str = ""
    source_ref: str = ""
    source_sha256: str = ""
    source_page: str = ""


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


class PublicOperatingPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    stock_code: str
    period_label: str
    period_type: str
    assurance: str
    is_stub: bool


class PublicOperatingPeriodList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periods: list[PublicOperatingPeriod]


class OperationsSnapshotLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    statement_report_id: str
    version: int
    company_name: str
    stock_code: str
    period_label: str
    payload_hash: str
    created_at: str | None = None


class OperationsSnapshotList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshots: list[OperationsSnapshotLine]


_OPERATING_FACT_THEME = {
    "international_parcels": "growth_quality",
    "china_orders_fulfilled": "growth_quality",
    "adjusted_net_profit": "profit_quality",
    "adjusted_net_profit_margin": "profit_quality",
    "adjusted_ebitda": "profit_quality",
    "adjusted_ebitda_margin": "profit_quality",
    "business_line_share.international_logistics": "revenue_structure",
    "business_line_share.china_logistics": "revenue_structure",
    "business_line_share.technology_and_other_services": "revenue_structure",
}


def operating_fact_metrics_for_period(
    facts: list[OperatingFact], *, selected_period: str
) -> dict[str, list[OperationsMetricItem]]:
    """把严格同期间经营事实投影到主题；比较基准只取同频上年同期。"""

    current = [fact for fact in facts if fact.period_label == selected_period]
    previous_label = previous_comparable_period(selected_period)
    previous = {
        fact.metric_code: fact
        for fact in facts
        if previous_label is not None and fact.period_label == previous_label
    }
    grouped: dict[str, list[OperationsMetricItem]] = {}
    for fact in current:
        theme_id = _OPERATING_FACT_THEME.get(fact.metric_code)
        if theme_id is None:
            continue
        prior = previous.get(fact.metric_code)
        value = (
            str(fact.numeric_value)
            if fact.numeric_value is not None
            else fact.text_value
        )
        if prior is not None:
            prior_value = (
                str(prior.numeric_value)
                if prior.numeric_value is not None
                else prior.text_value
            )
            basis = f"{previous_label} {prior_value} {prior.unit}"
        else:
            basis = f"{selected_period} 原始披露；无同频可比期间"
        grouped.setdefault(theme_id, []).append(
            OperationsMetricItem(
                entry_id=fact.metric_code,
                name=fact.metric_name,
                status=ObjectiveStatus.COMPUTED.value,
                value=value,
                basis=basis,
                caliber_note=fact.caliber_note,
                source="operating_fact",
                period_label=fact.period_label,
                period_type=fact.period_type,
                assurance=fact.assurance,
                source_ref=fact.source_ref,
                source_sha256=fact.source_sha256,
                source_page=fact.source_page,
            )
        )
    return grouped


def list_public_operating_periods() -> list[PublicOperatingPeriod]:
    """列出真实披露期间；不合成月度选项。"""

    periods: list[PublicOperatingPeriod] = []
    for stock_code in OPERATING_FACTS_BY_STOCK:
        facts = load_operating_facts(stock_code)
        seen: set[str] = set()
        for fact in facts:
            if fact.period_label in seen:
                continue
            seen.add(fact.period_label)
            periods.append(
                PublicOperatingPeriod(
                    company_name=fact.company_name,
                    stock_code=fact.stock_code,
                    period_label=fact.period_label,
                    period_type=fact.period_type,
                    assurance=fact.assurance,
                    is_stub=fact.is_stub,
                )
            )
    return periods


def build_public_operating_overview(
    *, stock_code: str, selected_period: str
) -> OperationsOverview:
    """为没有完整财报的公开经营期间生成只读六主题概览。"""

    facts = load_operating_facts(stock_code)
    if not any(fact.period_label == selected_period for fact in facts):
        raise ValueError("operating_period_not_found")
    operating_metrics = operating_fact_metrics_for_period(
        facts, selected_period=selected_period
    )
    segment_series = load_segment_series(stock_code)
    themes: list[OperationsTheme] = []
    for theme_id in (
        "growth_quality",
        "revenue_structure",
        "cost_structure",
        "profit_quality",
        "users_channels",
        "operational_efficiency",
    ):
        extra_metrics = operating_metrics.get(theme_id, [])
        if theme_id == "revenue_structure" and segment_series is not None:
            theme = _segment_revenue_theme(
                segment_series, selected_period=selected_period
            )
            theme.metrics.extend(extra_metrics)
            if extra_metrics and theme.status == "not_applicable":
                theme.status = "available"
            themes.append(theme)
            continue
        if extra_metrics:
            themes.append(
                OperationsTheme(
                    theme_id=theme_id,
                    name=_THEME_NAMES[theme_id],
                    availability="financial_report",
                    status="available",
                    metrics=extra_metrics,
                )
            )
            continue
        reason = (
            "internal_data_required"
            if theme_id == "users_channels"
            else "statement_report_required"
        )
        themes.append(
            OperationsTheme(
                theme_id=theme_id,
                name=_THEME_NAMES[theme_id],
                availability="internal_process"
                if theme_id == "users_channels"
                else "financial_report",
                status="not_applicable",
                reason=reason,
                metrics=[],
            )
        )
    return OperationsOverview(
        report_id=f"operating:{stock_code}:{selected_period}",
        catalog_id="flow.analysis.objective_finance.v1",
        themes=themes,
        management_watch=[],
    )


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


def load_segment_series(stock_code: str) -> dict[str, Any] | None:
    """加载公司分部系列数据集（L1 公开分部披露，可溯源到年报原文）。"""

    relative = SEGMENT_SERIES_BY_STOCK.get(stock_code)
    if relative is None:
        return None
    import yaml

    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_file():
            loaded: dict[str, Any] = yaml.safe_load(
                candidate.read_text(encoding="utf-8")
            )
            return loaded
    return None


def load_operating_facts(stock_code: str) -> list[OperatingFact]:
    """加载公司经营事实并在适配器边界转换为统一 typed 合同。"""

    relative = OPERATING_FACTS_BY_STOCK.get(stock_code)
    if relative is None:
        return []
    for root in (Path.cwd(), *Path.cwd().parents):
        candidate = root / relative
        if candidate.is_file() and stock_code == "CAINIAO":
            return load_cainiao_operating_facts(candidate, repo_root=root)
    return []


def _segment_revenue_theme(
    series: dict[str, Any], *, selected_period: str
) -> OperationsTheme:
    """分部收入主题（L1 公开分部披露）：确定性同比 + 缺口如实说明。"""

    series_data: dict[str, dict[str, Any]] = series.get("series", {})
    metrics: list[OperationsMetricItem] = []
    notes: list[str] = []
    selected = series_data.get(selected_period)
    if selected is None:
        return OperationsTheme(
            theme_id="revenue_structure",
            name=_THEME_NAMES["revenue_structure"],
            availability="financial_report",
            status="not_applicable",
            reason="segment_period_not_available",
            metrics=[],
        )

    prev_period = previous_comparable_period(selected_period)
    cur_revenue = selected.get("segment_revenue")
    prev_revenue = (
        series_data.get(prev_period, {}).get("segment_revenue") if prev_period else None
    )
    if cur_revenue is not None and prev_revenue is not None and prev_period is not None:
        cur_value = Decimal(str(cur_revenue))
        prev_value = Decimal(str(prev_revenue))
        yoy = ((cur_value - prev_value) / abs(prev_value)).quantize(Decimal("0.0001"))
        metrics.append(
            OperationsMetricItem(
                entry_id="segment_revenue_yoy",
                name=f"分部收入同比（{selected_period} vs {prev_period}）",
                status=ObjectiveStatus.COMPUTED.value,
                value=str(yoy),
                basis=f"{prev_period} 分部收入 {prev_value}",
                caliber_note=series.get("unit", ""),
                source="fact_direct",
            )
        )
    ebita_value = selected.get("adjusted_ebita")
    if ebita_value is not None:
        metrics.append(
            OperationsMetricItem(
                entry_id="segment_adjusted_ebita",
                name=f"经调整 EBITA（{selected_period}，MPM 口径）",
                status=ObjectiveStatus.COMPUTED.value,
                value=str(ebita_value),
                basis=f"{selected_period} 分部披露",
                caliber_note="经调整 EBITA 为 MPM，须有调节表（D047）",
                source="fact_direct",
            )
        )
    elif any(row.get("adjusted_ebita") is not None for row in series_data.values()):
        notes.append(f"{selected_period} 未单列经调整 EBITA，如实缺省")

    note_text = "；".join(note for note in notes if note) or None
    return OperationsTheme(
        theme_id="revenue_structure",
        name=_THEME_NAMES["revenue_structure"],
        availability="financial_report",
        status="available",
        reason=note_text,
        metrics=metrics,
    )


def build_operations_overview(session: Any, *, report_id: str | UUID) -> OperationsOverview:
    """六主题经营概览：D01 条目按主题分组 + 分层判定 + 联动信号（≤3）。"""

    analysis = ObjectiveAnalysisService(session).analyze(report_id)
    entry_by_id = {entry.entry_id: entry for entry in analysis.entries}

    from sqlalchemy import select

    from flow_api.infrastructure.models.statement import (
        StatementNormalizedItem,
        StatementReport,
    )

    rows = list(
        session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report_id
            )
        )
    )

    role_facts = _facts_with_roles(rows)

    report_for_segments = session.get(StatementReport, report_id)
    segment_series = (
        load_segment_series(report_for_segments.stock_code)
        if report_for_segments is not None
        else None
    )
    operating_metrics = (
        operating_fact_metrics_for_period(
            load_operating_facts(report_for_segments.stock_code),
            selected_period=report_for_segments.period_label,
        )
        if report_for_segments is not None
        else {}
    )

    themes: list[OperationsTheme] = []
    for theme_id in (
        "growth_quality",
        "revenue_structure",
        "cost_structure",
        "profit_quality",
        "users_channels",
        "operational_efficiency",
    ):
        if theme_id == "revenue_structure":
            extra_metrics = operating_metrics.get(theme_id, [])
            if segment_series is not None:
                segment_theme = _segment_revenue_theme(
                    segment_series, selected_period=report_for_segments.period_label
                )
                segment_theme.metrics.extend(extra_metrics)
                if extra_metrics and segment_theme.status == "not_applicable":
                    segment_theme.status = "available"
                themes.append(segment_theme)
            elif extra_metrics:
                themes.append(
                    OperationsTheme(
                        theme_id=theme_id,
                        name=_THEME_NAMES[theme_id],
                        availability="financial_report",
                        status="available",
                        metrics=extra_metrics,
                    )
                )
            else:
                themes.append(
                    OperationsTheme(
                        theme_id=theme_id,
                        name=_THEME_NAMES[theme_id],
                        availability="financial_report",
                        status="not_applicable",
                        reason=THEME_UNAVAILABLE_REASON.get(theme_id),
                        metrics=[],
                    )
                )
            continue
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
        metrics.extend(operating_metrics.get(theme_id, []))
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


__all__ = [
    "OperationsOverview",
    "OperationsSnapshotLine",
    "OperationsSnapshotList",
    "OperationsTheme",
    "PublicOperatingPeriod",
    "PublicOperatingPeriodList",
    "build_public_operating_overview",
    "build_operations_overview",
    "list_public_operating_periods",
    "operating_fact_metrics_for_period",
]
