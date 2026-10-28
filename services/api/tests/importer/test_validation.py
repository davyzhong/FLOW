"""R1 校验引擎单测：合法样例 + 四类典型错误各一。"""
from __future__ import annotations

from flow_api.importer.templates import build_template_xlsx
from flow_api.importer.validation import (
    validate_income_statement,
    validate_trial_balance,
)


def _trial_row(**overrides: str) -> dict[str, str]:
    base = {
        "会计期间": "2025-01",
        "科目编码": "1001",
        "科目名称": "库存现金",
        "科目类别": "资产",
        "方向": "借",
        "期初余额": "10000.00",
        "本期借方发生额": "5000.00",
        "本期贷方发生额": "3000.00",
        "期末余额": "12000.00",
    }
    base.update(overrides)
    return base


def test_valid_trial_balance_passes_with_balance_summary() -> None:
    rows = [
        _trial_row(),
        _trial_row(科目编码="2001", 科目名称="短期借款", 科目类别="负债", 方向="贷",
                   期初余额="10000.00", 期末余额="12000.00"),
    ]
    result = validate_trial_balance(rows)
    assert result.ok, result.errors
    assert result.balance_summary["期末借方合计"] == "12000.00"
    assert result.balance_summary["期末贷方合计"] == "12000.00"


def test_unbalanced_closing_rejected_with_row_zero_error() -> None:
    rows = [
        _trial_row(期末余额="12000.00"),
        _trial_row(
            科目编码="2001", 科目类别="负债", 方向="贷",
            期初余额="10000.00", 期末余额="99999.00",
        ),
    ]
    result = validate_trial_balance(rows)
    assert not result.ok
    assert any(e.row == 0 and "期末借贷不平衡" in e.message for e in result.errors)


def test_missing_required_column_fails_format_check() -> None:
    row = _trial_row()
    del row["科目类别"]
    row["科目类别缺失占位"] = ""
    result = validate_trial_balance([row])
    assert not result.ok
    assert any(e.column == "科目类别" for e in result.errors)


def test_bad_period_and_amount_reported_with_row_number() -> None:
    rows = [_trial_row(会计期间="2025/1", 期初余额="abc")]
    result = validate_trial_balance(rows)
    assert not result.ok
    messages = {(e.row, e.column) for e in result.errors}
    assert (1, "会计期间") in messages
    assert (1, "期初余额") in messages


def test_duplicate_period_and_code_rejected() -> None:
    rows = [_trial_row(), _trial_row(科目名称="现金二")]
    result = validate_trial_balance(rows)
    assert not result.ok
    assert any("科目编码重复" in e.message for e in result.errors)


def test_invalid_category_and_direction_rejected() -> None:
    result = validate_trial_balance([_trial_row(科目类别="其他", 方向="平")])
    assert not result.ok
    columns = {e.column for e in result.errors}
    assert "科目类别" in columns
    assert "方向" in columns


def test_income_statement_valid_and_invalid() -> None:
    ok = validate_income_statement([
        {"会计期间": "2025-01", "项目": "营业收入", "本期金额": "100.00", "本年累计金额": "100.00"},
    ])
    assert ok.ok
    bad = validate_income_statement([
        {"会计期间": "202501", "项目": "", "本期金额": "x", "本年累计金额": ""},
    ])
    assert not bad.ok
    assert len(bad.errors) >= 3


def test_template_xlsx_contains_header_and_samples() -> None:
    import io

    from openpyxl import load_workbook

    data = build_template_xlsx()
    workbook = load_workbook(io.BytesIO(data))
    ws = workbook.active
    assert ws.title == "科目余额表"
    first_row = [cell.value for cell in ws[1]]
    assert first_row[0] == "会计期间"
    assert ws.max_row >= 3  # 表头 + 两行示例
