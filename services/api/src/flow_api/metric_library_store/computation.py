"""O-02 AI 计算提议「提议 → 程序复算」服务（D054 原则落地）。

AI 生成的计算只能以「提议」形式进入：提名治理字典中的指标（metric_code）+
实体 + 期间，由确定性沙盒求值器（与影响分析同一条 Decimal 独立实现路径）在
冻结报表事实上复算。复算通过才产生可引用的 verified 结果；任何缺口（未知
指标 / 缺事实 / 零分母 / 未知引用）都是结构化 refusal，绝不编造数值。

边界：本模块完全只读（不写 DB）；审计留痕由路由层追加 JSONL（无新表）。
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.metric_library import MetricDictionaryEntry
from flow_api.metric_library_store.impact import (
    FACTS_PATH,
    ImpactError,
    _load_facts,
    _SandboxEvaluator,
)


@dataclass(frozen=True, slots=True)
class ComputationResult:
    status: str  # verified / refused
    metric_code: str
    entry_id: str | None
    dictionary_id: str | None
    company: str
    period: str
    value: str | None = None
    unit: str | None = None
    formula_text: str | None = None
    referenced_items: tuple[str, ...] = ()
    refusal_code: str | None = None
    refusal_message: str | None = None


def _refs(node: object) -> tuple[set[str], set[str]]:
    metric_refs: set[str] = set()
    item_refs: set[str] = set()
    if isinstance(node, dict):
        for arg in node.get("args", []):
            sub_m, sub_i = _refs(arg)
            metric_refs |= sub_m
            item_refs |= sub_i
    elif isinstance(node, str):
        if node.startswith(("bs.", "is.", "cf.", "mpm.")):
            item_refs.add(node)
        else:
            metric_refs.add(node)
    return metric_refs, item_refs


def computation_inventory() -> dict[str, list[str]]:
    """复算可用事实清单：company → 有事实的期间（升序）。"""
    facts = _load_facts()
    periods: dict[str, set[str]] = {}
    for company, period, _, _ in facts:
        periods.setdefault(company, set()).add(period)
    return {company: sorted(periods[company]) for company in sorted(periods)}


def propose_computation(
    session: Session, metric_code: str, company: str, period: str
) -> ComputationResult:
    """复算一次治理指标的取值；一切缺口都是结构化 refusal，不抛异常。"""
    entry = session.scalar(
        select(MetricDictionaryEntry).where(
            MetricDictionaryEntry.metric_code == metric_code,
            MetricDictionaryEntry.status == "effective",
        )
    )
    if entry is None:
        return ComputationResult(
            status="refused",
            metric_code=metric_code,
            entry_id=None,
            dictionary_id=None,
            company=company,
            period=period,
            refusal_code="unknown_metric",
            refusal_message=f"治理字典中没有 effective 状态的指标：{metric_code}",
        )

    _, item_refs = _refs(entry.formula)
    referenced = tuple(sorted(item_refs))
    # 公式可引用其他治理指标（如 sgr→roe）：复算面 = 全部 effective 条目
    entries = list(
        session.scalars(
            select(MetricDictionaryEntry).where(MetricDictionaryEntry.status == "effective")
        ).all()
    )
    metrics_map = {e.metric_code: e for e in entries}
    base = ComputationResult(
        status="refused",
        metric_code=metric_code,
        entry_id=str(entry.id),
        dictionary_id=entry.dictionary_id,
        company=company,
        period=period,
        formula_text=entry.formula_text,
        unit=entry.unit,
        referenced_items=referenced,
    )
    try:
        facts = _load_facts()
    except ImpactError as error:
        return replace(base, refusal_code="facts_unavailable", refusal_message=error.message)
    evaluator = _SandboxEvaluator(facts)
    try:
        value = evaluator.ev(entry.formula, metrics_map, company, period)
    except ImpactError as error:
        return replace(base, refusal_code=error.code, refusal_message=error.message)
    return replace(base, status="verified", value=str(value))


__all__ = ["FACTS_PATH", "ComputationResult", "computation_inventory", "propose_computation"]
