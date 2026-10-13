"""CFO 驾驶舱投影服务（批次 A）。

设计依据：docs/05_design/2026-09-29-cfo-cockpit-design.md（approved v0.6）
- §5 四段式（指标卡 → 趋势与结构 → 归因排名 → 结论与行动）
- §9-Q4 三基准（同比 + 环比 + 行业分位）；预算/环比/行业分位属内部期或批次 C，
  显式 unavailable 而非补零（D054：不可伪造缺失事实）
- §9「可追溯」铁律：每个 KPI 必带 metric_snapshot_id，缺失者前端拒绝渲染

本模块**只做投影转换**，不重复查询、不重算指标：数据全部来自
DashboardService.get_overview（同一批已冻结事实）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from flow_api.dashboard.models import ActiveFilters, DashboardOverview
from flow_api.dashboard.service import DashboardService


class CockpitProjectionError(RuntimeError):
    code = "cockpit_projection_failed"


@dataclass(frozen=True)
class CockpitKpi:
    metric_code: str
    title: str
    category: str
    unit: str
    primary: dict[str, Any]
    comparisons: dict[str, dict[str, Any]]
    polarity: str
    control_status: str
    control_line: dict[str, Any] | None
    caliber_note: str | None
    source_label: str | None
    snapshot_id: str


@dataclass(frozen=True)
class CockpitTrendSeries:
    key: str
    title: str
    unit: str
    points: list[dict[str, Any]]


@dataclass(frozen=True)
class CockpitTrendProjection:
    status: str
    unit: str
    series: list[CockpitTrendSeries]
    degradation_message: str | None


@dataclass(frozen=True)
class CockpitConclusionProjection:
    text: str
    findings: list[dict[str, str]]
    tone: str


@dataclass(frozen=True)
class CockpitOverviewProjection:
    state: str
    context: dict[str, Any]
    data_status: dict[str, Any]
    kpi_cards: list[CockpitKpi]
    # 单元素列表（结构预留多面板，批次 C 扩展）
    trends: list[CockpitTrendProjection]
    conclusion: CockpitConclusionProjection
    source_notice: str | None


# 指标极性：决定比较值着色方向（费用率下降是好事，不能一律「上升=绿」）
_NEGATIVE_EXACT = {
    "expense_ratio",
    "period_expense_ratio",
    "debt_ratio",
    "asset_debt_ratio",
    "ccc",
    "dso",
    "dio",
    "interest_bearing_debt",
}
_NEGATIVE_KEYWORDS = ("expense", "cost", "debt", "ratio_days", "_dso", "_dio", "ccc")


def _polarity(metric_code: str) -> str:
    if metric_code in _NEGATIVE_EXACT:
        return "negative"
    if any(word in metric_code for word in _NEGATIVE_KEYWORDS):
        return "negative"
    return "positive"


def _decimal(value: Any) -> Decimal | None:
    """DashboardValue.exact_value 是字符串（如 "-0.0940"）；不可解析返回 None。"""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _as_value_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        dumped: dict[str, Any] = value.model_dump(mode="json")
        return dumped
    return {
        "status": "unavailable",
        "display_value": "—",
        "unavailable_code": "not_projected",
        "unavailable_message": "该基准在驾驶舱首版未投影",
        "semantic_direction": "neutral",
    }


def _unavailable(code: str, message: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "exact_value": None,
        "display_value": "—",
        "unavailable_code": code,
        "unavailable_message": message,
        "semantic_direction": "neutral",
    }


def _control_status(
    value: dict[str, Any], control_line: dict[str, Any] | None, polarity: str
) -> str:
    """管控线状态：红=突破 / 黄=接近(80%-100%) / 绿=正常 / 灰=未就绪。

    无管控线或值不可用时返回 not_ready（灰态），不假装正常。
    """
    if value.get("status") != "ready" or not control_line:
        return "not_ready"
    if control_line.get("status") != "ready":
        return "not_ready"
    raw = _decimal(value.get("exact_value"))
    line = _decimal(control_line.get("exact_value"))
    if raw is None or line is None or line == 0:
        return "not_ready"
    if polarity == "negative":
        # 越低越好：超过管控线 = 突破；达到 80% = 接近
        ratio = abs(raw / line)
        if ratio > 1:
            return "breach"
        if ratio >= Decimal("0.8"):
            return "near"
        return "ok"
    # 越高越好：低于管控线 = 突破；达到 120% = 接近
    ratio = abs(raw / line)
    if ratio < 1:
        return "breach"
    if ratio < Decimal("1.2"):
        return "near"
    return "ok"


_TREND_SERIES = (
    ("revenue", "营业收入"),
    ("operating_profit", "营业利润"),
    ("gross_margin", "毛利率"),
    ("operating_cash_flow", "经营现金流"),
)


class CockpitProjectionService:
    """把 DashboardOverview 投影为驾驶舱四段式结构（不重算、不补零）。"""

    def __init__(self, dashboard: DashboardService | None = None) -> None:
        self._dashboard = dashboard or DashboardService()

    def overview(
        self,
        session: Session,
        *,
        filters: ActiveFilters,
        source_notice: str | None = None,
        now: datetime | None = None,
    ) -> CockpitOverviewProjection:
        base: DashboardOverview = self._dashboard.get_overview(
            session, filters=filters, now=now or datetime.now(UTC)
        )
        snapshot_id = str(base.context.metric_snapshot_id or "")
        return CockpitOverviewProjection(
            state=base.state,
            context=base.context.model_dump(mode="json"),
            data_status=base.data_status.model_dump(mode="json"),
            kpi_cards=[self._kpi(card, snapshot_id) for card in base.metric_cards],
            trends=self._trends(base),
            conclusion=self._conclusion(base),
            source_notice=source_notice,
        )

    def _kpi(self, card: Any, snapshot_id: str) -> CockpitKpi:
        metric_code = card.metric_code
        polarity = _polarity(metric_code)
        primary = _as_value_dict(card.primary)
        # YTD 预算作为管控线参照（公开期通常 unavailable → 状态为 not_ready 灰态）
        control_line = _as_value_dict(card.ytd_budget) if card.ytd_budget else None
        yoy = _as_value_dict(card.yoy) if card.yoy else _unavailable(
            "yoy_not_published", "同比未发布"
        )
        return CockpitKpi(
            metric_code=metric_code,
            title=card.title,
            category=card.category,
            unit=card.unit,
            primary=primary,
            comparisons={
                "yoy": yoy,
                "mom": _unavailable(
                    "mom_not_projected",
                    "环比基准属批次 C（需逐月冻结事实对齐）",
                ),
                "percentile": _unavailable(
                    "industry_percentile_not_projected",
                    "行业分位需 16 行业参考包，批次 C 接入",
                ),
            },
            polarity=polarity,
            control_status=_control_status(primary, control_line, polarity),
            control_line=(
                control_line
                if control_line and control_line.get("status") == "ready"
                else None
            ),
            caliber_note=f"{card.title}（{card.category}）· 由指标字典 v1.2 计算，口径随图附",
            source_label=(
                f"同比 {yoy['display_value']}" if yoy.get("status") == "ready" else "同比未就绪"
            ),
            snapshot_id=snapshot_id,
        )

    def _trends(self, base: DashboardOverview) -> list[CockpitTrendProjection]:
        trend = base.trends
        series: list[CockpitTrendSeries] = []
        for key, title in _TREND_SERIES:
            points: list[dict[str, Any]] = []
            for point in trend.points:
                value = _as_value_dict(getattr(point, key, None))
                exact = _decimal(value.get("exact_value"))
                points.append(
                    {
                        "period": point.month,
                        "value": float(exact) if exact is not None else 0.0,
                        "display_value": value.get("display_value", "—"),
                        "status": str(value.get("status", "unavailable")),
                        "unit": str(value.get("unit", "")),
                    }
                )
            if points:
                unit = points[0].get("unit", "")
                series.append(
                    CockpitTrendSeries(
                        key=key, title=title, unit=unit, points=points
                    )
                )
        return [
            CockpitTrendProjection(
                status=trend.status,
                unit=series[0].unit if series else "",
                series=series,
                degradation_message=trend.degradation_message,
            )
        ]

    def _conclusion(self, base: DashboardOverview) -> CockpitConclusionProjection:
        """结论条：只由已冻结 Finding 生成，不接受裸文本入参（D054）。"""
        findings: list[dict[str, str]] = [
            {
                "id": str(item.finding_id),
                "title": item.title,
                "investigation_path": item.investigation_path,
            }
            for item in base.findings[:3]
        ]
        if not findings:
            return CockpitConclusionProjection(
                text="本期无已终审结论；不补造经营判断。",
                findings=[],
                tone="neutral",
            )
        # 色调由 Finding 影响值的语义方向决定（impact 已带 semantic_direction）
        risky = [f for f in base.findings[:3] if f.impact.semantic_direction == "negative"]
        if len(risky) >= 2:
            tone = "risk"
        elif risky:
            tone = "attention"
        else:
            tone = "neutral"
        titles = "、".join(item.title for item in base.findings[:2])
        return CockpitConclusionProjection(
            text=f"本期关注 {len(findings)} 项已终审发现：{titles}。",
            findings=findings,
            tone=tone,
        )


__all__ = [
    "CockpitConclusionProjection",
    "CockpitKpi",
    "CockpitOverviewProjection",
    "CockpitProjectionError",
    "CockpitProjectionService",
    "CockpitTrendProjection",
    "CockpitTrendSeries",
]
