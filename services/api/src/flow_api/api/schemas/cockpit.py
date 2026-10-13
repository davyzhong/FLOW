"""CFO 驾驶舱响应 schema（批次 A）。

契约纪律：
- 复用 Dashboard 的 DashboardValue / DataStatus / DashboardContext（不重复定义）
- 每个 kpi_card 必带 snapshot_id（可追溯铁律；缺失时前端拒绝渲染）
- unavailable 显式表达，不补零、不造数
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from flow_api.dashboard.models import DashboardContext, DashboardValue, DataStatus


class CockpitComparisons(BaseModel):
    yoy: DashboardValue
    mom: DashboardValue
    percentile: DashboardValue


class CockpitKpiCard(BaseModel):
    metric_code: str
    title: str
    category: str
    unit: str
    primary: DashboardValue
    comparisons: CockpitComparisons
    polarity: str = Field(description="positive/negative/neutral：决定比较值着色方向")
    control_status: str = Field(description="ok/near/breach/not_ready")
    control_line: DashboardValue | None = None
    caliber_note: str | None = None
    source_label: str | None = None
    snapshot_id: str = Field(description="可追溯铁律：必填")


class CockpitTrendPoint(BaseModel):
    period: str
    value: float
    display_value: str
    status: str = "ready"


class CockpitTrendSeries(BaseModel):
    key: str
    title: str
    unit: str
    points: list[CockpitTrendPoint]


class CockpitTrend(BaseModel):
    status: str
    unit: str
    series: list[CockpitTrendSeries] = Field(default_factory=list)
    degradation_message: str | None = None


class CockpitConclusionFinding(BaseModel):
    id: str
    title: str
    investigation_path: str


class CockpitConclusion(BaseModel):
    text: str
    findings: list[CockpitConclusionFinding] = Field(default_factory=list)
    tone: str = "neutral"


class CockpitOverviewResponse(BaseModel):
    state: str
    context: DashboardContext
    data_status: DataStatus
    kpi_cards: list[CockpitKpiCard] = Field(default_factory=list)
    trends: list[CockpitTrend] = Field(default_factory=list)
    conclusion: CockpitConclusion
    source_notice: str | None = None
