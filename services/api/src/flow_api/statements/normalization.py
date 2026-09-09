"""规范化与取数映射（B03）。

原始披露行名 → 标准报表项目 item_id 的归一化：
- 原始行与原始值（statement_line_item）不可变，归一化结果按映射版本修订并存；
- 同一映射版本重复归一幂等重建；新映射版本新增行集，旧版保留可查询；
- 组合映射（{sum: [...]}）生成合成行并在 trace 留痕；
- 未映射行如实保留 item_id=None，不猜测。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.statement import (
    StatementLineItem,
    StatementNormalizedItem,
    StatementReport,
)

# stock_code → 别名映射公司键（与公司专用抽取器谱系一致）
COMPANY_KEY_BY_STOCK: dict[str, str] = {
    "002352.SZ": "sf_002352",
    "0700.HK": "tencent_0700",
    "2618.HK": "jd_logistics_2618",
    "600233": "yto_600233",
}

ALIAS_MAP_PATH = Path("config/statements/item_alias_map_v1.yaml")
ROLE_VALUE_COLUMNS = {
    "end": "value_end",
    "open": "value_begin",
    "cur": "value_current",
    "prev_yoy": "value_prior",
}


class NormalizationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class NormalizationSummary:
    report_id: Any
    mapping_version: str
    resolved: int
    unresolved: int
    synthetic: int
    unresolved_items: tuple[str, ...]


def _norm(name: str) -> str:
    return "".join(str(name or "").split())


def load_alias_map(path: Path | None = None) -> dict[str, Any]:
    candidate = path or ALIAS_MAP_PATH
    for root in (Path.cwd(), *Path.cwd().parents):
        full = root / candidate
        if full.is_file():
            data = yaml.safe_load(full.read_text())
            if not isinstance(data, dict) or "companies" not in data:
                raise NormalizationError("invalid_alias_map", f"别名映射缺少 companies：{full}")
            return data
    raise NormalizationError("alias_map_not_found", f"未找到别名映射：{candidate}")


def _resolve_company(alias_map: dict[str, Any], report: StatementReport) -> dict[str, Any] | None:
    key = COMPANY_KEY_BY_STOCK.get(report.stock_code)
    if key is None:
        return None
    company = alias_map.get("companies", {}).get(key)
    if not isinstance(company, dict):
        return None
    return company.get("statements")


def _lookup(mapping: dict[str, Any], item_name: str) -> Any:
    if item_name in mapping:
        return mapping[item_name]
    normalized = _norm(item_name)
    for key, value in mapping.items():
        if _norm(key) == normalized:
            return value
    return None


def _mapped_values(
    line: StatementLineItem, target: Any
) -> tuple[str | None, dict[str, Decimal | None], dict[str, str]]:
    if isinstance(target, str):
        return target, {
            "value_end": line.value_end,
            "value_begin": line.value_begin,
            "value_current": line.value_current,
            "value_prior": line.value_prior,
        }, {"kind": "mapped"}
    if isinstance(target, dict) and isinstance(target.get("item"), str):
        use_absolute = target.get("abs") is True
        values = {
            name: abs(value) if use_absolute and value is not None else value
            for name, value in {
                "value_end": line.value_end,
                "value_begin": line.value_begin,
                "value_current": line.value_current,
                "value_prior": line.value_prior,
            }.items()
        }
        trace = {
            "kind": "mapped",
            **({"transformation": "absolute_value"} if use_absolute else {}),
            **({"note": str(target["note"])} if target.get("note") else {}),
        }
        return target["item"], values, trace
    return None, {
        "value_end": line.value_end,
        "value_begin": line.value_begin,
        "value_current": line.value_current,
        "value_prior": line.value_prior,
    }, {"note": "unmapped"}


def normalize_report(
    session: Session,
    report: StatementReport,
    *,
    alias_map: dict[str, Any] | None = None,
    mapping_version: str | None = None,
) -> NormalizationSummary:
    """把一份报表的原始行归一到标准 item_id；按映射版本幂等重建。"""

    alias_map = alias_map or load_alias_map()
    version = mapping_version or str(alias_map.get("version", "v0"))
    statements = _resolve_company(alias_map, report)

    session.execute(
        delete(StatementNormalizedItem).where(
            StatementNormalizedItem.report_id == report.id,
            StatementNormalizedItem.mapping_version == version,
        )
    )

    by_type: dict[str, list[StatementLineItem]] = defaultdict(list)
    for item in report.items:
        by_type[item.statement_type].append(item)

    resolved = unresolved = synthetic = 0
    unresolved_names: list[str] = []

    for statement_type, lines in by_type.items():
        section = (statements or {}).get(statement_type, {})
        mapping = section.get("map", {}) if isinstance(section, dict) else {}
        roles = section.get("roles", {}) if isinstance(section, dict) else {}
        applicable_columns = {
            ROLE_VALUE_COLUMNS[role]
            for role in roles.values()
            if role in ROLE_VALUE_COLUMNS
        }
        # 同名行序号（U2/6.1 契约）：港股 IFRS 合法同名行（借款等在流动/
        # 非流动分组下各一行）按披露出现序 0,1,2… 编号，保留分组语义，
        # 不合并原始行；唯一键为 (report, version, type, group_ordinal, item_name)。
        ordinal_by_name: dict[str, int] = {}
        for line in lines:
            group_ordinal = ordinal_by_name.get(line.item_name, 0)
            ordinal_by_name[line.item_name] = group_ordinal + 1
            target = _lookup(mapping, line.item_name)
            if isinstance(target, dict) and "sum" in target:
                # 组合映射在合成行生成，原始行本身不再单独映射
                continue
            item_id, values, trace = _mapped_values(line, target)
            if item_id is not None:
                resolved += 1
            else:
                unresolved += 1
                unresolved_names.append(line.item_name)
            session.add(
                StatementNormalizedItem(
                    report_id=report.id,
                    mapping_version=version,
                    statement_type=statement_type,
                    item_name=line.item_name,
                    group_ordinal=group_ordinal,
                    item_id=item_id,
                    value_end=values["value_end"],
                    value_begin=values["value_begin"],
                    value_current=values["value_current"],
                    value_prior=values["value_prior"],
                    trace=trace,
                )
            )

        # 合成行（{sum: [行名...]}）
        for key, target in mapping.items():
            if not (isinstance(target, dict) and "sum" in target):
                continue
            item_id = key.lstrip("_")
            parts: dict[str, StatementLineItem] = {}
            for part_name in target["sum"]:
                part = next(
                    (line for line in lines if _norm(line.item_name) == _norm(part_name)),
                    None,
                )
                if part is not None:
                    parts[part_name] = part

            missing_parts = [name for name in target["sum"] if name not in parts]
            value_columns = ("value_end", "value_begin", "value_current", "value_prior")
            missing_parts_by_column: dict[str, list[str]] = {}
            for column in value_columns:
                column_has_value = any(
                    getattr(part, column) is not None for part in parts.values()
                )
                if column not in applicable_columns and not column_has_value:
                    continue
                missing_for_column = [
                    name
                    for name in target["sum"]
                    if name not in parts or getattr(parts[name], column) is None
                ]
                if missing_for_column:
                    missing_parts_by_column[column] = missing_for_column

            def _sum(
                col: str,
                parts: dict[str, StatementLineItem] = parts,
                missing_parts: list[str] = missing_parts,
            ) -> Decimal | None:
                if missing_parts:
                    return None
                values = [getattr(part, col) for part in parts.values()]
                if not values or any(value is None for value in values):
                    return None
                total: Decimal = Decimal(0)
                for value in values:
                    assert value is not None
                    total += value
                return total

            synthetic += 1
            session.add(
                StatementNormalizedItem(
                    report_id=report.id,
                    mapping_version=version,
                    statement_type=statement_type,
                    item_name=key,
                    item_id=item_id,
                    value_end=_sum("value_end"),
                    value_begin=_sum("value_begin"),
                    value_current=_sum("value_current"),
                    value_prior=_sum("value_prior"),
                    trace={
                        "kind": "sum",
                        "status": (
                            "incomplete"
                            if missing_parts or missing_parts_by_column
                            else "complete"
                        ),
                        "parts": sorted(parts),
                        "missing_parts": missing_parts,
                        "missing_parts_by_column": missing_parts_by_column,
                        **({"note": target["note"]} if target.get("note") else {}),
                    },
                )
            )

    session.flush()
    return NormalizationSummary(
        report_id=report.id,
        mapping_version=version,
        resolved=resolved,
        unresolved=unresolved,
        synthetic=synthetic,
        unresolved_items=tuple(unresolved_names),
    )


def normalized_items(
    session: Session, report_id: Any, *, mapping_version: str
) -> list[StatementNormalizedItem]:
    """历史查询：按映射版本读取归一化行（旧版本可稳定查询）。"""

    return list(
        session.scalars(
            select(StatementNormalizedItem)
            .where(
                StatementNormalizedItem.report_id == report_id,
                StatementNormalizedItem.mapping_version == mapping_version,
            )
            .order_by(StatementNormalizedItem.statement_type, StatementNormalizedItem.item_name)
        )
    )


__all__ = [
    "ALIAS_MAP_PATH",
    "COMPANY_KEY_BY_STOCK",
    "NormalizationError",
    "NormalizationSummary",
    "load_alias_map",
    "normalize_report",
    "normalized_items",
]
