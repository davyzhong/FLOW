"""Packet builders that serialize governed domain context for the copilot."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from flow_api.investigation.repositories import (
    FindingBinding,
    InvestigationRepository,
)


def investigation_packet(session: Session, binding: FindingBinding) -> dict[str, Any]:
    repository = InvestigationRepository()
    finding = binding.finding
    metric = binding.metric_definition
    drivers = repository.drivers(session, finding)
    evidence = repository.evidence(session, finding)
    result = binding.result

    packet: dict[str, Any] = {
        "batch": {
            "id": str(binding.snapshot.batch_id),
        },
        "snapshot": {
            "id": str(binding.snapshot.id),
            "version": int(binding.snapshot.version),
            "engine_version": str(binding.snapshot.engine_version),
            "definition_set_id": str(binding.snapshot.definition_set_id),
            "fingerprint": str(binding.snapshot.fingerprint),
            "run": {
                "id": str(binding.run.id),
                "policy_id": str(binding.run.policy_id),
                "policy_set_hash": str(binding.run.policy_set_hash),
                "engine_version": str(binding.run.engine_version),
            },
        },
        "metric_definitions": (
            [
                {
                    "code": str(metric.metric_code),
                    "name": str(metric.name),
                    "version": int(metric.version),
                    "formula": str(metric.formula),
                    "unit": str(metric.unit),
                    "business_definition": str(metric.business_definition),
                }
            ]
            if metric is not None
            else []
        ),
        "findings": [
            {
                "id": str(finding.id),
                "title": str(finding.title),
                "type": finding.finding_type,
                "status": str(finding.status),
                "impact_amount": str(finding.impact_amount),
                "confidence": str(finding.confidence),
                "fact_statement": finding.fact_statement,
                "comparison_basis": finding.comparison_basis,
                "result": (
                    {
                        "playbook_code": str(result.playbook_code),
                        "status": str(result.status),
                        "impact_amount": str(result.impact_amount),
                        "reconciliation_difference": str(result.reconciliation_difference),
                        "reconciliation_tolerance": str(result.reconciliation_tolerance),
                    }
                    if result is not None
                    else None
                ),
                "drivers": [
                    {
                        "code": str(driver.driver_code),
                        "contribution_amount": str(driver.contribution_amount),
                        "contribution_ratio": (
                            str(driver.contribution_ratio)
                            if driver.contribution_ratio is not None
                            else None
                        ),
                        "calculation_method": driver.calculation_method,
                    }
                    for driver in drivers
                ],
                "evidence": [
                    {
                        "id": str(item.id),
                        "status": str(item.status),
                        "type": str(item.evidence_type),
                        "object_id": str(item.object_id),
                    }
                    for item in evidence
                ],
            }
        ],
    }
    return packet


def mapping_packet(session: Session, import_version: Any) -> dict[str, Any]:
    issues = InvestigationRepository().quality_issues(session, import_version)
    batch = import_version.batch
    return {
        "batch": {
            "id": str(batch.id),
            "name": str(batch.name),
        },
        "snapshot": {},
        "metric_definitions": [],
        "findings": [],
        "import_version": {
            "id": str(import_version.id),
            "sequence": int(import_version.sequence),
            "status": str(import_version.status),
            "quality_issues": [
                {
                    "severity": str(issue.severity),
                    "code": str(issue.code),
                    "message": str(issue.message),
                }
                for issue in issues
            ],
        },
    }


__all__ = ["investigation_packet", "mapping_packet"]
