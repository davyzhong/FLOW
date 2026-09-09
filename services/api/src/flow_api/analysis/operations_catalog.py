"""经营轨主题目录（O1，D050/OP 方法论）。

数据可得性分层是第一原则：主题、事件簿均携带 availability 标注
（financial_report= L1 结果层 / internal_process= L2 过程层 /
internal_events= L3 事件层 / action_loop= L4 行动层，后置）。
数据层不可得 → not_applicable（typed 原因），不返回 0、缺失不补造。
目录只做注册与校验：metric_refs 必须已在指标字典登记（不另建第二套口径）；
计算在 O2 经指标库 facts 与 U2 原语接线，发布走冻结链（OP-6）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Availability = Literal[
    "financial_report", "internal_process", "internal_events", "action_loop"
]


class ThemeEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    theme_id: str
    name: str
    board_slot: int
    availability: Availability
    metric_refs: tuple[str, ...]
    primitives: tuple[str, ...] = ()
    enhanced_by: Availability | None = None
    required_layers: tuple[Availability, ...] = ()
    caliber_note: str = ""
    scope_note: str = ""


class EventBookField(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_name: str
    field_type: str
    allowed: tuple[str, ...] = ()
    scope_note: str = ""


class EventBookContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    availability: Availability
    fields: tuple[EventBookField, ...]
    rules: tuple[str, ...]


class OperationsCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog_id: str
    status: str
    decision_ref: str
    methodology_ref: str = ""
    themes: tuple[ThemeEntry, ...]
    event_book: EventBookContract
    rules: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _theme_ids_unique(self) -> OperationsCatalog:
        seen: set[str] = set()
        for theme in self.themes:
            if theme.theme_id in seen:
                raise ValueError(f"theme_id 重复: {theme.theme_id}")
            seen.add(theme.theme_id)
        return self


def _load_raw(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_operations_catalog(path: str | Path) -> OperationsCatalog:
    return OperationsCatalog.model_validate(_load_raw(path))


def validate_metric_refs(
    catalog: OperationsCatalog, registered_codes: set[str]
) -> list[str]:
    """metric_refs 引用的代码必须已在指标字典登记；返回未知代码。"""

    referenced: set[str] = set()
    for theme in catalog.themes:
        referenced.update(theme.metric_refs)
    return sorted(referenced - registered_codes)


def theme_availability(
    theme: ThemeEntry, *, available_layers: set[str]
) -> dict[str, str]:
    """按已接入数据层判定主题可用性；不可得给 typed 原因，不伪造数值。"""

    if theme.availability in available_layers:
        return {"status": "available", "reason": ""}
    required = set(theme.required_layers) or {theme.availability}
    if required <= available_layers:
        return {"status": "available", "reason": ""}
    return {
        "status": "not_applicable",
        "reason": "internal_data_required"
        if theme.availability != "action_loop"
        else "action_loop_postponed",
    }
