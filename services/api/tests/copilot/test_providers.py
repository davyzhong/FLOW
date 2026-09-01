from __future__ import annotations

import pytest
from pydantic import ValidationError

from flow_api.copilot.models import (
    CopilotRequest,
    CopilotResponse,
    CopilotSection,
    StructuredAnswer,
)
from flow_api.copilot.providers import CopilotProvider, ScriptedProvider


class TestModels:
    def test_request_is_frozen_and_typed(self) -> None:
        request = CopilotRequest(
            use_case="investigation_qa",
            question="为什么毛利率下降？",
            context_digest="abcdef123456",
            template_version="flow.copilot.v1",
        )
        assert request.use_case == "investigation_qa"
        with pytest.raises(ValidationError):
            request.question = "改动"

    def test_structured_answer_requires_sections(self) -> None:
        answer = StructuredAnswer(
            facts=(),
            judgments=(
                CopilotSection(
                    text="结构变化是主要驱动", citations=["finding:1"]
                ),
            ),
            hypotheses=(),
            questions=(),
        )
        assert answer.judgments[0].citations == ("finding:1",)
        with pytest.raises(ValidationError):
            StructuredAnswer()

    def test_response_carries_answer_and_usage(self) -> None:
        response = CopilotResponse(
            answer=StructuredAnswer(
                degradation="insufficient_data",
            ),
            provider="scripted",
            model="scripted-v1",
            template_version="flow.copilot.v1",
        )
        assert response.provider == "scripted"


class TestScriptedProvider:
    def test_protocol_is_satisfied(self) -> None:
        provider = ScriptedProvider(responses=[])
        assert isinstance(provider, CopilotProvider)

    def test_scripted_provider_returns_queued_response(self) -> None:
        queued = CopilotResponse(
            answer=StructuredAnswer(
                facts=(CopilotSection(text="影响 -1157 万", citations=["finding:1"]),),
            ),
            provider="scripted",
            model="scripted-v1",
            template_version="flow.copilot.v1",
        )
        provider = ScriptedProvider(responses=[queued])
        request = CopilotRequest(
            use_case="investigation_qa",
            question="q",
            context_digest="digest0001",
            template_version="flow.copilot.v1",
        )
        assert provider.complete(request) is queued

    def test_scripted_provider_without_queue_is_explicit(self) -> None:
        provider = ScriptedProvider(responses=[])
        request = CopilotRequest(
            use_case="investigation_qa",
            question="q",
            context_digest="digest0001",
            template_version="flow.copilot.v1",
        )
        with pytest.raises(RuntimeError):
            provider.complete(request)
