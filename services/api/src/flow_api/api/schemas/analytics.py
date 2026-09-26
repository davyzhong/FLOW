"""分析实体（MetricSnapshot / AnalysisRun）只读详情响应模型（批次二 §3.2）。

数值与身份全部来自 DB 实体本身，不做投影计算；created_at 以 ISO 秒级字符串跨 JSON。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MetricSnapshotDetailResponse(FrozenResponse):
    """指标快照身份：版本/引擎/定义集/指纹/状态/批次链/期间。"""

    id: str
    batch_id: str
    import_version_id: str
    as_of_period_id: str
    as_of_month_key: int | None = None
    version: int
    engine_version: str
    definition_set_id: str
    definition_set_hash: str
    fingerprint: str
    status: str
    created_at: str | None = None


class AnalysisRunDetailResponse(FrozenResponse):
    """分析运行身份：策略集/引擎/指纹/状态/所属快照。"""

    id: str
    metric_snapshot_id: str
    import_version_id: str
    policy_id: str
    policy_set_hash: str
    engine_version: str
    fingerprint: str
    status: str
    created_at: str | None = None
