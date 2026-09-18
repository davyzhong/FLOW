"""O-01 指标字典语义上下文编译器。

把指标库（定义/公式/口径/基准/执行绑定）编译为 AI 代理可引用的语义上下文。
映射依据（借鉴 #21 指标四元素，docs/40_specs/metrics/README.md 设计输入）：
- 对象：metric_code / name / domain / definition（指标衡量的主体）；
- 维度：analysis_dimensions（可分析的细分视角）；
- 限定：caliber / default_caliber / alternative_calibers / benchmark（消除口径二义性）；
- 值：formula_text / unit / depends_on + 执行绑定（确定性计算定义）。

「AI 回答可追溯至口径」的合同：每次计算引用必须携带 entry_id + metric_code +
collection（entry_id 缺失 = YAML-only 条目，如实置空，不得伪造）。
"""

from __future__ import annotations

from flow_api.api.schemas.metric_library import (
    MetricLibraryResponse,
    SemanticContextResponse,
    SemanticMetricContext,
    SemanticObject,
    SemanticQualifications,
    SemanticValue,
)


def build_semantic_context(
    payload: MetricLibraryResponse,
    codes: list[str] | None = None,
) -> SemanticContextResponse:
    """从指标库载荷编译语义上下文；codes 非空时按 metric_code 过滤（保序）。"""
    wanted = set(codes) if codes else None
    metrics = [
        SemanticMetricContext(
            metric_code=metric.metric_code,
            name=metric.name,
            collection=metric.collection,
            domain=metric.domain,
            entry_id=metric.entry_id,
            status=metric.status,
            object=SemanticObject(definition=metric.definition),
            dimensions=list(metric.analysis_dimensions or []),
            qualifications=SemanticQualifications(
                caliber=metric.caliber,
                default_caliber=metric.default_caliber,
                default_basis=metric.default_basis,
                alternative_calibers=list(metric.alternative_calibers or []),
                benchmark=metric.benchmark,
            ),
            value=SemanticValue(
                formula_text=metric.formula_text,
                unit=metric.unit,
                depends_on=list(metric.depends_on or []),
                execution_kind=metric.execution_kind,
                execution_detail=metric.execution_detail,
            ),
        )
        for metric in payload.metrics
        if wanted is None or metric.metric_code in wanted
    ]
    return SemanticContextResponse(
        dictionary_id=payload.dictionary_id,
        metric_count=len(metrics),
        metrics=metrics,
    )


__all__ = ["build_semantic_context"]
