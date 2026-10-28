"""导入校验引擎（R1）：Decimal 全程、错误逐行定位、整批拒绝制。

校验器是纯函数：输入解析后的字典行，输出结构化结果，不触数据库——
R2 的 API 层负责读文件与写库，本模块只回答「这批数据能不能收」。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from flow_api.importer.templates import (
    ACCOUNT_CATEGORIES,
    DIRECTIONS,
    INCOME_STATEMENT_COLUMNS,
    INCOME_STATEMENT_SHEET,
    TRIAL_BALANCE_COLUMNS,
    TRIAL_BALANCE_SHEET,
)

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class RowError:
    """单行错误：row 为数据行号（1 起，不含表头）。"""

    row: int
    column: str
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    sheet: str
    errors: tuple[RowError, ...] = ()
    rows: tuple[dict[str, str], ...] = ()
    # 平衡校验通过时的两侧合计（借/贷），供 API 层回显
    balance_summary: dict[str, str] = field(default_factory=dict)


def _parse_amount(value: str, row: int, column: str, errors: list[RowError]) -> Decimal | None:
    text = (value or "").strip()
    if not text:
        errors.append(RowError(row, column, "金额不能为空（无发生填 0.00）"))
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        errors.append(RowError(row, column, f"金额须为数字，收到：{text!r}"))
        return None


def validate_trial_balance(rows: list[dict[str, str]]) -> ValidationResult:
    """科目余额表校验：列完整 → 行级格式 → 期初/期末借贷平衡 → 重复科目。"""
    errors: list[RowError] = []
    # 必需列缺失由 R2 读表层负责（openpyxl 按表头解析），本函数只校验行数据。

    parsed: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    opening_debit = opening_credit = closing_debit = closing_credit = _ZERO

    for index, row in enumerate(rows, start=1):
        period = (row.get("会计期间") or "").strip()
        code = (row.get("科目编码") or "").strip()
        category = (row.get("科目类别") or "").strip()
        direction = (row.get("方向") or "").strip()
        if not _PERIOD_RE.match(period):
            errors.append(RowError(index, "会计期间", "会计期间须为 YYYY-MM 格式（如 2025-01）"))
        if not code:
            errors.append(RowError(index, "科目编码", "科目编码不能为空"))
        if category not in ACCOUNT_CATEGORIES:
            allowed = "/".join(ACCOUNT_CATEGORIES)
            errors.append(RowError(index, "科目类别", f"科目类别须为 {allowed} 之一"))
        if direction not in DIRECTIONS:
            errors.append(RowError(index, "方向", f"方向须为 {'/'.join(DIRECTIONS)} 之一"))

        opening = _parse_amount(row.get("期初余额", ""), index, "期初余额", errors)
        closing = _parse_amount(row.get("期末余额", ""), index, "期末余额", errors)
        _parse_amount(row.get("本期借方发生额", ""), index, "本期借方发生额", errors)
        _parse_amount(row.get("本期贷方发生额", ""), index, "本期贷方发生额", errors)

        key = (period, code)
        if key in seen_keys:
            errors.append(RowError(index, "科目编码", f"同一期间科目编码重复：{period} / {code}"))
        seen_keys.add(key)

        if opening is not None:
            if direction == "借":
                opening_debit += opening
            elif direction == "贷":
                opening_credit += opening
        if closing is not None:
            if direction == "借":
                closing_debit += closing
            elif direction == "贷":
                closing_credit += closing
        parsed.append({column: (row.get(column) or "").strip() for column in TRIAL_BALANCE_COLUMNS})

    balance: dict[str, str] = {}
    if not errors:
        if opening_debit != opening_credit:
            errors.append(
                RowError(
                    0,
                    "期初余额",
                    f"期初借贷不平衡：借方合计 {opening_debit} ≠ 贷方合计 {opening_credit}",
                )
            )
        if closing_debit != closing_credit:
            errors.append(
                RowError(
                    0,
                    "期末余额",
                    f"期末借贷不平衡：借方合计 {closing_debit} ≠ 贷方合计 {closing_credit}",
                )
            )
        balance = {
            "期初借方合计": str(opening_debit),
            "期初贷方合计": str(opening_credit),
            "期末借方合计": str(closing_debit),
            "期末贷方合计": str(closing_credit),
        }
    return ValidationResult(
        ok=not errors,
        sheet=TRIAL_BALANCE_SHEET,
        errors=tuple(errors),
        rows=tuple(parsed),
        balance_summary=balance,
    )


def validate_income_statement(rows: list[dict[str, str]]) -> ValidationResult:
    """利润表校验：列完整 → 行级格式（无平衡约束，多期损益自由结构）。"""
    errors: list[RowError] = []
    parsed: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=1):
        period = (row.get("会计期间") or "").strip()
        item = (row.get("项目") or "").strip()
        if not _PERIOD_RE.match(period):
            errors.append(RowError(index, "会计期间", "会计期间须为 YYYY-MM 格式（如 2025-01）"))
        if not item:
            errors.append(RowError(index, "项目", "项目不能为空"))
        _parse_amount(row.get("本期金额", ""), index, "本期金额", errors)
        _parse_amount(row.get("本年累计金额", ""), index, "本年累计金额", errors)
        parsed.append(
            {column: (row.get(column) or "").strip() for column in INCOME_STATEMENT_COLUMNS}
        )
    return ValidationResult(
        ok=not errors,
        sheet=INCOME_STATEMENT_SHEET,
        errors=tuple(errors),
        rows=tuple(parsed),
    )
