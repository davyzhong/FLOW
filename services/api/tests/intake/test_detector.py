from __future__ import annotations

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from flow_api.intake.detector import (
    FormulaInputError,
    InvalidWorkbookError,
    UnsafeWorkbookError,
    profile_workbook,
)
from flow_api.intake.models import ColumnProfile, SheetProfile

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
STANDARD = REPOSITORY_ROOT / "fixtures/workbooks/flow_standard_v1.xlsx"
NONSTANDARD = REPOSITORY_ROOT / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx"


def _column(profile: SheetProfile, header: str) -> ColumnProfile:
    return next(column for column in profile.columns if column.header == header)


def test_standard_workbook_profile_detects_flow_structure_and_types() -> None:
    profile = profile_workbook(STANDARD)

    assert profile.sha256 == hashlib.sha256(STANDARD.read_bytes()).hexdigest()
    assert profile.sheet_count == 10
    operating = profile.get_sheet("02_经营实际")
    assert operating.header_row == 1
    assert operating.field_id_row == 2
    assert operating.data_start_row == 4
    assert operating.data_end_row == 3075
    assert operating.data_row_count == 3072
    assert _column(operating, "营业收入").stable_field_id == "revenue"
    assert _column(operating, "营业收入").inferred_type == "decimal"
    assert _column(operating, "月份").inferred_type == "month"
    assert _column(operating, "记录编码").uniqueness_ratio == 1.0
    assert "记录编码" in operating.grain_candidates


def test_nonstandard_workbook_profile_finds_shifted_headers_and_data_region() -> None:
    original = NONSTANDARD.read_bytes()
    profile = profile_workbook(original)

    assert original == NONSTANDARD.read_bytes()
    assert profile.sheet_count == 9
    operating = profile.get_sheet("业务明细")
    assert operating.header_row == 3
    assert operating.field_id_row is None
    assert operating.data_start_row == 4
    assert operating.data_row_count == 3072
    assert _column(operating, "营业收入(元)").stable_field_id is None
    assert _column(operating, "营业收入(元)").inferred_type == "decimal"
    assert _column(operating, "业务月份").inferred_type == "month"
    assert _column(operating, "来源记录号").uniqueness_ratio == 1.0
    assert "数据备注" not in operating.grain_candidates


def test_empty_sheet_is_profiled_without_inventing_a_header(tmp_path: Path) -> None:
    workbook = Workbook()
    workbook.active.title = "空白页"
    path = tmp_path / "empty.xlsx"
    workbook.save(path)

    sheet = profile_workbook(path).get_sheet("空白页")

    assert sheet.header_row is None
    assert sheet.data_start_row is None
    assert sheet.data_row_count == 0
    assert sheet.columns == ()


def test_formula_cells_are_rejected_as_untrusted_input(tmp_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["月份", "收入"])
    sheet.append(["2026-08", "=1+1"])
    path = tmp_path / "formula.xlsx"
    workbook.save(path)

    with pytest.raises(FormulaInputError, match="formula"):
        profile_workbook(path)


def test_invalid_and_suspicious_zip_inputs_are_rejected() -> None:
    with pytest.raises(InvalidWorkbookError):
        profile_workbook(b"not an xlsx")

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", b"0" * 2_000_000)
    with pytest.raises(UnsafeWorkbookError, match="compression ratio"):
        profile_workbook(buffer.getvalue())
