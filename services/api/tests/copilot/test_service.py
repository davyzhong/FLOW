from __future__ import annotations

import uuid

import pytest
from integration.analysis_run_support import (
    _intake_session_fixture as _intake_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    _metric_session_fixture as _metric_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import (
    analysis_session_fixture as _analysis_session_fixture,  # noqa: F401
)
from integration.analysis_run_support import publish_analysis_run
from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.copilot.models import (
    CopilotResponse,
    CopilotSection,
    StructuredAnswer,
)
from flow_api.copilot.providers import ScriptedProvider
from flow_api.copilot.service import CopilotService, CopilotValidationError
from flow_api.infrastructure.models.analytics import Evidence, Finding
from flow_api.infrastructure.models.copilot import CopilotInteraction


def _top_finding(session: Session) -> Finding:
    finding = session.scalars(select(Finding).order_by(Finding.total_score.desc())).first()
    assert finding is not None
    return finding


def _scripted_response(question: str, impact: str, evidence_id: str) -> CopilotResponse:
    return CopilotResponse(
        answer=StructuredAnswer(
            facts=(
                CopilotSection(
                    text=f"影响金额 {impact}。{question}",
                    citations=("evidence:" + evidence_id, "metric:gross_margin"),
                ),
            ),
            judgments=(CopilotSection(text="结构与成本为主要驱动。", citations=()),),
        ),
        provider="scripted",
        model="scripted-v1",
    )


def test_investigation_question_round_trip(analysis_session: Session) -> None:
    run = publish_analysis_run(analysis_session)
    finding = _top_finding(analysis_session)
    evidence_id = str(
        analysis_session.scalar(select(Evidence.id).where(Evidence.finding_id == finding.id))
    )
    packet_answer = CopilotResponse(
        answer=StructuredAnswer(
            facts=(
                CopilotSection(
                    text=f"影响 {finding.impact_amount} 已由证据支持。",
                    citations=(f"evidence:{evidence_id}", f"finding:{finding.id}"),
                ),
            ),
            judgments=(CopilotSection(text="判断：成本上升是主因。", citations=()),),
        ),
        provider="scripted",
        model="scripted-v1",
    )
    provider = ScriptedProvider(responses=[packet_answer])
    service = CopilotService(provider=provider)

    result = service.answer_investigation_question(
        analysis_session,
        finding.id,
        question="这个发现的主要原因是什么？",
        actor="陈晨",
        batch_id=run.metric_snapshot.batch_id,
        metric_snapshot_id=run.metric_snapshot_id,
        analysis_run_id=run.id,
    )

    assert result.outcome == "accepted"
    assert result.interaction_id
    stored = analysis_session.get(CopilotInteraction, uuid.UUID(result.interaction_id))
    assert stored is not None
    assert stored.outcome == "accepted"
    assert stored.actor == "陈晨"
    assert stored.context_digest == result.context_digest
    assert stored.request_references["finding_id"] == str(finding.id)


def test_uncited_numbers_are_rejected_and_audited(analysis_session: Session) -> None:
    run = publish_analysis_run(analysis_session)
    finding = _top_finding(analysis_session)
    bogus = CopilotResponse(
        answer=StructuredAnswer(
            judgments=(CopilotSection(text="影响约为 -9999999.1234 元", citations=()),),
        ),
        provider="scripted",
        model="scripted-v1",
    )
    provider = ScriptedProvider(responses=[bogus])
    service = CopilotService(provider=provider)

    with pytest.raises(CopilotValidationError) as error:
        service.answer_investigation_question(
            analysis_session,
            finding.id,
            question="为什么？",
            actor="陈晨",
            batch_id=run.metric_snapshot.batch_id,
            metric_snapshot_id=run.metric_snapshot_id,
            analysis_run_id=run.id,
        )
    assert any("uncited_number" in reason for reason in error.value.reasons)

    analysis_session.commit()
    stored = analysis_session.scalars(select(CopilotInteraction)).all()
    assert len(stored) == 1
    assert stored[0].outcome == "rejected"


def test_mapping_explanation_use_case(analysis_session: Session) -> None:
    run = publish_analysis_run(analysis_session)
    provider = ScriptedProvider(
        responses=[
            CopilotResponse(
                answer=StructuredAnswer(
                    judgments=(
                        CopilotSection(
                            text="字段映射基于稳定字段 ID 与别名匹配。",
                            citations=(),
                        ),
                    ),
                ),
                provider="scripted",
                model="scripted-v1",
            )
        ]
    )
    service = CopilotService(provider=provider)
    result = service.explain_mapping(
        analysis_session,
        run.import_version_id,
        actor="flow.pipeline",
    )
    assert result.outcome == "accepted"


def test_report_outline_prohibits_unapproved_findings(analysis_session: Session) -> None:
    run = publish_analysis_run(analysis_session)
    finding = _top_finding(analysis_session)
    assert finding.status == "candidate"
    provider = ScriptedProvider(
        responses=[
            CopilotResponse(
                answer=StructuredAnswer(
                    judgments=(
                        CopilotSection(
                            text="建议纳入该发现。",
                            citations=(f"finding:{finding.id}",),
                        ),
                    ),
                ),
                provider="scripted",
                model="scripted-v1",
            )
        ]
    )
    service = CopilotService(provider=provider)
    with pytest.raises(CopilotValidationError) as error:
        service.draft_report_outline(
            analysis_session,
            run.metric_snapshot.batch_id,
            actor="陈晨",
        )
    assert any("unapproved_finding" in reason for reason in error.value.reasons)
