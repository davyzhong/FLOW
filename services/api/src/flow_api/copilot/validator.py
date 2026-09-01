"""Structured-output validation for Copilot responses.

The validator enforces the Phase 8 governance contract:

- every number appearing in the answer must appear verbatim in the allow-listed
  context packet (uncited numbers are rejected);
- every citation must resolve to a known object in the packet;
- `facts` sections must cite verified evidence or metric/analysis objects;
- report outlines may only cite approved findings;
- `insufficient_data` degradation allows only questions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from flow_api.copilot.models import CopilotUseCase, StructuredAnswer

_NUMBER_PATTERN = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

_ALLOWED_FACT_PREFIXES = ("evidence:", "metric:", "analysis:", "snapshot:")

_REPORT_ALLOWED_PREFIXES = ("finding:", "metric:", "snapshot:", "batch:")


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    accepted: bool
    reasons: tuple[str, ...] = field(default=())

    @staticmethod
    def ok() -> ValidationOutcome:
        return ValidationOutcome(accepted=True, reasons=())


def _packet_numbers(packet: dict[str, Any]) -> set[str]:
    numbers: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            numbers.update(_NUMBER_PATTERN.findall(value))

    walk(packet)
    return numbers


def _packet_citations(packet: dict[str, Any]) -> set[str]:
    citations: set[str] = set()
    for batch_id in [packet.get("batch", {}).get("id")]:
        if batch_id:
            citations.add(f"batch:{batch_id}")
    snapshot_id = packet.get("snapshot", {}).get("id")
    if snapshot_id:
        citations.add(f"snapshot:{snapshot_id}")
    for definition in packet.get("metric_definitions", []):
        code = definition.get("code")
        if code:
            citations.add(f"metric:{code}")
    for finding in packet.get("findings", []):
        finding_id = finding.get("id")
        if finding_id:
            citations.add(f"finding:{finding_id}")
        for evidence in finding.get("evidence", []):
            evidence_id = evidence.get("id")
            if evidence_id:
                citations.add(f"evidence:{evidence_id}")
        for driver in finding.get("drivers", []):
            code = driver.get("code")
            if code:
                citations.add(f"driver:{finding_id}:{code}")
    return citations


def _verified_citations(packet: dict[str, Any]) -> set[str]:
    verified: set[str] = set()
    for finding in packet.get("findings", []):
        for evidence in finding.get("evidence", []):
            if evidence.get("status") == "verified" and evidence.get("id"):
                verified.add(f"evidence:{evidence['id']}")
    for definition in packet.get("metric_definitions", []):
        code = definition.get("code")
        if code:
            verified.add(f"metric:{code}")
    snapshot_id = packet.get("snapshot", {}).get("id")
    if snapshot_id:
        verified.add(f"snapshot:{snapshot_id}")
    return verified


def _finding_status_citations(packet: dict[str, Any], status: str) -> set[str]:
    return {
        f"finding:{finding['id']}"
        for finding in packet.get("findings", [])
        if finding.get("status") == status and finding.get("id")
    }


def validate_answer(
    answer: StructuredAnswer,
    *,
    packet: dict[str, Any],
    use_case: CopilotUseCase,
) -> ValidationOutcome:
    reasons: list[str] = []
    allowed_numbers = _packet_numbers(packet)
    allowed_citations = _packet_citations(packet)
    verified_citations = _verified_citations(packet)

    sections: list[tuple[str, tuple[Any, ...]]] = [
        ("facts", answer.facts),
        ("judgments", answer.judgments),
        ("hypotheses", answer.hypotheses),
        ("questions", answer.questions),
    ]
    for _section_name, items in sections:
        for section in items:
            for citation in section.citations:
                if citation not in allowed_citations:
                    reasons.append(f"unknown_citation:{citation}")
            for number in _NUMBER_PATTERN.findall(section.text):
                if number not in allowed_numbers:
                    reasons.append(f"uncited_number:{number}")

    for fact in answer.facts:
        if not any(citation in verified_citations for citation in fact.citations):
            reasons.append("unverified_fact:fact must cite verified evidence or metric context")

    if use_case == "report_outline":
        approved = _finding_status_citations(packet, "approved")
        for section in (*answer.judgments, *answer.facts):
            for citation in section.citations:
                if citation.startswith("finding:") and citation not in approved:
                    reasons.append(f"unapproved_finding:{citation}")

    if answer.degradation == "insufficient_data" and (answer.facts or answer.judgments):
        reasons.append("degradation_conflict:insufficient data may not carry facts or judgments")

    return ValidationOutcome(accepted=not reasons, reasons=tuple(reasons))


__all__ = ["ValidationOutcome", "validate_answer"]
