"""Provider-neutral Copilot backends.

`ScriptedProvider` replays deterministic queued responses so all tests and
evaluations run offline. A live provider adapter may implement the same
protocol later; live calls are opt-in and never gate CI.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flow_api.copilot.models import (
    CopilotRequest,
    CopilotResponse,
    CopilotSection,
    StructuredAnswer,
)


@runtime_checkable
class CopilotProvider(Protocol):
    def complete(self, request: CopilotRequest) -> CopilotResponse:
        """Return a structured response for the request."""


class ScriptedProvider:
    """Deterministic provider that replays queued responses in order."""

    provider = "scripted"
    model = "scripted-v1"

    def __init__(self, responses: list[CopilotResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[CopilotRequest] = []

    def complete(self, request: CopilotRequest) -> CopilotResponse:
        self.calls.append(request)
        if not self._responses:
            raise RuntimeError("ScriptedProvider queue is empty")
        response = self._responses.pop(0)
        return response


class DeterministicProvider:
    """Offline template provider that answers strictly from the context packet.

    Facts restate packet values with citations to verified evidence and metric
    definitions; judgments and questions carry no numbers. The output therefore
    passes governance validation by construction while staying fully
    deterministic.
    """

    provider = "deterministic"
    model = "deterministic-v1"

    def complete(self, request: CopilotRequest) -> CopilotResponse:
        packet = request.context
        findings = packet.get("findings", [])
        facts: list[CopilotSection] = []
        judgments: list[CopilotSection] = []
        questions: list[CopilotSection] = []

        metric_codes = [
            str(definition.get("code"))
            for definition in packet.get("metric_definitions", [])
            if definition.get("code")
        ]
        snapshot_id = packet.get("snapshot", {}).get("id")

        if not findings:
            questions.append(
                CopilotSection(
                    text="当前上下文缺少可引用的分析对象，请提供已发布批次或分析运行。",
                    citations=(),
                )
            )
            return self._respond(
                StructuredAnswer(
                    questions=tuple(questions), degradation="insufficient_data"
                )
            )

        for finding in findings:
            finding_id = str(finding.get("id"))
            citations = [f"finding:{finding_id}"]
            verified = [
                f"evidence:{item['id']}"
                for item in finding.get("evidence", [])
                if item.get("status") == "verified" and item.get("id")
            ]
            if verified:
                citations.append(verified[0])
            if metric_codes:
                citations.append(f"metric:{metric_codes[0]}")
            impact = finding.get("impact_amount")
            statement = finding.get("fact_statement") or str(finding.get("title"))
            if impact:
                statement = f"{statement}（影响金额 {impact}）"
            facts.append(
                CopilotSection(text=statement, citations=tuple(citations))
            )
            judgments.append(
                CopilotSection(
                    text=(
                        "判断：该发现与其驱动结构一致；"
                        "引用对象以证据状态为准，未验证内容不作为事实陈述。"
                    ),
                    citations=(f"finding:{finding_id}",),
                )
            )
            questions.append(
                CopilotSection(
                    text="还需要哪些业务凭证来提升该发现的置信度？",
                    citations=(),
                )
            )
        if snapshot_id:
            questions.append(
                CopilotSection(
                    text=f"如需复核计算口径，可引用快照 {snapshot_id}。",
                    citations=(f"snapshot:{snapshot_id}",),
                )
            )
        return self._respond(
            StructuredAnswer(
                facts=tuple(facts),
                judgments=tuple(judgments),
                questions=tuple(questions),
            )
        )

    def _respond(self, answer: StructuredAnswer) -> CopilotResponse:
        return CopilotResponse(
            answer=answer,
            provider=self.provider,
            model=self.model,
        )


__all__ = ["CopilotProvider", "DeterministicProvider", "ScriptedProvider"]
