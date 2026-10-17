"""CFO 驾驶舱响应 schema（批次 A）。

契约纪律：
- 复用 Dashboard 的 DashboardValue / DataStatus / DashboardContext（不重复定义）
- 每个 kpi_card 必带 snapshot_id（可追溯铁律；缺失时前端拒绝渲染）
- unavailable 显式表达，不补零、不造数
"""

from __future__ import annotations

from typing import Any

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


class CockpitActionItemCreate(BaseModel):
    """行动项创建（B4）：从 Finding 派生的财务结论闭环载体。"""

    finding_id: str = Field(description="来源 Finding id（必须属于本企业且已终审）")
    snapshot_id: str = Field(description="关联指标快照 id（可追溯铁律）")
    title: str = Field(min_length=1, max_length=200)
    detail: str | None = None


class CockpitActionItemResponse(BaseModel):
    id: str
    finding_id: str
    snapshot_id: str
    title: str
    detail: str | None = None
    created_by: str
    created_at: str
    acknowledgment: str = Field(
        description=(
            "闭环语义：确认动作只写 durable AuditEvent（不改业务行）；"
            "本字段固定指向审计凭证语义"
        )
    )


class CockpitActionItemAcknowledgeResponse(BaseModel):
    id: str
    acknowledged_via: str = Field(default="audit_event")
    message: str = Field(
        default=(
            "确认已记入 durable 审计（allow 决策即凭证，resource_id=行动项 id）；"
            "业务行不可变"
        )
    )


class CockpitModuleResponse(BaseModel):
    """模块页聚合响应（批次 C-2）：一次返回该模块 KPI + 图表 + 降级块（禁 N+1）。"""

    module: str
    title: str
    period: str
    prior_period: str
    snapshot_id: str
    report_ids: list[str] = Field(default_factory=list)
    source_notice: str | None = None
    unit: str = "百万元"
    kpis: list[dict[str, Any]] = Field(default_factory=list)
    charts: dict[str, Any] = Field(default_factory=dict)
    unavailable: list[dict[str, Any]] = Field(default_factory=list)


class CockpitProfitabilitySourceFact(BaseModel):
    item_id: str | None = None
    row_id: str | None = None
    statement_type: str | None = None
    item_name: str | None = None
    page_number: int | None = None
    page_anchor: str | None = None
    role: str | None = None
    value: str | None = None


class CockpitProfitabilityMetric(BaseModel):
    metric_code: str
    status: str
    value: str | None = None
    unit: str | None = None
    formula: str | None = None
    definition_version: str | None = None
    reason: str | None = None
    report_id: str
    snapshot_id: str | None = None
    source_facts: list[CockpitProfitabilitySourceFact] = Field(default_factory=list)


class CockpitProfitabilityPeriod(BaseModel):
    period: str
    report_id: str
    snapshot_id: str | None = None
    snapshot_version: int | None = None
    source_ref: str
    source_sha256: str | None = None
    metrics: list[CockpitProfitabilityMetric] = Field(default_factory=list)
    consistency: dict[str, str | None] = Field(default_factory=dict)


class CockpitProfitabilityResponse(BaseModel):
    module: str = "profitability"
    title: str = "盈利能力与杜邦分析"
    source_notice: str
    periods: list[CockpitProfitabilityPeriod] = Field(default_factory=list)
    unavailable: list[dict[str, str]] = Field(default_factory=list)


class CockpitOverviewResponse(BaseModel):
    state: str
    context: DashboardContext
    data_status: DataStatus
    kpi_cards: list[CockpitKpiCard] = Field(default_factory=list)
    trends: list[CockpitTrend] = Field(default_factory=list)
    conclusion: CockpitConclusion
    source_notice: str | None = None
