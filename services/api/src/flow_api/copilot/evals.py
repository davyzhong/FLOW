"""Fixed offline evaluations for the Copilot governance contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from flow_api.copilot.models import CopilotSection, CopilotUseCase, StructuredAnswer
from flow_api.copilot.validator import validate_answer

DEFAULT_EVALS_PATH = Path(__file__).resolve().parents[3] / "config/copilot/flow-v1-evals.yaml"


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    use_case: CopilotUseCase
    packet: dict[str, Any]
    answer: StructuredAnswer
    expect_accepted: bool
    required_reason: str | None


@dataclass(frozen=True, slots=True)
class EvalResult:
    case_id: str
    passed: bool
    detail: str


def load_cases(path: Path = DEFAULT_EVALS_PATH) -> tuple[EvalCase, ...]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases: list[EvalCase] = []
    for raw in payload["cases"]:
        answer = StructuredAnswer.model_validate(raw["answer"])
        cases.append(
            EvalCase(
                case_id=str(raw["case_id"]),
                use_case=raw["use_case"],
                packet=dict(raw.get("packet") or {}),
                answer=answer,
                expect_accepted=bool(raw["expect_accepted"]),
                required_reason=raw.get("required_reason"),
            )
        )
    return tuple(cases)


def run_case(case: EvalCase) -> EvalResult:
    outcome = validate_answer(case.answer, packet=case.packet, use_case=case.use_case)
    if outcome.accepted != case.expect_accepted:
        return EvalResult(
            case_id=case.case_id,
            passed=False,
            detail=(
                f"expected accepted={case.expect_accepted}, got accepted={outcome.accepted} "
                f"reasons={list(outcome.reasons)}"
            ),
        )
    if case.required_reason and case.required_reason not in " ".join(outcome.reasons):
        return EvalResult(
            case_id=case.case_id,
            passed=False,
            detail=f"missing required reason {case.required_reason} in {list(outcome.reasons)}",
        )
    return EvalResult(case_id=case.case_id, passed=True, detail="ok")


def run_all(path: Path = DEFAULT_EVALS_PATH) -> tuple[EvalResult, ...]:
    return tuple(run_case(case) for case in load_cases(path))


def _sections(payloads: list[dict[str, Any]]) -> tuple[CopilotSection, ...]:
    return tuple(CopilotSection.model_validate(item) for item in payloads)


__all__ = ["EvalCase", "EvalResult", "load_cases", "run_all", "run_case"]
