"""指标库治理（C04）：草稿 → 验证 → 生效/退役，全程可靠持久化审计。

- 草稿：新定义以 version=当前最大+1、status=draft 进入，不触碰在效定义；
- 验证：非法 AST（未知算子）、循环依赖、引用缺失均阻止生效；
- 生效：验证通过才置 effective；同指标同时在效版本唯一；
- 退役：status=retired，行永不删除；旧定义与旧快照不变；
- 每次动作写 metric_governance_event（操作者/理由/差异），冲突（并发草稿）typed 拒绝。
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.metric_library import (
    MetricDictionaryEntry,
    MetricGovernanceEvent,
    StatementLineMapping,
)

SUPPORTED_FORMULA_OPS = {"identity", "avg", "prior", "div", "sub", "add", "mul", "sum"}
LIFECYCLE = ("draft", "effective", "retired")


class GovernanceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _entry(session: Session, entry_id: UUID) -> MetricDictionaryEntry:
    entry = session.get(MetricDictionaryEntry, entry_id)
    if entry is None:
        raise GovernanceError("entry_not_found", "指定的指标定义不存在")
    return entry


def _record(
    session: Session,
    entry: MetricDictionaryEntry,
    *,
    action: str,
    operator: str,
    reason: str,
    diff: dict[str, Any],
) -> None:
    session.add(
        MetricGovernanceEvent(
            dictionary_id=entry.dictionary_id,
            collection=entry.collection,
            metric_code=entry.metric_code,
            version=entry.version,
            action=action,
            operator=operator,
            reason=reason,
            diff=diff,
        )
    )


def _formula_nodes(node: Any) -> tuple[set[str], set[str], set[str]]:
    """返回（指标引用 code 集合, 报表项目引用集合, 算子集合）。"""

    metric_refs: set[str] = set()
    item_refs: set[str] = set()
    ops: set[str] = set()
    if isinstance(node, dict):
        op = node.get("op")
        if op:
            ops.add(str(op))
        for arg in node.get("args", []):
            sub_m, sub_i, sub_o = _formula_nodes(arg)
            metric_refs |= sub_m
            item_refs |= sub_i
            ops |= sub_o
    elif isinstance(node, str):
        if node.startswith(("bs.", "is.", "cf.", "mpm.")):
            item_refs.add(node)
        else:
            metric_refs.add(node)
    return metric_refs, item_refs, ops


def _validate_definition(session: Session, entry: MetricDictionaryEntry) -> None:
    """生效前验证：非法 AST / 循环依赖 / 引用缺失均 typed 拒绝。"""

    metric_refs, item_refs, ops = _formula_nodes(entry.formula)
    unknown_ops = ops - SUPPORTED_FORMULA_OPS
    if unknown_ops:
        raise GovernanceError(
            "invalid_formula_ast", f"公式含未支持算子：{'、'.join(sorted(unknown_ops))}"
        )
    if item_refs:
        known_items = {
            row
            for row in session.scalars(select(StatementLineMapping.item_id)).all()
        }
        missing_items = item_refs - known_items
        if missing_items:
            raise GovernanceError(
                "missing_reference",
                f"公式引用的报表项目未登记：{'、'.join(sorted(missing_items))}",
            )
    if metric_refs:
        known_metrics = set(
            session.scalars(
                select(MetricDictionaryEntry.metric_code).where(
                    MetricDictionaryEntry.dictionary_id == entry.dictionary_id,
                    MetricDictionaryEntry.status != "retired",
                )
            ).all()
        )
        missing_metrics = metric_refs - known_metrics
        if missing_metrics:
            raise GovernanceError(
                "missing_reference",
                f"公式引用的指标不存在：{'、'.join(sorted(missing_metrics))}",
            )
        # 循环依赖检测（沿 depends_on + 公式引用）
        edges: dict[str, set[str]] = {}
        rows = session.scalars(
            select(MetricDictionaryEntry).where(
                MetricDictionaryEntry.dictionary_id == entry.dictionary_id,
                MetricDictionaryEntry.status != "retired",
            )
        ).all()
        for row in rows:
            refs, _, _ = _formula_nodes(row.formula)
            edges[row.metric_code] = refs | set(row.depends_on or [])
        edges[entry.metric_code] = metric_refs | set(entry.depends_on or [])

        visiting: list[str] = []

        def _dfs(code: str) -> None:
            if code in visiting:
                raise GovernanceError(
                    "circular_dependency",
                    f"指标循环依赖：{' → '.join([*visiting, code])}",
                )
            visiting.append(code)
            for nxt in edges.get(code, ()):
                if nxt in edges:
                    _dfs(nxt)
            visiting.pop()

        _dfs(entry.metric_code)


class MetricGovernance:
    def __init__(self, session: Session) -> None:
        self._session = session

    def draft_change(
        self,
        entry_id: UUID,
        *,
        changes: dict[str, Any],
        operator: str,
        reason: str,
    ) -> MetricDictionaryEntry:
        """以在效定义为基线起草新版本（并发草稿 typed 拒绝）。"""

        base = _entry(self._session, entry_id)
        if base.status != "effective":
            raise GovernanceError("invalid_base", "只能从在效（effective）定义起草新版本")
        pending = self._session.scalar(
            select(MetricDictionaryEntry).where(
                MetricDictionaryEntry.dictionary_id == base.dictionary_id,
                MetricDictionaryEntry.metric_code == base.metric_code,
                MetricDictionaryEntry.status == "draft",
            )
        )
        if pending is not None:
            raise GovernanceError(
                "draft_conflict",
                f"指标 {base.metric_code} 已有未处理草稿 v{pending.version}，先处理再起草",
            )
        latest_version = self._session.scalar(
            select(func.max(MetricDictionaryEntry.version)).where(
                MetricDictionaryEntry.dictionary_id == base.dictionary_id,
                MetricDictionaryEntry.metric_code == base.metric_code,
            )
        ) or 0
        draft = MetricDictionaryEntry(
            dictionary_id=base.dictionary_id,
            collection=base.collection,
            metric_code=base.metric_code,
            version=latest_version + 1,
            status="draft",
            name=base.name,
            domain=base.domain,
            definition=base.definition,
            formula_text=base.formula_text,
            formula=base.formula,
        )
        allowed = {
            "name", "definition", "formula_text", "formula", "unit", "time_behavior",
            "caliber", "default_caliber", "default_basis", "alternative_calibers",
            "source_cas", "source_ifrs", "depends_on", "decompositions", "aliases",
            "benchmark", "reconciliation", "mpm",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise GovernanceError(
                "unknown_field", f"不允许修改的字段：{'、'.join(sorted(unknown))}"
            )
        for key, value in changes.items():
            setattr(draft, key, value)
        self._session.add(draft)
        _record(
            self._session, draft,
            action="draft", operator=operator, reason=reason, diff=changes,
        )
        self._session.flush()
        return draft

    def activate(self, entry_id: UUID, *, operator: str, reason: str) -> MetricDictionaryEntry:
        entry = _entry(self._session, entry_id)
        if entry.status != "draft":
            raise GovernanceError("invalid_transition", "只有草稿可以生效")
        _validate_definition(self._session, entry)
        # 同指标旧在效版本自动退役
        current = self._session.scalars(
            select(MetricDictionaryEntry).where(
                MetricDictionaryEntry.dictionary_id == entry.dictionary_id,
                MetricDictionaryEntry.metric_code == entry.metric_code,
                MetricDictionaryEntry.status == "effective",
                MetricDictionaryEntry.id != entry.id,
            )
        ).all()
        for old in current:
            old.status = "retired"
            _record(
                self._session, old,
                action="retire", operator=operator,
                reason=f"被 v{entry.version} 取代：{reason}", diff={},
            )
        entry.status = "effective"
        _record(
            self._session, entry,
            action="activate", operator=operator, reason=reason, diff={},
        )
        self._session.flush()
        return entry

    def retire(self, entry_id: UUID, *, operator: str, reason: str) -> MetricDictionaryEntry:
        entry = _entry(self._session, entry_id)
        if entry.status == "retired":
            raise GovernanceError("invalid_transition", "定义已退役")
        entry.status = "retired"
        _record(
            self._session, entry,
            action="retire", operator=operator, reason=reason, diff={},
        )
        self._session.flush()
        return entry

    def events(self, metric_code: str | None = None) -> list[MetricGovernanceEvent]:
        query = select(MetricGovernanceEvent).order_by(MetricGovernanceEvent.created_at)
        if metric_code:
            query = query.where(MetricGovernanceEvent.metric_code == metric_code)
        return list(self._session.scalars(query))


__all__ = [
    "GovernanceError",
    "LIFECYCLE",
    "MetricGovernance",
    "SUPPORTED_FORMULA_OPS",
]
