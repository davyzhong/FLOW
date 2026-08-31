from __future__ import annotations

import json
from pathlib import Path

from flow_api.data_contract.contract import load_contract
from flow_api.data_contract.semantic import compare_semantics
from flow_api.fixtures.known_answers import calculate_known_answers
from flow_api.intake.detector import profile_workbook
from flow_api.intake.extractor import extract_candidate_package
from flow_api.intake.mapping import load_aliases, propose_mapping
from flow_api.intake.quality import evaluate_quality
from flow_api.intake.transforms import load_transform_rules


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    contract = load_contract(repository_root / "templates/excel/flow_v1_contract.yaml")
    aliases = load_aliases(repository_root / "config/intake/flow_v1_aliases.yaml")
    transforms = load_transform_rules(repository_root / "config/intake/flow_v1_transforms.yaml")
    paths = {
        "standard": repository_root / "fixtures/workbooks/flow_standard_v1.xlsx",
        "external": repository_root / "fixtures/workbooks/external_logistics_nonstandard_v1.xlsx",
    }
    expected_answers = json.loads(
        (repository_root / "fixtures/expected/known_answers.json").read_text(
            encoding="utf-8"
        )
    )
    results: dict[str, object] = {}
    candidates = {}
    for name, path in paths.items():
        profile = profile_workbook(path)
        proposal = propose_mapping(profile, contract, aliases)
        candidate = extract_candidate_package(path, profile, proposal, contract, transforms)
        quality = evaluate_quality(candidate.package, contract, proposal)
        candidates[name] = candidate
        answers = calculate_known_answers(candidate.package)
        results[name] = {
            "sha256": candidate.source_sha256,
            "sheet_count": profile.sheet_count,
            "mapping_hash": proposal.mapping_hash,
            "unresolved_sheets": len(proposal.unresolved_sheet_ids),
            "unresolved_required_fields": sum(
                len(sheet.unresolved_required_fields) for sheet in proposal.sheets
            ),
            "lineage_values": len(candidate.lineage),
            "blocking_issues": len(quality.blocking_issues),
            "warning_issues": len(quality.warning_issues),
            "reconciliations_passed": all(check.passed for check in quality.reconciliations),
            "known_answers_match": answers == expected_answers,
            "row_counts": answers["row_counts"],
            "analysis_headline": answers["headline_totals"]["analysis"],
        }
    semantic_differences = compare_semantics(
        candidates["standard"].package, candidates["external"].package
    )
    results["semantic_differences"] = list(semantic_differences)
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    if semantic_differences:
        raise SystemExit("FLOW intake semantic comparison failed")


if __name__ == "__main__":
    main()
