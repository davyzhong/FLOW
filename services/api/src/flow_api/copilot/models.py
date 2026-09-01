"""Typed models for bounded Copilot interactions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CopilotUseCase = Literal["mapping_explanation", "investigation_qa", "report_outline"]

PROMPT_TEMPLATE_VERSION = "flow.copilot.v1"


class StrictModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CopilotRequest(StrictModel):
    use_case: CopilotUseCase
    question: str = ""
    context_digest: str = Field(min_length=8)
    template_version: str = PROMPT_TEMPLATE_VERSION
    context: dict[str, Any] = Field(default_factory=dict)


class CopilotSection(StrictModel):
    text: str = Field(min_length=1)
    citations: tuple[str, ...] = ()


class StructuredAnswer(StrictModel):
    facts: tuple[CopilotSection, ...] = ()
    judgments: tuple[CopilotSection, ...] = ()
    hypotheses: tuple[CopilotSection, ...] = ()
    questions: tuple[CopilotSection, ...] = ()
    degradation: Literal["none", "insufficient_data"] = "none"

    @model_validator(mode="after")
    def _require_some_content(self) -> StructuredAnswer:
        if (
            not self.facts
            and not self.judgments
            and not self.hypotheses
            and not self.questions
            and self.degradation == "none"
        ):
            raise ValueError("answer must contain at least one section or a degradation")
        return self


class CopilotResponse(StrictModel):
    answer: StructuredAnswer
    provider: str
    model: str
    template_version: str = PROMPT_TEMPLATE_VERSION


__all__ = [
    "CopilotRequest",
    "CopilotResponse",
    "CopilotSection",
    "CopilotUseCase",
    "PROMPT_TEMPLATE_VERSION",
    "StrictModel",
    "StructuredAnswer",
]
