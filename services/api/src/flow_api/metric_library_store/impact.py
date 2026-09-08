"""指标变更影响分析与沙盒试算（C05）。

- 影响遍历：依赖该指标的全部下游（公式引用 + depends_on，传递闭包）与取数映射；
- 沙盒试算：在报表事实库上用 Decimal 独立求值器对比草稿与在效定义，产出数值差异；
- 边界：只读操作，失败试算不写入任何正式数据；已冻结快照与在效定义永不被影响分析改写。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import MetricSnapshot
from flow_api.infrastructure.models.metric_library import (
    MetricDictionaryEntry,
    StatementLineMapping,
)

FACTS_PATH = Path("docs/implementation/p5/statement_facts.yaml")


class ImpactError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class SandboxDiff:
    company: str
    period: str
    current_value: str | None
    draft_value: str | None
    delta: str | None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ImpactReport:
    metric_code: str
    draft_version: int
    downstream_metrics: tuple[str, ...]
    referenced_items: tuple[str, ...]
    frozen_snapshots_untouched: int
    sandbox: tuple[SandboxDiff, ...]


def _refs(node: Any) -> tuple[set[str], set[str]]:
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


def _collect_downstream(
    entries: list[MetricDictionaryEntry], code: str
) -> tuple[str, ...]:
    edges: dict[str, set[str]] = {}
    for entry in entries:
        refs, _ = _refs(entry.formula)
        edges[entry.metric_code] = refs | set(entry.depends_on or [])
    downstream: set[str] = set()
    queue = [code]
    while queue:
        current = queue.pop()
        for candidate, refs in edges.items():
            if current in refs and candidate not in downstream and candidate != code:
                downstream.add(candidate)
                queue.append(candidate)
    return tuple(sorted(downstream))


class _SandboxEvaluator:
    """Decimal 独立求值器：与 scripts/p5_query_facts.py 路径不同实现。"""

    def __init__(self, facts: dict[tuple[str, str, str, str], Decimal]) -> None:
        self.facts = facts

    def item(self, item_id: str, company: str, period: str, role: str | None) -> Decimal:
        if role is None:
            role = "end" if item_id.startswith("bs.") else "cur"
        value = self.facts.get((company, period, item_id, role))
        if value is None:
            raise ImpactError("missing_fact", f"{company}/{period} 缺少 {item_id}({role})")
        return value

    def ev(self, node: Any, metrics: dict[str, Any], company: str, period: str) -> Decimal:
        if isinstance(node, (int, float)):
            return Decimal(str(node))
        if isinstance(node, str):
            if node.startswith(("bs.", "is.", "cf.", "mpm.")):
                return self.item(node, company, period, None)
            if node in metrics:
                formula = metrics[node]
                return self.ev(
                    formula["formula"] if isinstance(formula, dict) else formula.formula,
                    metrics,
                    company,
                    period,
                )
            raise ImpactError("missing_reference", f"未知引用：{node}")
        op, args = node["op"], node["args"]
        if op == "identity":
            return self.ev(args[0], metrics, company, period)
        if op == "avg":
            end = self.item(args[0], company, period, "end")
            open_ = self.item(args[0], company, period, "open")
            return (end + open_) / 2
        if op == "prior":
            role = "open" if args[0].startswith("bs.") else "prev_yoy"
            return self.item(args[0], company, period, role)
        values = [self.ev(arg, metrics, company, period) for arg in args]
        if op == "div":
            if values[1] == 0:
                raise ImpactError("zero_denominator", "分母为零")
            return values[0] / values[1]
        if op == "sub":
            return values[0] - values[1]
        if op in ("add", "sum"):
            return sum(values, Decimal(0))
        if op == "mul":
            result = Decimal(1)
            for value in values:
                result *= value
            return result
        raise ImpactError("invalid_formula_ast", f"未知算子：{op}")


def _load_facts(path: Path = FACTS_PATH) -> dict[tuple[str, str, str, str], Decimal]:
    for root in (Path.cwd(), *Path.cwd().parents):
        full = root / path
        if full.is_file():
            doc = yaml.safe_load(full.read_text())
            facts: dict[tuple[str, str, str, str], Decimal] = {}
            for fact in doc["facts"]:
                facts[(fact["company"], fact["period"], fact["item_id"], fact["role"])] = Decimal(
                    str(fact["value"])
                )
            return facts
    raise ImpactError("facts_not_found", f"事实库不存在：{path}")


class MetricImpactService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def analyze(self, draft_id: UUID) -> ImpactReport:
        draft = self._session.get(MetricDictionaryEntry, draft_id)
        if draft is None:
            raise ImpactError("entry_not_found", "指定的指标定义不存在")
        if draft.status != "draft":
            raise ImpactError("invalid_base", "影响分析只针对草稿版本")

        entries = list(
            self._session.scalars(
                select(MetricDictionaryEntry).where(
                    MetricDictionaryEntry.dictionary_id == draft.dictionary_id,
                    MetricDictionaryEntry.status != "retired",
                )
            ).all()
        )
        current = next(
            (
                entry
                for entry in entries
                if entry.metric_code == draft.metric_code and entry.status == "effective"
            ),
            None,
        )
        downstream = _collect_downstream(entries, draft.metric_code)
        _, item_refs = _refs(draft.formula)
        registered = set(
            self._session.scalars(select(StatementLineMapping.item_id)).all()
        )
        missing = item_refs - registered
        if missing:
            raise ImpactError(
                "missing_reference", f"草稿公式引用未登记报表项目：{'、'.join(sorted(missing))}"
            )

        # 已冻结快照数量仅作只读统计，证明影响分析不触碰历史
        snapshot_count = len(list(self._session.scalars(select(MetricSnapshot.id)).all()))

        # 沙盒试算：草稿 vs 在效（有在效才比）
        sandbox: list[SandboxDiff] = []
        if current is not None:
            facts = _load_facts()
            evaluator = _SandboxEvaluator(facts)
            company_periods = sorted({(c, p) for c, p, _, _ in facts})
            metrics = {entry.metric_code: entry for entry in entries}
            metrics[draft.metric_code] = draft
            for company, period in company_periods:
                diff = self._trial(
                    evaluator, metrics, draft, current, company, period
                )
                if diff is not None:
                    sandbox.append(diff)

        return ImpactReport(
            metric_code=draft.metric_code,
            draft_version=draft.version,
            downstream_metrics=downstream,
            referenced_items=tuple(sorted(item_refs)),
            frozen_snapshots_untouched=snapshot_count,
            sandbox=tuple(sandbox),
        )

    def _trial(
        self,
        evaluator: _SandboxEvaluator,
        metrics: dict[str, Any],
        draft: MetricDictionaryEntry,
        current: MetricDictionaryEntry,
        company: str,
        period: str,
    ) -> SandboxDiff | None:
        try:
            current_value = evaluator.ev(current.formula, metrics, company, period)
        except ImpactError:
            current_value = None
        try:
            draft_value = evaluator.ev(draft.formula, metrics, company, period)
        except ImpactError as error:
            return SandboxDiff(
                company=company,
                period=period,
                current_value=str(current_value) if current_value is not None else None,
                draft_value=None,
                delta=None,
                error=f"{error.code}: {error.message}",
            )
        delta = (
            draft_value - current_value
            if draft_value is not None and current_value is not None
            else None
        )
        return SandboxDiff(
            company=company,
            period=period,
            current_value=str(current_value) if current_value is not None else None,
            draft_value=str(draft_value) if draft_value is not None else None,
            delta=str(delta) if delta is not None else None,
        )


__all__ = ["ImpactError", "ImpactReport", "MetricImpactService", "SandboxDiff"]
