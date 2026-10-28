"""导入服务编排（R2）：读文件 → 校验 → 存库 的完整入口。"""
from __future__ import annotations

from dataclasses import dataclass

from flow_api.importer.reader import SheetReadError, read_income_statement, read_trial_balance
from flow_api.importer.store import ImportStore
from flow_api.importer.validation import (
    RowError,
    ValidationResult,
    validate_income_statement,
    validate_trial_balance,
)


@dataclass(frozen=True, slots=True)
class ImportOutcome:
    ok: bool
    dataset_id: str | None
    trial_balance: ValidationResult
    income_statement: ValidationResult | None
    read_error: str | None = None


def import_workbook(
    store: ImportStore,
    data: bytes,
    name: str,
    source_filename: str,
) -> ImportOutcome:
    try:
        tb_rows = read_trial_balance(data)
        is_rows = read_income_statement(data)
    except SheetReadError as exc:
        return ImportOutcome(
            ok=False,
            dataset_id=None,
            trial_balance=ValidationResult(ok=False, sheet="科目余额表"),
            income_statement=None,
            read_error=str(exc),
        )
    if not tb_rows:
        read_error = "科目余额表没有数据行"
        return ImportOutcome(
            ok=False,
            dataset_id=None,
            trial_balance=ValidationResult(ok=False, sheet="科目余额表"),
            income_statement=None,
            read_error=read_error,
        )
    tb_result = validate_trial_balance(tb_rows)
    is_result = validate_income_statement(is_rows) if is_rows is not None else None
    ok = tb_result.ok and (is_result is None or is_result.ok)
    if not ok:
        return ImportOutcome(
            ok=False,
            dataset_id=None,
            trial_balance=tb_result,
            income_statement=is_result,
        )
    dataset_id = store.save_dataset(name, source_filename, tb_result, is_result)
    return ImportOutcome(
        ok=True, dataset_id=dataset_id, trial_balance=tb_result, income_statement=is_result
    )


def collect_errors(outcome: ImportOutcome) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if outcome.read_error:
        errors.append({"row": "0", "column": "文件", "message": outcome.read_error})
    results = [outcome.trial_balance]
    if outcome.income_statement is not None:
        results.append(outcome.income_statement)
    for result in results:
        for error in result.errors:
            errors.append(_error_dict(error, result.sheet))
    return errors


def _error_dict(error: RowError, sheet: str) -> dict[str, str]:
    row_label = "表级" if error.row == 0 else f"第 {error.row} 行"
    return {
        "row": str(error.row),
        "column": error.column,
        "message": f"[{sheet} · {row_label} · {error.column}] {error.message}",
    }
