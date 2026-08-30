from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from flow_api.data_contract.models import WorkbookContract
from flow_api.intake.mapping import FieldMapping, MappingProposal
from flow_api.intake.models import WorkbookProfile


class InvalidAISuggestionError(ValueError):
    """An AI proposal references identities outside the observed source or frozen contract."""


class AIMappingSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_sheet: str = Field(min_length=1)
    source_header: str = Field(min_length=1)
    target_sheet_id: str = Field(min_length=1)
    target_field_id: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1)


class AIMappingAdapter(Protocol):
    def suggest(
        self,
        profile: WorkbookProfile,
        contract: WorkbookContract,
        deterministic_proposal: MappingProposal,
    ) -> tuple[AIMappingSuggestion, ...]: ...


def apply_ai_suggestions(
    proposal: MappingProposal,
    profile: WorkbookProfile,
    contract: WorkbookContract,
    suggestions: tuple[AIMappingSuggestion, ...],
) -> MappingProposal:
    sheets = {sheet.target_sheet_id: sheet for sheet in proposal.sheets}
    source_sheets = {sheet.name: sheet for sheet in profile.sheets}
    for suggestion in suggestions:
        try:
            contract_sheet = contract.get_sheet(suggestion.target_sheet_id)
            contract_sheet.get_field(suggestion.target_field_id)
            mapped_sheet = sheets[suggestion.target_sheet_id]
            source_sheet = source_sheets[suggestion.source_sheet]
        except KeyError as error:
            raise InvalidAISuggestionError(
                "AI suggestion references an unknown identity"
            ) from error
        if mapped_sheet.source_sheet != suggestion.source_sheet:
            raise InvalidAISuggestionError("AI suggestion crosses the confirmed sheet mapping")
        if suggestion.target_field_id not in mapped_sheet.unresolved_required_fields:
            raise InvalidAISuggestionError("AI may only fill an unresolved required field")
        source_columns = {column.header: column for column in source_sheet.columns}
        if suggestion.source_header not in source_columns:
            raise InvalidAISuggestionError("AI suggestion references an unknown source column")
        if any(field.source_header == suggestion.source_header for field in mapped_sheet.fields):
            raise InvalidAISuggestionError("AI suggestion reuses an already mapped source column")
        source_column = source_columns[suggestion.source_header]
        field_mapping = FieldMapping(
            source_header=suggestion.source_header,
            source_column=source_column.column_letter,
            target_field_id=suggestion.target_field_id,
            method="ai_suggestion",
            score=suggestion.confidence,
            confidence="medium" if suggestion.confidence >= 0.75 else "low",
            requires_confirmation=True,
            rationale=suggestion.rationale,
        )
        updated = replace(
            mapped_sheet,
            fields=mapped_sheet.fields + (field_mapping,),
            unresolved_required_fields=tuple(
                field_id
                for field_id in mapped_sheet.unresolved_required_fields
                if field_id != suggestion.target_field_id
            ),
            ignored_source_headers=tuple(
                header
                for header in mapped_sheet.ignored_source_headers
                if header != suggestion.source_header
            ),
        )
        sheets[suggestion.target_sheet_id] = updated

    return replace(
        proposal,
        sheets=tuple(sheets[sheet.target_sheet_id] for sheet in proposal.sheets),
    )
