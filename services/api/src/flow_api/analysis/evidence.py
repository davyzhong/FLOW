from __future__ import annotations

import hashlib
import json

from flow_api.analysis.models import AnalysisResultDraft, EvidenceReference
from flow_api.analysis.repositories import AnalysisSourceBundle


def _combined_source_digest(bundle: AnalysisSourceBundle) -> str:
    canonical = json.dumps(bundle.source_digests, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_verified_evidence(
    result: AnalysisResultDraft, bundle: AnalysisSourceBundle
) -> tuple[EvidenceReference, ...]:
    return (
        EvidenceReference(
            evidence_type="metric_value",
            object_type="metric",
            object_id=f"metric-snapshot:{bundle.snapshot_id}",
            verification_trace={
                "verified": True,
                "metric_value_count": len(bundle.metric_values),
            },
        ),
        EvidenceReference(
            evidence_type="calculation",
            object_type="analysis_result",
            object_id=f"draft:{result.playbook_code}:{result.comparison_basis}",
            verification_trace={
                "verified": True,
                "playbook_version": result.playbook_version,
            },
        ),
        EvidenceReference(
            evidence_type="source_record_set",
            object_type="canonical_record_set",
            object_id=f"import-version:{bundle.import_version_id}",
            digest=_combined_source_digest(bundle),
            verification_trace={
                "verified": True,
                "source_record_count": result.source_record_count,
                "source_digests": bundle.source_digests,
            },
        ),
        EvidenceReference(
            evidence_type="lineage",
            object_type="lineage",
            object_id=f"snapshot:{bundle.snapshot_id}:import:{bundle.import_version_id}",
            verification_trace={"verified": True},
        ),
        EvidenceReference(
            evidence_type="invariant",
            object_type="invariant",
            object_id=f"invariant:{result.playbook_code}:{result.comparison_basis}",
            verification_trace={
                "verified": True,
                "difference": str(result.reconciliation_difference),
                "tolerance": str(result.reconciliation_tolerance),
            },
        ),
    )


__all__ = ["build_verified_evidence"]
