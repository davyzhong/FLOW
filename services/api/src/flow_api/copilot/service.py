"""Governed Copilot use-case services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from flow_api.copilot.context import build_investigation_packet, build_mapping_packet, packet_digest
from flow_api.copilot.models import (
    PROMPT_TEMPLATE_VERSION,
    CopilotRequest,
    CopilotResponse,
    CopilotUseCase,
)
from flow_api.copilot.providers import CopilotProvider
from flow_api.copilot.validator import validate_answer
from flow_api.infrastructure.models.copilot import CopilotInteraction
from flow_api.investigation.repositories import (
    InvestigationNotFoundError,
    InvestigationRepository,
)


class CopilotValidationError(RuntimeError):
    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass(frozen=True, slots=True)
class CopilotInteractionResult:
    interaction_id: str
    outcome: str
    context_digest: str
    response: CopilotResponse


class CopilotService:
    def __init__(
        self,
        provider: CopilotProvider,
        repository: InvestigationRepository | None = None,
    ) -> None:
        self.provider = provider
        self.repository = repository or InvestigationRepository()

    def answer_investigation_question(
        self,
        session: Session,
        finding_id: UUID,
        *,
        question: str,
        actor: str,
        batch_id: UUID | None,
        metric_snapshot_id: UUID | None,
        analysis_run_id: UUID | None,
    ) -> CopilotInteractionResult:
        binding = self.repository.load_binding(
            session,
            finding_id,
            batch_id=batch_id,
            metric_snapshot_id=metric_snapshot_id,
            analysis_run_id=analysis_run_id,
        )
        packet = build_investigation_packet(session, binding)
        return self._run(
            session,
            use_case="investigation_qa",
            question=question,
            packet=packet,
            actor=actor,
            finding_id=finding_id,
            batch_id=binding.snapshot.batch_id,
            references={
                "finding_id": str(finding_id),
                "metric_snapshot_id": str(binding.snapshot.id),
                "analysis_run_id": str(binding.run.id),
                "batch_id": str(binding.snapshot.batch_id),
            },
        )

    def explain_mapping(
        self,
        session: Session,
        import_version_id: UUID,
        *,
        actor: str,
    ) -> CopilotInteractionResult:
        from flow_api.infrastructure.models.intake import ImportVersion

        import_version = session.get(ImportVersion, import_version_id)
        if import_version is None:
            raise InvestigationNotFoundError(
                f"import version does not exist: {import_version_id}"
            )
        packet = build_mapping_packet(session, import_version)
        return self._run(
            session,
            use_case="mapping_explanation",
            question="解释本次导入的映射与质量结论。",
            packet=packet,
            actor=actor,
            finding_id=None,
            batch_id=import_version.batch_id,
            references={"import_version_id": str(import_version_id)},
        )

    def draft_report_outline(
        self,
        session: Session,
        batch_id: UUID,
        *,
        actor: str,
    ) -> CopilotInteractionResult:
        from sqlalchemy import select

        from flow_api.infrastructure.models.analytics import AnalysisRun, Finding

        run = session.scalar(
            select(AnalysisRun)
            .join(Finding, Finding.analysis_run_id == AnalysisRun.id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(1)
        )
        if run is None or run.metric_snapshot.batch_id != batch_id:
            raise InvestigationNotFoundError("batch has no published analysis run")
        top_finding_id = session.scalar(
            select(Finding.id)
            .where(Finding.analysis_run_id == run.id)
            .order_by(Finding.total_score.desc())
            .limit(1)
        )
        if top_finding_id is None:
            raise InvestigationNotFoundError("analysis run has no findings")
        binding = self.repository.load_binding(
            session,
            top_finding_id,
            batch_id=batch_id,
            metric_snapshot_id=None,
            analysis_run_id=run.id,
        )
        packet = build_investigation_packet(session, binding)
        findings = session.scalars(
            select(Finding).where(Finding.analysis_run_id == run.id)
        ).all()
        packet["findings"] = [
            {
                "id": str(item.id),
                "title": str(item.title),
                "status": str(item.status),
                "impact_amount": str(item.impact_amount),
                "evidence": [],
                "drivers": [],
            }
            for item in findings
        ]
        return self._run(
            session,
            use_case="report_outline",
            question="基于已批准发现起草报告大纲。",
            packet=packet,
            actor=actor,
            finding_id=None,
            batch_id=batch_id,
            references={"batch_id": str(batch_id), "analysis_run_id": str(run.id)},
        )

    def _run(
        self,
        session: Session,
        *,
        use_case: CopilotUseCase,
        question: str,
        packet: dict[str, Any],
        actor: str,
        finding_id: UUID | None,
        batch_id: UUID | None,
        references: dict[str, str],
    ) -> CopilotInteractionResult:
        digest = packet_digest(packet)
        request = CopilotRequest(
            use_case=use_case,
            question=question,
            context_digest=digest,
            template_version=PROMPT_TEMPLATE_VERSION,
            context=packet,
        )
        response = self.provider.complete(request)
        outcome = validate_answer(response.answer, packet=packet, use_case=use_case)
        interaction = CopilotInteraction(
            finding_id=finding_id,
            batch_id=batch_id,
            use_case=use_case,
            question=question,
            template_version=response.template_version,
            provider=response.provider,
            model=response.model,
            context_digest=digest,
            request_references=references,
            response_payload=response.model_dump(mode="json"),
            outcome="accepted" if outcome.accepted else "rejected",
            rejection_reasons=list(outcome.reasons),
            actor=actor,
        )
        session.add(interaction)
        session.flush()
        if not outcome.accepted:
            raise CopilotValidationError(outcome.reasons)
        return CopilotInteractionResult(
            interaction_id=str(interaction.id),
            outcome="accepted",
            context_digest=digest,
            response=response,
        )

__all__ = ["CopilotInteractionResult", "CopilotService", "CopilotValidationError"]
