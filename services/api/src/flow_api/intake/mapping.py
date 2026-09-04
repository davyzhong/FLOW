from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from flow_api.data_contract.models import FieldContract, SheetContract, WorkbookContract
from flow_api.intake.models import ColumnProfile, SheetProfile, WorkbookProfile

MappingConfidence = Literal["high", "medium", "low"]
MappingMethod = Literal[
    "stable_field_id",
    "display_name",
    "registered_alias",
    "compatible_type",
    "ai_suggestion",
    "manual_override",
]
NON_DATA_SHEET_IDS = frozenset({"instructions"})


@dataclass(frozen=True, slots=True)
class AliasRegistry:
    contract_version: str
    sheet_aliases: dict[str, tuple[str, ...]]
    field_aliases: dict[str, dict[str, tuple[str, ...]]]


@dataclass(frozen=True, slots=True)
class FieldMapping:
    source_header: str
    source_column: str
    target_field_id: str
    method: MappingMethod
    score: float
    confidence: MappingConfidence
    requires_confirmation: bool
    rationale: str


@dataclass(frozen=True, slots=True)
class SheetMapping:
    source_sheet: str
    target_sheet_id: str
    method: str
    score: float
    fields: tuple[FieldMapping, ...]
    unresolved_required_fields: tuple[str, ...]
    ignored_source_headers: tuple[str, ...]

    def get_field(self, target_field_id: str) -> FieldMapping:
        try:
            return next(field for field in self.fields if field.target_field_id == target_field_id)
        except StopIteration as error:
            raise KeyError(target_field_id) from error


@dataclass(frozen=True, slots=True)
class MappingProposal:
    contract_version: str
    source_sha256: str
    sheets: tuple[SheetMapping, ...]
    unresolved_sheet_ids: tuple[str, ...]
    ignored_source_sheets: tuple[str, ...]

    def get_sheet(self, target_sheet_id: str) -> SheetMapping:
        try:
            return next(sheet for sheet in self.sheets if sheet.target_sheet_id == target_sheet_id)
        except StopIteration as error:
            raise KeyError(target_sheet_id) from error

    @property
    def mapping_hash(self) -> str:
        payload = json.dumps(
            asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class MappingOverride:
    """Finance BP 对单个目标字段的手工映射修正。"""

    target_sheet_id: str
    target_field_id: str
    source_sheet: str
    source_header: str


def proposal_from_spec(spec: Mapping[str, Any]) -> MappingProposal:
    """从 MappingVersion.mapping_spec（asdict 快照）重建提案对象。"""
    sheets = tuple(
        SheetMapping(
            source_sheet=sheet["source_sheet"],
            target_sheet_id=sheet["target_sheet_id"],
            method=sheet["method"],
            score=sheet["score"],
            fields=tuple(FieldMapping(**field) for field in sheet["fields"]),
            unresolved_required_fields=tuple(sheet["unresolved_required_fields"]),
            ignored_source_headers=tuple(sheet["ignored_source_headers"]),
        )
        for sheet in spec["sheets"]
    )
    return MappingProposal(
        contract_version=spec["contract_version"],
        source_sha256=spec["source_sha256"],
        sheets=sheets,
        unresolved_sheet_ids=tuple(spec["unresolved_sheet_ids"]),
        ignored_source_sheets=tuple(spec["ignored_source_sheets"]),
    )


def _tuple_strings(value: Any, location: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{location} must be a non-empty string list")
    return tuple(value)


def load_aliases(path: str | Path) -> AliasRegistry:
    payload: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sheets"), dict):
        raise ValueError("alias registry must contain a sheets mapping")
    sheet_aliases: dict[str, tuple[str, ...]] = {}
    field_aliases: dict[str, dict[str, tuple[str, ...]]] = {}
    for sheet_id, raw_sheet in payload["sheets"].items():
        if not isinstance(sheet_id, str) or not isinstance(raw_sheet, dict):
            raise ValueError("invalid alias sheet entry")
        sheet_aliases[sheet_id] = _tuple_strings(raw_sheet.get("aliases"), f"{sheet_id}.aliases")
        raw_fields = raw_sheet.get("fields")
        if not isinstance(raw_fields, dict):
            raise ValueError(f"{sheet_id}.fields must be a mapping")
        field_aliases[sheet_id] = {
            field_id: _tuple_strings(aliases, f"{sheet_id}.{field_id}")
            for field_id, aliases in raw_fields.items()
            if isinstance(field_id, str)
        }
    contract_version = payload.get("contract_version")
    if not isinstance(contract_version, str):
        raise ValueError("alias registry requires contract_version")
    return AliasRegistry(contract_version, sheet_aliases, field_aliases)


def _normalize(value: str) -> str:
    return re.sub(r"[\s_\-—:：]", "", value).casefold()


def _source_type_compatible(column: ColumnProfile, field: FieldContract) -> bool:
    expected: dict[str, set[str]] = {
        "string": {"text", "integer", "decimal"},
        "enum": {"text"},
        "integer": {"integer", "decimal"},
        "decimal": {"integer", "decimal"},
        "month": {"month", "text"},
        "datetime": {"datetime", "date", "text"},
    }
    return column.inferred_type in expected[field.data_type]


def _unique(candidates: list[ColumnProfile]) -> ColumnProfile | None:
    return candidates[0] if len(candidates) == 1 else None


def _field_match(
    sheet: SheetContract,
    source: SheetProfile,
    target: FieldContract,
    aliases: AliasRegistry,
    used_headers: set[str],
) -> FieldMapping | None:
    available = [column for column in source.columns if column.header not in used_headers]
    methods: tuple[tuple[MappingMethod, float, list[ColumnProfile], str], ...] = (
        (
            "stable_field_id",
            1.0,
            [column for column in available if column.stable_field_id == target.field_id],
            "源工作簿提供了与契约一致的稳定字段 ID。",
        ),
        (
            "display_name",
            0.96,
            [
                column
                for column in available
                if _normalize(column.header) == _normalize(target.display_name)
            ],
            "源表头与契约显示名称一致。",
        ),
        (
            "registered_alias",
            0.92,
            [
                column
                for column in available
                if _normalize(column.header)
                in {
                    _normalize(alias)
                    for alias in aliases.field_aliases.get(sheet.sheet_id, {}).get(
                        target.field_id, ()
                    )
                }
            ],
            "源表头命中已版本化登记别名。",
        ),
    )
    for method, score, candidates, rationale in methods:
        selected = _unique(candidates)
        if selected is not None:
            return FieldMapping(
                source_header=selected.header,
                source_column=selected.column_letter,
                target_field_id=target.field_id,
                method=method,
                score=score,
                confidence="high",
                requires_confirmation=False,
                rationale=rationale,
            )

    compatible = [column for column in available if _source_type_compatible(column, target)]
    selected = _unique(compatible)
    if selected is None:
        return None
    return FieldMapping(
        source_header=selected.header,
        source_column=selected.column_letter,
        target_field_id=target.field_id,
        method="compatible_type",
        score=0.55,
        confidence="low",
        requires_confirmation=True,
        rationale="只有一个未使用源字段具有兼容类型，仍需人工确认业务语义。",
    )


def _sheet_source(
    sheet: SheetContract, profile: WorkbookProfile, aliases: AliasRegistry, used: set[str]
) -> tuple[SheetProfile, str, float] | None:
    exact = [
        source
        for source in profile.sheets
        if source.name == sheet.sheet_name and source.name not in used
    ]
    if len(exact) == 1:
        return exact[0], "contract_sheet_name", 1.0
    registered = {_normalize(alias) for alias in aliases.sheet_aliases.get(sheet.sheet_id, ())}
    matched = [
        source
        for source in profile.sheets
        if source.name not in used and _normalize(source.name) in registered
    ]
    if len(matched) == 1:
        return matched[0], "registered_alias", 0.95
    return None


def propose_mapping(
    profile: WorkbookProfile, contract: WorkbookContract, aliases: AliasRegistry
) -> MappingProposal:
    if aliases.contract_version != contract.contract_version:
        raise ValueError("alias registry and workbook contract versions differ")
    mapped_sheets: list[SheetMapping] = []
    unresolved_sheets: list[str] = []
    used_source_sheets: set[str] = set()
    for sheet in contract.sheets:
        if sheet.sheet_id in NON_DATA_SHEET_IDS:
            continue
        source_match = _sheet_source(sheet, profile, aliases, used_source_sheets)
        if source_match is None:
            unresolved_sheets.append(sheet.sheet_id)
            continue
        source, method, score = source_match
        used_source_sheets.add(source.name)
        fields: list[FieldMapping] = []
        used_headers: set[str] = set()
        unresolved_required: list[str] = []
        for target in sheet.fields:
            mapping = _field_match(sheet, source, target, aliases, used_headers)
            if mapping is None:
                if target.required:
                    unresolved_required.append(target.field_id)
                continue
            fields.append(mapping)
            used_headers.add(mapping.source_header)
        mapped_sheets.append(
            SheetMapping(
                source_sheet=source.name,
                target_sheet_id=sheet.sheet_id,
                method=method,
                score=score,
                fields=tuple(fields),
                unresolved_required_fields=tuple(unresolved_required),
                ignored_source_headers=tuple(
                    column.header for column in source.columns if column.header not in used_headers
                ),
            )
        )
    return MappingProposal(
        contract_version=contract.contract_version,
        source_sha256=profile.sha256,
        sheets=tuple(mapped_sheets),
        unresolved_sheet_ids=tuple(unresolved_sheets),
        ignored_source_sheets=tuple(
            source.name for source in profile.sheets if source.name not in used_source_sheets
        ),
    )
