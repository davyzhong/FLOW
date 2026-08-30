from __future__ import annotations

import re
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

FIELD_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

DataType = Literal["string", "integer", "decimal", "month", "datetime", "enum"]


class ForeignKeyContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sheet_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    field_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")


class FieldContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(min_length=1)
    data_type: DataType
    required: bool
    nullable: bool
    description: str = Field(min_length=1)
    unit: str | None = None
    scale: int | None = Field(default=None, ge=0, le=12)
    enum: tuple[str, ...] | None = None
    foreign_key: ForeignKeyContract | None = None
    minimum: str | None = None
    format: str | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> Self:
        if self.required and self.nullable:
            raise ValueError("a required field cannot be nullable")
        if self.data_type == "decimal" and (self.unit is None or self.scale is None):
            raise ValueError("decimal fields require unit and scale")
        if self.data_type == "enum" and not self.enum:
            raise ValueError("enum fields require allowed values")
        if self.data_type != "enum" and self.enum is not None:
            raise ValueError("only enum fields may declare allowed values")
        return self


class SheetContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sheet_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    sheet_name: str = Field(min_length=1, max_length=31)
    purpose: str = Field(min_length=1)
    fields: tuple[FieldContract, ...] = Field(min_length=1)
    grain: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_fields_and_grain(self) -> Self:
        field_ids = [field.field_id for field in self.fields]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError(f"duplicate field ID in sheet {self.sheet_id}")
        missing_grain_fields = set(self.grain) - set(field_ids)
        if missing_grain_fields:
            raise ValueError(
                f"unknown grain fields in sheet {self.sheet_id}: {sorted(missing_grain_fields)}"
            )
        return self

    def get_field(self, field_id: str) -> FieldContract:
        for field in self.fields:
            if field.field_id == field_id:
                return field
        raise KeyError(f"unknown field {self.sheet_id}.{field_id}")


class WorkbookContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: str = Field(pattern=r"^flow\.excel\.v[1-9][0-9]*$")
    workbook_name: str = Field(min_length=1)
    sheets: tuple[SheetContract, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_sheets_and_relationships(self) -> Self:
        sheet_ids = [sheet.sheet_id for sheet in self.sheets]
        sheet_names = [sheet.sheet_name for sheet in self.sheets]
        if len(sheet_ids) != len(set(sheet_ids)):
            raise ValueError("duplicate sheet ID")
        if len(sheet_names) != len(set(sheet_names)):
            raise ValueError("duplicate sheet name")

        targets = {
            (sheet.sheet_id, field.field_id) for sheet in self.sheets for field in sheet.fields
        }
        for sheet in self.sheets:
            for field in sheet.fields:
                if field.foreign_key is not None:
                    target = (field.foreign_key.sheet_id, field.foreign_key.field_id)
                    if target not in targets:
                        raise ValueError(
                            f"unknown foreign key target for {sheet.sheet_id}.{field.field_id}: "
                            f"{target[0]}.{target[1]}"
                        )
        return self

    def get_sheet(self, sheet_id: str) -> SheetContract:
        for sheet in self.sheets:
            if sheet.sheet_id == sheet_id:
                return sheet
        raise KeyError(f"unknown sheet {sheet_id}")
