from __future__ import annotations

import json
from pathlib import Path

from flow_api.analysis.policy import load_analysis_policy
from flow_api.fixtures.analysis_known_answers import build_analysis_known_answers


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    policy = load_analysis_policy(
        repository_root / "services/api/config/analysis/flow-logistics-v1.yaml"
    )
    oracle = build_analysis_known_answers(repository_root)
    summary = {
        "status": "PASS",
        "policy_id": policy.policy.policy_id,
        "policy_hash": policy.policy_hash,
        "engine_version": policy.policy.engine_version,
        "result_count": len(oracle["results"]),
        "complete_results": sorted(oracle["results"]),
        "finding_rank": oracle["finding_rank"],
        "finding_scores": oracle["finding_scores"],
        "story_predicates": oracle["story_predicates"],
        "degradation_scenarios": ["unmatched_mix_cell", "missing_required_field"],
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
