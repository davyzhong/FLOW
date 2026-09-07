"""客观财务分析引擎（D01）。

从归一化报表事实计算目录条目：结构、趋势、同比、比率、杜邦分解。
原则：数据不足显式 not_computable（typed 原因）；不生成业务因果；每条结果携带
值、比较基准、口径与来源项目引用。所有金额 Decimal。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementNormalizedItem,
    StatementReport,
)

CATALOG_PATH = Path("config/analysis/objective_finance_v1.yaml")


class ObjectiveStatus(StrEnum):
    COMPUTED = "computed"
    NOT_COMPUTABLE = "not_computable"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ObjectiveEntryResult:
    entry_id: str
    name: str
    kind: str
    status: ObjectiveStatus
    value: str | None
    basis: str
    caliber_note: str
    refs: tuple[str, ...]
    reason: str | None = None
    parts: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ObjectiveAnalysisResult:
    report_id: str
    catalog_id: str
    entries: tuple[ObjectiveEntryResult, ...]


def load_objective_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    for root in (Path.cwd(), *Path.cwd().parents):
        full = root / path
        if full.is_file():
            data: dict[str, Any] = yaml.safe_load(full.read_text())
            return data
    raise FileNotFoundError(f"分析目录不存在：{path}")


class ObjectiveAnalysisService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def analyze(
        self, report_id: Any, *, mapping_version: str | None = None
    ) -> ObjectiveAnalysisResult:
        report = self._session.get(StatementReport, report_id)
        if report is None:
            raise ValueError("statement_report_not_found")
        if mapping_version is None:
            from flow_api.statements.normalization import load_alias_map

            mapping_version = str(load_alias_map().get("version", "v0"))
        items = self._session.scalars(
            select(StatementNormalizedItem).where(
                StatementNormalizedItem.report_id == report.id,
                StatementNormalizedItem.mapping_version == mapping_version,
            )
        ).all()
        facts: dict[tuple[str, str], Decimal] = {}
        for item in items:
            if item.item_id is None:
                continue
            for column, role in (
                ("value_end", "end"), ("value_begin", "open"),
                ("value_current", "cur"), ("value_prior", "prev_yoy"),
            ):
                value = getattr(item, column)
                if value is not None:
                    facts[(item.item_id, role)] = value

        catalog = load_objective_catalog()
        results = [
            self._compute_entry(entry, facts) for entry in catalog["entries"]
        ]
        return ObjectiveAnalysisResult(
            report_id=str(report.id),
            catalog_id=catalog["catalog_id"],
            entries=tuple(results),
        )

    def _value(self, facts: dict[tuple[str, str], Decimal], item: str, role: str) -> Decimal | None:
        return facts.get((item, role))

    def _compute_entry(
        self, entry: dict[str, Any], facts: dict[tuple[str, str], Decimal]
    ) -> ObjectiveEntryResult:
        kind = entry["kind"]
        basis = entry.get("basis", "")
        note = entry.get("scope_note", "")
        refs = tuple(self._entry_refs(entry))
        if kind == "structure":
            return self._structure(entry, facts, basis, note, refs)
        if kind in ("yoy", "trend"):
            return self._ratio_pair(entry, facts, basis, note, refs)
        if kind == "dupont":
            return self._dupont(entry, facts, basis, note, refs)
        # ratio with formula_ref：在事实层按目录声明的分子分母求值
        return self._ratio_pair(entry, facts, basis, note, refs)

    def _entry_refs(self, entry: dict[str, Any]) -> list[str]:
        refs: list[str] = []
        for key in ("numerator", "denominator"):
            node = entry.get(key)
            if isinstance(node, dict) and node.get("item"):
                refs.append(f"{node['item']}({node.get('role', 'cur')})")
        for item in entry.get("items", []):
            refs.append(str(item))
        if entry.get("formula_ref"):
            refs.append(f"metric:{entry['formula_ref']}")
        return refs

    def _structure(
        self, entry: dict[str, Any], facts: dict[tuple[str, str], Decimal],
        basis: str, note: str, refs: tuple[str, ...],
    ) -> ObjectiveEntryResult:
        denominator = self._value(facts, entry["denominator"], "end")
        if denominator is None:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_COMPUTABLE,
                None, basis, note, refs, reason="missing_operand: 分母缺失",
            )
        if denominator == 0:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_COMPUTABLE,
                None, basis, note, refs, reason="zero_denominator",
            )
        parts = []
        for item in entry["items"]:
            value = self._value(facts, item, "end")
            if value is None:
                parts.append({"item": item, "share": "", "note": "not_disclosed"})
                continue
            share = value / denominator
            parts.append({"item": item, "share": str(share)})
        return ObjectiveEntryResult(
            entry["id"], entry["name"], entry["kind"], ObjectiveStatus.COMPUTED,
            None, basis, note, refs, parts=tuple(parts),
        )

    def _ratio_pair(
        self, entry: dict[str, Any], facts: dict[tuple[str, str], Decimal],
        basis: str, note: str, refs: tuple[str, ...],
    ) -> ObjectiveEntryResult:
        numerator_spec = entry.get("numerator")
        denominator_spec = entry.get("denominator")
        if not numerator_spec or not denominator_spec:
            # formula_ref 条目在 D02 统一快照接通库内执行；此处如实标注
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_APPLICABLE,
                None, basis, note, refs,
                reason="formula_ref 条目由 D02 统一分析快照执行；本服务不重复计算",
            )
        numerator = self._value(
            facts, numerator_spec["item"], numerator_spec.get("role", "cur")
        )
        denominator = self._value(
            facts, denominator_spec["item"], denominator_spec.get("role", "cur")
        )
        if numerator is None or denominator is None:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_COMPUTABLE,
                None, basis, note, refs, reason="missing_operand",
            )
        if denominator == 0:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_COMPUTABLE,
                None, basis, note, refs, reason="zero_denominator",
            )
        if denominator < 0:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.COMPUTED,
                str(numerator / denominator), basis, note + "（分母为负，符号如实保留）", refs,
            )
        value = numerator / denominator
        if entry["kind"] == "yoy":
            value = value - 1
        return ObjectiveEntryResult(
            entry["id"], entry["name"], entry["kind"], ObjectiveStatus.COMPUTED,
            str(value), basis, note, refs,
        )

    def _dupont(
        self, entry: dict[str, Any], facts: dict[tuple[str, str], Decimal],
        basis: str, note: str, refs: tuple[str, ...],
    ) -> ObjectiveEntryResult:
        # ROE = 净利率 × 总资产周转率 × 权益乘数（期末口径）
        net_profit = self._value(facts, "is.net_profit", "cur")
        revenue = self._value(facts, "is.revenue", "cur")
        assets = self._value(facts, "bs.total_assets", "end")
        equity = self._value(facts, "bs.equity", "end")
        missing = [
            name
            for name, value in (
                ("is.net_profit", net_profit), ("is.revenue", revenue),
                ("bs.total_assets", assets), ("bs.equity", equity),
            )
            if value is None
        ]
        if missing:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_COMPUTABLE,
                None, basis, note, refs, reason=f"missing_operand: {'、'.join(missing)}",
            )
        assert (
            net_profit is not None and revenue is not None
            and assets is not None and equity is not None
        )
        if revenue == 0 or assets == 0 or equity == 0:
            return ObjectiveEntryResult(
                entry["id"], entry["name"], entry["kind"], ObjectiveStatus.NOT_COMPUTABLE,
                None, basis, note, refs, reason="zero_denominator",
            )
        net_margin = net_profit / revenue
        turnover = revenue / assets
        multiplier = assets / equity
        roe = net_margin * turnover * multiplier
        parts = [
            {"factor": "net_margin", "value": str(net_margin)},
            {"factor": "total_asset_turnover", "value": str(turnover)},
            {"factor": "equity_multiplier", "value": str(multiplier)},
            {"factor": "roe(期末口径,未年化)", "value": str(roe)},
        ]
        return ObjectiveEntryResult(
            entry["id"], entry["name"], entry["kind"], ObjectiveStatus.COMPUTED,
            str(roe), basis, note, refs, parts=tuple(parts),
        )


__all__ = [
    "CATALOG_PATH",
    "ObjectiveAnalysisResult",
    "ObjectiveAnalysisService",
    "ObjectiveEntryResult",
    "ObjectiveStatus",
    "load_objective_catalog",
]
