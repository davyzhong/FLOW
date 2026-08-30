from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from flow_api.data_contract.records import CanonicalPackage


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, ".4f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalize(nested) for key, nested in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        normalized = [_normalize(nested) for nested in value]
        if all(isinstance(item, dict) for item in normalized):
            return sorted(
                normalized,
                key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True),
            )
        return normalized
    return value


def semantic_snapshot(package: CanonicalPackage) -> dict[str, Any]:
    normalized = _normalize(package.model_dump())
    if not isinstance(normalized, dict):
        raise TypeError("canonical package did not normalize to a mapping")
    return normalized


def _compare(expected: Any, actual: Any, path: str, differences: list[str]) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            child_path = f"{path}.{key}" if path else key
            if key not in expected:
                differences.append(f"{child_path}: unexpected value {actual[key]!r}")
            elif key not in actual:
                differences.append(f"{child_path}: missing expected value {expected[key]!r}")
            else:
                _compare(expected[key], actual[key], child_path, differences)
        return
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            differences.append(f"{path}: expected {len(expected)} rows, received {len(actual)}")
            return
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual, strict=True)):
            _compare(expected_item, actual_item, f"{path}[{index}]", differences)
        return
    if expected != actual:
        differences.append(f"{path}: expected {expected!r}, received {actual!r}")


def compare_semantics(
    expected: CanonicalPackage | dict[str, Any],
    actual: CanonicalPackage | dict[str, Any],
) -> tuple[str, ...]:
    expected_snapshot = (
        semantic_snapshot(expected) if isinstance(expected, CanonicalPackage) else expected
    )
    actual_snapshot = semantic_snapshot(actual) if isinstance(actual, CanonicalPackage) else actual
    differences: list[str] = []
    _compare(expected_snapshot, actual_snapshot, "", differences)
    return tuple(differences)
