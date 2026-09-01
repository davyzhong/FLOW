from __future__ import annotations

import pytest

from flow_api.copilot.context import build_empty_packet, canonical_packet, packet_digest
from flow_api.copilot.models import CopilotSection, StructuredAnswer
from flow_api.copilot.validator import ValidationOutcome, validate_answer


class TestPacketHelpers:
    def test_canonical_serialization_is_stable(self) -> None:
        packet = {"b": 1, "a": {"z": "x", "y": [2, 1]}}
        assert canonical_packet(packet) == canonical_packet({"a": {"y": [2, 1], "z": "x"}, "b": 1})

    def test_digest_is_sha256_and_stable(self) -> None:
        packet = {"batch": {"id": "b1"}}
        assert packet_digest(packet) == packet_digest(dict(reversed(list(packet.items()))))
        assert len(packet_digest(packet)) == 64

    def test_empty_packet_has_known_shape(self) -> None:
        packet = build_empty_packet()
        assert packet["batch"] == {}
        assert packet["findings"] == []
        assert packet["metric_definitions"] == []


class TestValidator:
    def base_packet(self) -> dict:
        return {
            "batch": {"id": "batch-1", "code": "B-2026-08"},
            "snapshot": {"id": "snap-1", "engine_version": "flow-analysis/1"},
            "metric_definitions": [
                {"code": "gross_margin", "formula": "gross_profit / revenue", "unit": "%"}
            ],
            "findings": [
                {
                    "id": "finding-1",
                    "title": "毛利恶化",
                    "status": "approved",
                    "impact_amount": "-11570000.0000",
                    "evidence": [
                        {"id": "evidence-1", "status": "verified", "type": "metric_value"}
                    ],
                    "drivers": [
                        {"code": "rate_effect", "contribution_amount": "-7800000.0000"}
                    ],
                }
            ],
        }

    def test_clean_answer_with_cited_numbers_is_accepted(self) -> None:
        answer = StructuredAnswer(
            facts=(
                CopilotSection(
                    text="影响金额 -11570000.0000 元",
                    citations=("finding:finding-1", "evidence:evidence-1"),
                ),
            ),
        )
        outcome = validate_answer(answer, packet=self.base_packet(), use_case="investigation_qa")
        assert outcome == ValidationOutcome.ok()

    def test_uncited_number_is_rejected(self) -> None:
        answer = StructuredAnswer(
            judgments=(CopilotSection(text="影响约为 -9999999.1234 元", citations=()),),
        )
        outcome = validate_answer(answer, packet=self.base_packet(), use_case="investigation_qa")
        assert outcome.accepted is False
        assert any("uncited_number" in reason for reason in outcome.reasons)

    def test_unknown_citation_is_rejected(self) -> None:
        answer = StructuredAnswer(
            judgments=(CopilotSection(text="结论", citations=("finding:unknown",)),),
        )
        outcome = validate_answer(answer, packet=self.base_packet(), use_case="investigation_qa")
        assert outcome.accepted is False
        assert any("unknown_citation" in reason for reason in outcome.reasons)

    def test_fact_requires_verified_evidence_or_metric_citation(self) -> None:
        answer = StructuredAnswer(
            facts=(CopilotSection(text="定性描述", citations=("finding:finding-1",)),),
        )
        outcome = validate_answer(answer, packet=self.base_packet(), use_case="investigation_qa")
        assert outcome.accepted is False
        assert any("unverified_fact" in reason for reason in outcome.reasons)

    def test_report_outline_rejects_unapproved_findings(self) -> None:
        packet = self.base_packet()
        packet["findings"][0]["status"] = "candidate"
        answer = StructuredAnswer(
            judgments=(CopilotSection(text="建议纳入 毛利恶化", citations=("finding:finding-1",)),),
        )
        outcome = validate_answer(answer, packet=packet, use_case="report_outline")
        assert outcome.accepted is False
        assert any("unapproved_finding" in reason for reason in outcome.reasons)

    def test_insufficient_data_allows_questions_only(self) -> None:
        answer = StructuredAnswer(
            questions=(CopilotSection(text="能否提供分区域的回款明细？", citations=()),),
            degradation="insufficient_data",
        )
        outcome = validate_answer(answer, packet=self.base_packet(), use_case="investigation_qa")
        assert outcome.accepted is True

    @pytest.mark.parametrize(
        "use_case", ["mapping_explanation", "investigation_qa", "report_outline"]
    )
    def test_known_use_cases_accept_minimal_answers(self, use_case: str) -> None:
        answer = StructuredAnswer(
            judgments=(CopilotSection(text="ok", citations=()),),
        )
        outcome = validate_answer(answer, packet=self.base_packet(), use_case=use_case)
        assert outcome.accepted is True
