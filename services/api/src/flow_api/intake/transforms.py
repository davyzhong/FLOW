from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

import yaml

from flow_api.data_contract.models import DataType, FieldContract

MONTH_PATTERN = re.compile(r"^(\d{4})(?:-|/|年)(0[1-9]|1[0-2])月?$")
INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
TransformStatus = Literal["unchanged", "transformed", "failed"]


class TransformError(ValueError):
    """A source value cannot be converted without ambiguity or loss."""


@dataclass(frozen=True, slots=True)
class TransformRule:
    rule_id: str
    version: int
    target_type: DataType


@dataclass(frozen=True, slots=True)
class TransformResult:
    raw_value: Any
    value: Any
    rule_id: str
    rule_version: int
    status: TransformStatus
    reason: str


@dataclass(frozen=True, slots=True)
class TransformRegistry:
    transform_version: str
    rules: dict[DataType, TransformRule]
    null_rule_id: str
    null_rule_version: int

    def for_field(self, field: FieldContract) -> TransformRule:
        return self.rules[field.data_type]


def load_transform_rules(path: str | Path) -> TransformRegistry:
    payload: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("rules"), dict):
        raise ValueError("transform registry requires a rules mapping")
    raw_null = payload.get("null_rule")
    if not isinstance(raw_null, dict):
        raise ValueError("transform registry requires null_rule")
    rules: dict[DataType, TransformRule] = {}
    for data_type in ("string", "enum", "integer", "decimal", "month", "datetime"):
        raw_rule = payload["rules"].get(data_type)
        if not isinstance(raw_rule, dict):
            raise ValueError(f"missing transform rule for {data_type}")
        rules[data_type] = TransformRule(
            rule_id=str(raw_rule["rule_id"]),
            version=int(raw_rule["version"]),
            target_type=data_type,
        )
    return TransformRegistry(
        transform_version=str(payload["transform_version"]),
        rules=rules,
        null_rule_id=str(raw_null["rule_id"]),
        null_rule_version=int(raw_null["version"]),
    )


def _normalized_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip()


def _is_null(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not _normalized_text(value))


def _transform_non_null(rule: TransformRule, field: FieldContract, raw_value: Any) -> Any:
    if field.data_type in {"string", "enum"}:
        text_value = _normalized_text(str(raw_value))
        if field.data_type == "enum" and field.enum is not None and text_value not in field.enum:
            raise TransformError(f"{field.field_id} is not an allowed enum value: {text_value}")
        return text_value
    if field.data_type == "month":
        match = MONTH_PATTERN.fullmatch(_normalized_text(str(raw_value)))
        if match is None:
            raise TransformError(f"{field.field_id} is not an unambiguous month")
        return f"{match.group(1)}-{match.group(2)}"
    if field.data_type == "datetime":
        if isinstance(raw_value, datetime):
            return raw_value
        try:
            return datetime.fromisoformat(_normalized_text(str(raw_value)).replace("Z", "+00:00"))
        except ValueError as error:
            raise TransformError(f"{field.field_id} is not an ISO datetime") from error
    if field.data_type == "integer":
        if isinstance(raw_value, bool):
            raise TransformError(f"{field.field_id} is not an integer")
        text = _normalized_text(str(raw_value)).replace(",", "")
        if isinstance(raw_value, float) and raw_value.is_integer():
            integer_value = int(raw_value)
        elif INTEGER_PATTERN.fullmatch(text):
            integer_value = int(text)
        else:
            raise TransformError(f"{field.field_id} is not an unambiguous integer")
        if field.minimum is not None and integer_value < int(field.minimum):
            raise TransformError(f"{field.field_id} is below minimum {field.minimum}")
        return integer_value
    if field.data_type == "decimal":
        if isinstance(raw_value, bool):
            raise TransformError(f"{field.field_id} is not a decimal")
        text = _normalized_text(str(raw_value)).replace(",", "")
        try:
            decimal_value = Decimal(text)
        except InvalidOperation as error:
            raise TransformError(f"{field.field_id} is not an unambiguous decimal") from error
        quantum = Decimal(1).scaleb(-(field.scale or 0))
        quantized = decimal_value.quantize(quantum)
        if decimal_value != quantized:
            raise TransformError(f"{field.field_id} exceeds declared scale {field.scale}")
        if field.minimum is not None and quantized < Decimal(field.minimum):
            raise TransformError(f"{field.field_id} is below minimum {field.minimum}")
        return quantized
    raise TransformError(f"unsupported transform target: {rule.target_type}")


def apply_transform(
    rule: TransformRule,
    field: FieldContract,
    raw_value: Any,
    *,
    null_rule_id: str = "normalize_null",
    null_rule_version: int = 1,
) -> TransformResult:
    if _is_null(raw_value):
        return TransformResult(
            raw_value=raw_value,
            value=None,
            rule_id=null_rule_id,
            rule_version=null_rule_version,
            status="unchanged" if raw_value is None else "transformed",
            reason="空白源值规范化为标准空值。",
        )
    value = _transform_non_null(rule, field, raw_value)
    return TransformResult(
        raw_value=raw_value,
        value=value,
        rule_id=rule.rule_id,
        rule_version=rule.version,
        status=(
            "unchanged" if type(value) is type(raw_value) and value == raw_value else "transformed"
        ),
        reason="源值按版本化类型规则转换。",
    )
