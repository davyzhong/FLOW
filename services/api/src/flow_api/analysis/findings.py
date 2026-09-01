from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from flow_api.analysis.decimal_math import money, ratio
from flow_api.analysis.models import (
    AnalysisResultDraft,
    EvidenceReference,
    FindingDraft,
    FrozenModel,
    ScoreComponentDraft,
)
from flow_api.analysis.policy import AnalysisPolicy


class QualificationOutcome(FrozenModel):
    finding: FindingDraft | None
    suppression_reasons: tuple[str, ...]


ABNORMAL_DIRECTIONS = {
    "revenue_growth": "positive",
    "gross_profit_deterioration": "negative",
    "operating_profit_deterioration": "negative",
    "fulfillment_cost_increase": "positive",
    "ar_cash_deterioration": "negative",
}


DRIVER_LABELS = {
    "volume": "业务量",
    "mix": "业务结构",
    "price": "单价",
    "revenue_volume": "收入业务量",
    "revenue_mix": "收入结构",
    "revenue_price": "收入单价",
    "warehousing_cost": "仓储成本",
    "transportation_cost": "运输成本",
    "other_direct_cost": "其他直接成本",
    "operating_expense": "期间费用",
    "efficiency": "件单效率",
    "rate": "单位成本率",
}


FINDING_LABELS = {
    "revenue_growth": ("收入增长", "收入规模扩大"),
    "gross_profit_deterioration": ("毛利下降", "毛利空间收窄"),
    "operating_profit_deterioration": ("经营利润下降", "经营盈利承压"),
    "fulfillment_cost_increase": ("履约成本增加", "履约成本压力上升"),
    "ar_cash_deterioration": ("应收资金占用增加", "营运资金现金占用扩大"),
}


def _score_component(
    code: str,
    *,
    raw: Decimal,
    normalized: Decimal,
    weight: Decimal,
    trace: dict[str, str],
) -> ScoreComponentDraft:
    normalized_six = ratio(normalized)
    return ScoreComponentDraft(
        component_code=code,  # type: ignore[arg-type]
        raw_value=raw,
        normalized_score=normalized_six,
        weight=weight,
        weighted_score=ratio(normalized_six * weight),
        calculation_trace=trace,
    )


def calculate_score_components(
    *,
    finding_type: str,
    impact_amount: Decimal,
    persistence_flags: tuple[bool, ...],
    verified_evidence_count: int,
    required_evidence_count: int,
    policy: AnalysisPolicy,
) -> tuple[ScoreComponentDraft, ...]:
    high_amount = policy.high_materiality_amount[finding_type]
    materiality = min(abs(impact_amount) / high_amount, Decimal("1")) * Decimal("100")
    if persistence_flags:
        persistence = (
            Decimal(sum(persistence_flags))
            / Decimal(len(persistence_flags))
            * Decimal("100")
        )
        persistence_trace = {
            "true_periods": str(sum(persistence_flags)),
            "observed_periods": str(len(persistence_flags)),
        }
    else:
        persistence = Decimal("50")
        persistence_trace = {"policy": "point_in_time_neutral"}
    if required_evidence_count <= 0:
        raise ValueError("required evidence count must be positive")
    evidence_score = (
        Decimal(verified_evidence_count)
        / Decimal(required_evidence_count)
        * Decimal("100")
    )
    relevance = policy.management_relevance[finding_type]
    weights = policy.ranking_weights
    return (
        _score_component(
            "materiality",
            raw=abs(impact_amount),
            normalized=materiality,
            weight=weights["materiality"],
            trace={"high_materiality_amount": str(high_amount)},
        ),
        _score_component(
            "persistence",
            raw=Decimal(sum(persistence_flags)),
            normalized=persistence,
            weight=weights["persistence"],
            trace=persistence_trace,
        ),
        _score_component(
            "evidence_completeness",
            raw=Decimal(verified_evidence_count),
            normalized=evidence_score,
            weight=weights["evidence_completeness"],
            trace={"required_evidence_count": str(required_evidence_count)},
        ),
        _score_component(
            "management_relevance",
            raw=relevance,
            normalized=relevance,
            weight=weights["management_relevance"],
            trace={"finding_type": finding_type},
        ),
    )


def _fingerprint(
    *, run_identity: str, finding_type: str, result: AnalysisResultDraft
) -> str:
    payload = {
        "run_identity": run_identity,
        "finding_type": finding_type,
        "playbook_code": result.playbook_code,
        "playbook_version": result.playbook_version,
        "comparison_basis": result.comparison_basis,
        "impact_amount": str(result.impact_amount),
        "drivers": [
            {
                "code": driver.driver_code,
                "amount": str(driver.contribution_amount),
            }
            for driver in result.drivers
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _direction_supported(finding_type: str, impact: Decimal) -> bool:
    direction = ABNORMAL_DIRECTIONS.get(finding_type)
    return (direction == "negative" and impact < 0) or (
        direction == "positive" and impact > 0
    )


def _verified_evidence_types(evidence: tuple[EvidenceReference, ...]) -> set[str]:
    return {
        item.evidence_type
        for item in evidence
        if item.verification_trace.get("verified") is True
    }


def _wording(
    finding_type: str, result: AnalysisResultDraft
) -> tuple[str, str, str]:
    title, meaning = FINDING_LABELS[finding_type]
    driver_text = "；".join(
        f"{DRIVER_LABELS.get(driver.driver_code, driver.driver_code)}贡献"
        f"{driver.contribution_amount}元"
        for driver in result.drivers
        if driver.contribution_amount != 0
    )
    fact = f"{title}，同比影响{result.impact_amount}元"
    if driver_text:
        fact = f"{fact}；数学分解为：{driver_text}"
    return title, fact, meaning


def qualify_finding(
    *,
    result: AnalysisResultDraft,
    finding_type: str,
    policy: AnalysisPolicy,
    evidence: tuple[EvidenceReference, ...],
    persistence_flags: tuple[bool, ...],
    run_identity: str,
    expected_run_identity: str,
    existing_fingerprints: frozenset[str],
) -> QualificationOutcome:
    reasons: list[str] = []
    if result.status != "complete":
        reasons.append("result_not_complete")
    if abs(result.reconciliation_difference) > result.reconciliation_tolerance:
        reasons.append("invariant_failed")
    required_types = set(policy.required_evidence)
    verified_types = _verified_evidence_types(evidence)
    if not required_types.issubset(verified_types):
        reasons.append("evidence_incomplete")
    if run_identity != expected_run_identity:
        reasons.append("run_identity_mismatch")
    threshold = policy.qualification_materiality.get(finding_type)
    if threshold is None or finding_type not in policy.high_materiality_amount:
        reasons.append("unsupported_finding_type")
    elif abs(result.impact_amount) < threshold:
        reasons.append("below_materiality")
    if finding_type not in ABNORMAL_DIRECTIONS or not _direction_supported(
        finding_type, result.impact_amount
    ):
        reasons.append("unsupported_direction")
    if reasons:
        return QualificationOutcome(finding=None, suppression_reasons=tuple(reasons))

    fingerprint = _fingerprint(
        run_identity=run_identity, finding_type=finding_type, result=result
    )
    if fingerprint in existing_fingerprints:
        return QualificationOutcome(
            finding=None, suppression_reasons=("duplicate_fingerprint",)
        )
    components = calculate_score_components(
        finding_type=finding_type,
        impact_amount=result.impact_amount,
        persistence_flags=persistence_flags,
        verified_evidence_count=len(required_types & verified_types),
        required_evidence_count=len(required_types),
        policy=policy,
    )
    total_score = ratio(
        sum((component.weighted_score for component in components), start=Decimal("0"))
    )
    title, fact, meaning = _wording(finding_type, result)
    finding = FindingDraft(
        finding_type=finding_type,
        playbook_code=result.playbook_code,
        title=title,
        fact_statement=fact,
        business_meaning=meaning,
        comparison_basis=result.comparison_basis,
        impact_amount=money(result.impact_amount),
        confidence=Decimal("1"),
        total_score=total_score,
        policy_version=policy.policy_id,
        fingerprint=fingerprint,
        score_components=components,
        evidence=evidence,
        qualification_trace={
            "gates": {
                "result_complete": True,
                "invariant_passed": True,
                "evidence_complete": True,
                "materiality_passed": True,
                "direction_supported": True,
                "run_identity_matched": True,
                "fingerprint_unique": True,
            }
        },
    )
    return QualificationOutcome(finding=finding, suppression_reasons=())


def rank_findings(findings: tuple[FindingDraft, ...]) -> tuple[FindingDraft, ...]:
    return tuple(
        sorted(
            findings,
            key=lambda item: (-item.total_score, -abs(item.impact_amount), item.fingerprint),
        )
    )


__all__ = [
    "QualificationOutcome",
    "calculate_score_components",
    "qualify_finding",
    "rank_findings",
]
