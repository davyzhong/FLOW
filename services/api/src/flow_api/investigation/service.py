"""Governed Investigation read and review service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from flow_api.infrastructure.models.analytics import (
    Conclusion,
    Evidence,
    Finding,
    ReviewEvent,
)
from flow_api.investigation import state_machines
from flow_api.investigation.models import (
    AnalysisResultContext,
    ConclusionState,
    ConclusionUpsertRequest,
    DriverLine,
    EvidenceDecisionRequest,
    EvidenceLine,
    FindingContext,
    FindingTransitionRequest,
    InvestigationContext,
    InvestigationIdentity,
    MetricContext,
    MutationAcknowledgement,
    QualityIssueLine,
    ReconciliationLine,
    ReviewLine,
    SourceRecordLine,
)
from flow_api.investigation.repositories import (
    OPERATING_PLAYBOOKS,
    FindingBinding,
    InvestigationNotFoundError,
    InvestigationRepository,
)

DEFAULT_SOURCE_RECORD_LIMIT = 12
MAX_SOURCE_RECORD_LIMIT = 100


class InvestigationService:
    def __init__(self, repository: InvestigationRepository | None = None) -> None:
        self.repository = repository or InvestigationRepository()

    # ------------------------------------------------------------------ read

    def get_context(
        self,
        session: Session,
        finding_id: UUID,
        *,
        batch_id: UUID | None = None,
        metric_snapshot_id: UUID | None = None,
        analysis_run_id: UUID | None = None,
        source_record_limit: int = DEFAULT_SOURCE_RECORD_LIMIT,
    ) -> InvestigationContext:
        binding = self.repository.load_binding(
            session,
            finding_id,
            batch_id=batch_id,
            metric_snapshot_id=metric_snapshot_id,
            analysis_run_id=analysis_run_id,
        )
        finding = binding.finding
        metric_definition = binding.metric_definition
        if metric_definition is None and binding.result is not None:
            metric_definition = self.repository.metric_definition_for_playbook(
                session, binding, playbook_code=str(binding.result.playbook_code)
            )
        labels = self.repository.label_maps(session)
        segments, products, regions, customers = labels

        drivers = self.repository.drivers(session, finding)
        evidence = self.repository.evidence(session, finding)
        reviews = self.repository.reviews(session, finding)
        quality = self.repository.quality_issues(session, binding.import_version)
        reconciliations = self.repository.reconciliations(session, binding.import_version)
        conclusion = session.scalar(select(Conclusion).where(Conclusion.finding_id == finding.id))

        source_records = self._source_records(
            session, binding, limit=min(max(source_record_limit, 1), MAX_SOURCE_RECORD_LIMIT)
        )
        evidence_statuses = tuple(str(item.status) for item in evidence)
        blockers = self._eligibility_blockers(
            finding.status,
            evidence_statuses,
            state_machines.conclusion_is_complete(conclusion),
        )

        return InvestigationContext(
            identity=InvestigationIdentity(
                finding_id=str(finding.id),
                batch_id=str(binding.snapshot.batch_id),
                metric_snapshot_id=str(binding.snapshot.id),
                analysis_run_id=str(binding.run.id),
            ),
            finding=FindingContext(
                finding_id=str(finding.id),
                finding_type=finding.finding_type,
                title=finding.title,
                status=str(finding.status),
                impact_amount=str(finding.impact_amount),
                unit="CNY",
                confidence=str(finding.confidence),
                business_meaning=finding.business_meaning,
                fact_statement=finding.fact_statement,
                comparison_basis=finding.comparison_basis,
                total_score=str(finding.total_score) if finding.total_score else None,
                policy_version=finding.policy_version,
                created_at=finding.created_at.isoformat(),
            ),
            result=(
                AnalysisResultContext(
                    analysis_result_id=str(binding.result.id),
                    playbook_code=str(binding.result.playbook_code),
                    playbook_version=int(binding.result.playbook_version),
                    status=str(binding.result.status),
                    comparison_basis=str(binding.result.comparison_basis),
                    impact_amount=str(binding.result.impact_amount),
                    unit=str(binding.result.unit),
                    reconciliation_difference=str(binding.result.reconciliation_difference),
                    reconciliation_tolerance=str(binding.result.reconciliation_tolerance),
                    source_record_count=int(binding.result.source_record_count),
                    degradation_code=binding.result.degradation_code,
                    degradation_message=binding.result.degradation_message,
                )
                if binding.result is not None
                else None
            ),
            metric=MetricContext(
                metric_code=(
                    str(metric_definition.metric_code)
                    if metric_definition
                    else None
                ),
                metric_name=(
                    str(metric_definition.name) if metric_definition else None
                ),
                business_definition=(
                    str(metric_definition.business_definition)
                    if metric_definition
                    else None
                ),
                formula=(
                    str(metric_definition.formula) if metric_definition else None
                ),
                unit=str(metric_definition.unit) if metric_definition else None,
                definition_version=(
                    int(metric_definition.version) if metric_definition else None
                ),
                engine_version=str(binding.run.engine_version),
                policy_id=str(binding.run.policy_id),
                policy_set_hash=str(binding.run.policy_set_hash),
            ),
            drivers=tuple(
                DriverLine(
                    position=int(driver.position),
                    driver_code=str(driver.driver_code),
                    calculation_method=driver.calculation_method,
                    contribution_amount=str(driver.contribution_amount),
                    contribution_ratio=(
                        str(driver.contribution_ratio) if driver.contribution_ratio else None
                    ),
                )
                for driver in drivers
            ),
            evidence=tuple(
                EvidenceLine(
                    evidence_id=str(item.id),
                    status=str(item.status),
                    evidence_type=str(item.evidence_type),
                    object_type=str(item.object_type),
                    object_id=str(item.object_id),
                    note=item.note,
                    evidence_digest=item.evidence_digest,
                )
                for item in evidence
            ),
            reviews=tuple(
                ReviewLine(
                    sequence=int(item.sequence),
                    reviewer=str(item.reviewer),
                    decision=str(item.decision),
                    comment=item.comment,
                    created_at=item.created_at.isoformat(),
                )
                for item in reviews
            ),
            quality_issues=tuple(
                QualityIssueLine(
                    severity=str(item.severity),
                    code=str(item.code),
                    message=str(item.message),
                    acknowledged=item.acknowledgement is not None,
                )
                for item in quality
            ),
            reconciliations=tuple(
                ReconciliationLine(
                    reconciliation_code=str(item.reconciliation_code),
                    passed=bool(item.passed),
                    expected_value=item.expected_value,
                    actual_value=item.actual_value,
                )
                for item in reconciliations
            ),
            conclusion=(
                ConclusionState(
                    exists=True,
                    verified_facts=str(conclusion.verified_facts),
                    analysis_judgment=str(conclusion.analysis_judgment),
                    open_questions=str(conclusion.open_questions),
                    recommendation=str(conclusion.recommendation),
                )
                if conclusion
                else ConclusionState(exists=False)
            ),
            source_records=source_records,
            eligibility_blockers=blockers,
        )

    def _source_records(
        self,
        session: Session,
        binding: FindingBinding,
        *,
        limit: int,
    ) -> tuple[SourceRecordLine, ...]:
        if binding.result is None:
            return ()
        playbook = str(binding.result.playbook_code)
        if playbook == "ar_cash_impact":
            rows = self.repository.ar_records(session, binding, limit=limit)
            _, _, _, customers = self.repository.label_maps(session)
            return tuple(
                SourceRecordLine(
                    fact_id=str(row.fact_id),
                    month_key=row.month_key,
                    labels={
                        "客户": customers.get(row.customer_id, str(row.customer_id)),
                        "发票号": row.invoice_number or "—",
                        "账龄区间": row.aging_bucket or "—",
                    },
                    values={
                        "应收余额": row.receivable_balance,
                        "到期金额": row.due_amount,
                        "逾期金额": row.overdue_amount,
                        "已回款": row.collected_amount,
                    },
                    source_file_name=row.lineage.file_name,
                    sheet_name=row.lineage.sheet_name,
                    source_row=row.lineage.source_row,
                    source_column=row.lineage.source_column,
                )
                for row in rows
            )
        if playbook in OPERATING_PLAYBOOKS:
            operating_rows = self.repository.operating_records(
                session, binding, playbook_code=playbook, limit=limit
            )
            segments, products, regions, customers = self.repository.label_maps(session)
            return tuple(
                SourceRecordLine(
                    fact_id=str(row.fact_id),
                    month_key=row.month_key,
                    labels={
                        "客户": customers.get(row.customer_id, str(row.customer_id)),
                        "客户群": row.segment_name or "—",
                        "物流产品": products.get(
                            row.logistics_product_id, str(row.logistics_product_id)
                        ),
                        "区域": regions.get(row.region_id, str(row.region_id)),
                    },
                    values={
                        "订单量": row.order_count,
                        "收入": row.revenue,
                        "仓储成本": row.warehousing_cost,
                        "运输成本": row.transportation_cost,
                        "其他直接成本": row.other_direct_cost,
                    },
                    source_file_name=row.lineage.file_name,
                    sheet_name=row.lineage.sheet_name,
                    source_row=row.lineage.source_row,
                    source_column=row.lineage.source_column,
                )
                for row in operating_rows
            )
        return ()

    def _eligibility_blockers(
        self,
        status: str,
        evidence_statuses: tuple[str, ...],
        conclusion_complete: bool,
    ) -> tuple[str, ...]:
        blockers: list[str] = []
        if status == "candidate":
            blockers.append("finding_not_submitted")
        elif status == "approved":
            return ()
        elif status == "rejected":
            blockers.append("finding_rejected")
        if any(item == "pending" for item in evidence_statuses):
            blockers.append("evidence_pending")
        if any(item == "rejected" for item in evidence_statuses):
            blockers.append("evidence_rejected")
        if not conclusion_complete:
            blockers.append("conclusion_incomplete")
        return tuple(blockers)

    # ----------------------------------------------------------------- write

    def decide_evidence(
        self,
        session: Session,
        finding_id: UUID,
        evidence_id: UUID,
        request: EvidenceDecisionRequest,
    ) -> MutationAcknowledgement:
        finding = self._existing_finding(session, finding_id)
        evidence = session.get(Evidence, evidence_id)
        if evidence is None or evidence.finding_id != finding.id:
            raise InvestigationNotFoundError(f"evidence does not exist: {evidence_id}")
        event = state_machines.apply_evidence_decision(
            session,
            evidence,
            request.decision,
            reviewer=request.reviewer,
            comment=request.comment,
        )
        session.commit()
        return MutationAcknowledgement(
            finding_id=str(finding.id),
            status=str(finding.status),
            review_sequence=int(event.sequence),
            decision=str(event.decision),
        )

    def save_conclusion(
        self,
        session: Session,
        finding_id: UUID,
        request: ConclusionUpsertRequest,
    ) -> MutationAcknowledgement:
        finding = self._existing_finding(session, finding_id)
        conclusion = session.scalar(select(Conclusion).where(Conclusion.finding_id == finding.id))
        if conclusion is None:
            conclusion = Conclusion(finding=finding)
            session.add(conclusion)
        conclusion.verified_facts = request.verified_facts
        conclusion.analysis_judgment = request.analysis_judgment
        conclusion.open_questions = request.open_questions
        conclusion.recommendation = request.recommendation
        session.flush()
        event: ReviewEvent | None
        if finding.status == "candidate":
            event = state_machines.apply_finding_decision(
                session,
                finding,
                "submitted",
                reviewer=request.editor,
                comment="结论已更新并提交复核",
            )
        else:
            event = self.repository.latest_review_event(session, finding)
            if event is None:
                raise InvestigationNotFoundError("finding has no review history")
        assert event is not None
        session.commit()
        return MutationAcknowledgement(
            finding_id=str(finding.id),
            status=str(finding.status),
            review_sequence=int(event.sequence),
            decision=str(event.decision),
        )

    def transition_finding(
        self,
        session: Session,
        finding_id: UUID,
        request: FindingTransitionRequest,
    ) -> MutationAcknowledgement:
        finding = self._existing_finding(session, finding_id)
        event = state_machines.apply_finding_decision(
            session,
            finding,
            request.decision,
            reviewer=request.reviewer,
            comment=request.comment,
        )
        session.commit()
        return MutationAcknowledgement(
            finding_id=str(finding.id),
            status=str(finding.status),
            review_sequence=int(event.sequence),
            decision=str(event.decision),
        )

    def _existing_finding(self, session: Session, finding_id: UUID) -> Finding:
        binding = self.repository.load_binding(
            session,
            finding_id,
            batch_id=None,
            metric_snapshot_id=None,
            analysis_run_id=None,
        )
        return binding.finding


__all__ = [
    "InvestigationService",
]
