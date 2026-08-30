from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

PrimitiveType = Literal["boolean", "integer", "decimal", "date", "datetime", "month", "text"]


@dataclass(frozen=True, slots=True)
class CellRegion:
    min_row: int
    max_row: int
    min_column: int
    max_column: int


@dataclass(frozen=True, slots=True)
class ColumnProfile:
    column_index: int
    column_letter: str
    header: str
    stable_field_id: str | None
    inferred_type: PrimitiveType
    nullable: bool
    non_null_count: int
    uniqueness_ratio: float
    sample_values: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class SheetProfile:
    name: str
    index: int
    state: str
    used_region: CellRegion | None
    header_row: int | None
    field_id_row: int | None
    data_start_row: int | None
    data_end_row: int | None
    data_row_count: int
    columns: tuple[ColumnProfile, ...]
    grain_candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkbookProfile:
    sha256: str
    size_bytes: int
    sheets: tuple[SheetProfile, ...]

    @property
    def sheet_count(self) -> int:
        return len(self.sheets)

    def get_sheet(self, name: str) -> SheetProfile:
        try:
            return next(sheet for sheet in self.sheets if sheet.name == name)
        except StopIteration as error:
            raise KeyError(name) from error
