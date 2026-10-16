#!/usr/bin/env python3
"""为公开财报 C 级验收冻结活动样本、答案集与输入文件身份。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_answer_set_l1 import source_paths  # noqa: E402
from public_statement_row_identity import (  # noqa: E402
    apply_public_row_identity_corrections,
)

SOURCES_MAP = Path("config/statements/answer_set_sources.yaml")
ANSWER_SET = Path("config/statements/answer_set_l1_v6.yaml")
CORRECTION_MAP = Path("validation/financial_reports/corrections/public-row-identity-map-v1.csv")
SOURCE_MANIFEST = Path("validation/financial_reports/manifest.yaml")
FREEZE_OUTPUT = Path("validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml")
FREEZE_GENERATOR = Path("scripts/build_public_financial_sample_freeze.py")
L1_GENERATOR = Path("scripts/build_answer_set_l1.py")
ROW_IDENTITY_ADAPTER = Path("scripts/public_statement_row_identity.py")
L0_BENCHMARK = Path("scripts/accuracy_benchmark.py")
EXPECTED_IMPLEMENTATION_SHA = "eb2b7f3cbadec0c36eb4b36473c6321d69aa4fff"
EXPECTED_CI_RUN = "36478301484"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"预期 YAML 对象：{path}")
    return value


def _relative(path: Path, repo: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def _independent_validation_audit(
    repo: Path, reports: list[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    holdouts: list[dict[str, Any]] = []
    claim_mismatches: list[str] = []
    historical_claim_mismatches: list[str] = []
    oracle_sample_ids: set[str] = set()
    for row in registry.get("holdouts", []):
        precise = next(
            (
                value
                for key, value in row.items()
                if key.startswith("key_items_precise_") and isinstance(value, dict)
            ),
            None,
        )
        if not precise or not precise.get("oracle_file"):
            continue
        oracle_path = repo / precise["oracle_file"]
        if not oracle_path.is_file():
            raise FileNotFoundError(f"登记的 oracle 文件不存在：{precise['oracle_file']}")
        oracle_payload = _load_yaml(oracle_path)
        sample_id = str(row["id"])
        oracle_sample_ids.add(str(oracle_payload.get("sample_id", "")))
        actual_sha = _sha256(oracle_path)
        claimed_sha = str(precise.get("oracle_sha256", ""))
        previous_claim = str(precise.get("oracle_sha256_previous_claim", ""))
        claim_matches = actual_sha == claimed_sha
        if not claim_matches:
            claim_mismatches.append(sample_id)
        if previous_claim and previous_claim != actual_sha:
            historical_claim_mismatches.append(sample_id)
        holdouts.append(
            {
                "sample": sample_id,
                "oracle_file": precise["oracle_file"],
                "claimed_sha256": claimed_sha,
                "previous_claim_sha256": previous_claim or None,
                "actual_sha256": actual_sha,
                "claim_matches": claim_matches,
                "key_items": len(oracle_payload.get("key_items", [])),
                "supplementary_lines": len(oracle_payload.get("supplementary_lines", [])),
                "full_report_oracle": oracle_payload.get("coverage_scope") == "full_report_rows",
            }
        )

    frozen_sample_ids = {row["sample"] for row in reports}
    full_row_oracles = sum(
        row["sample"] in oracle_sample_ids and row["full_report_oracle"] for row in holdouts
    )
    legacy_path = Path("validation/financial_reports/holdout_runs/2026-09-24/summary.json")
    legacy = json.loads((repo / legacy_path).read_text(encoding="utf-8"))
    legacy_samples = ("sf_2026h1", "tencent_fy2025", "zto_2026q1")
    legacy_totals = {
        key: sum(int(legacy[sample].get(key, 0)) for sample in legacy_samples)
        for key in ("total", "rows_extracted", "matched", "mismatched", "not_comparable")
    }
    new_holdout_samples = ("xiaomi_2026h1", "alibaba_fy2027q1")
    run_artifacts = sorted(
        _relative(path, repo)
        for sample in new_holdout_samples
        for path in (repo / "validation/financial_reports/holdout_runs").rglob(
            f"{sample}_diff.json"
        )
    )
    cross_review_path = Path("docs/80_reviews/ai-cross-review/results/gpt-6-astra-2026-09-25.md")
    adjudication_path = Path("docs/80_reviews/ai-cross-review/results/adjudication.md")
    return {
        "full_row_oracles_for_frozen_reports": full_row_oracles,
        "frozen_samples_without_full_row_oracle": sorted(frozen_sample_ids - oracle_sample_ids),
        "registered_holdout_oracles": len(holdouts),
        "holdout_oracles": holdouts,
        "oracle_claim_mismatches": sorted(claim_mismatches),
        "historical_oracle_claim_mismatches": sorted(historical_claim_mismatches),
        "legacy_first_run": {
            "artifact": legacy_path.as_posix(),
            "artifact_sha256": _sha256(repo / legacy_path),
            **legacy_totals,
        },
        "drawn_new_holdout_run_artifacts_found": run_artifacts,
        "cross_review": {
            "artifact": cross_review_path.as_posix(),
            "artifact_sha256": _sha256(repo / cross_review_path),
            "adjudication": adjudication_path.as_posix(),
            "adjudication_sha256": _sha256(repo / adjudication_path),
            "is_numeric_full_row_oracle": False,
            "is_rendered_report_blind_review": False,
        },
        "c_level_passed": False,
    }


def _l0_source_value_count(payload: dict[str, Any]) -> int:
    total = 0
    for rows in payload["statements"].values():
        for row in rows:
            total += sum(
                value is not None
                for key, value in row.items()
                if key not in {"item", "page", "source_text_label"}
            )
    return total


def _l0_key(
    payload: dict[str, Any], column: str, item: str, statement: str
) -> tuple[str, str, str, str]:
    aliases = {
        "期末余额": "value_end",
        "期初余额": "value_begin",
        "本期发生额": "value_current",
        "上期发生额": "value_prior",
        "本期金额": "value_current",
        "上期金额": "value_prior",
    }
    return (
        payload["source_pdf"],
        statement,
        item,
        aliases.get(column, column),
    )


def build_manifest(
    repo: Path = ROOT,
    *,
    implementation_sha: str = EXPECTED_IMPLEMENTATION_SHA,
) -> dict[str, Any]:
    """严格校验并构建确定性冻结清单；不读取或改写任何数据库。"""
    if not re.fullmatch(r"[0-9a-f]{40}", implementation_sha):
        raise ValueError("implementation_sha 必须是完整 40 位 Git commit SHA")

    mapping_payload = _load_yaml(repo / SOURCES_MAP)
    registry_payload = _load_yaml(repo / SOURCE_MANIFEST)
    mapping_rows = mapping_payload.get("reports")
    if not isinstance(mapping_rows, list):
        raise ValueError("答案集报告身份映射缺少 reports 列表")
    mapping = {row["sample"]: row for row in mapping_rows}
    if len(mapping) != len(mapping_rows):
        raise ValueError("答案集报告身份映射存在重复 sample")

    answer_payload = _load_yaml(repo / ANSWER_SET)
    answer_entries = answer_payload.get("entries")
    if not isinstance(answer_entries, list):
        raise ValueError("L1 答案集缺少 entries 列表")

    report_payloads: list[tuple[dict[str, Any], Path, dict[str, Any]]] = []
    seen_samples: set[str] = set()
    for source_path in source_paths(repo):
        source_payload = _load_yaml(source_path)
        corrected = apply_public_row_identity_corrections(source_payload, repository_root=repo)
        sample = corrected.get("sample")
        if sample not in mapping:
            raise ValueError(f"活动抽取输入未登记报告身份：{sample!r}")
        if sample in seen_samples:
            raise ValueError(f"活动抽取输入 sample 重复：{sample}")
        seen_samples.add(sample)
        report_payloads.append((corrected, source_path, mapping[sample]))

    if len(report_payloads) != 15 or len(mapping_rows) != 15:
        raise ValueError(
            f"冻结样本必须恰为15份：活动输入{len(report_payloads)}，映射{len(mapping_rows)}"
        )
    if seen_samples != set(mapping):
        raise ValueError("活动抽取输入与报告身份映射的 sample 集合不一致")

    reports: list[dict[str, Any]] = []
    l0_expected: dict[tuple[str, str, str, str], Any] = {}
    aggregate_l1 = 0
    aggregate_located = 0
    aggregate_unlocated = 0
    for payload, active_yaml, identity in report_payloads:
        source_pdf = payload["source_pdf"]
        pdf_path = repo / source_pdf
        if not pdf_path.is_file():
            raise FileNotFoundError(f"原始报告 PDF 不存在：{source_pdf}")
        if not source_pdf.endswith(identity["source_pdf_suffix"]):
            raise ValueError(f"报告身份映射的 PDF 后缀不匹配：{payload['sample']} / {source_pdf}")

        report_entries = [
            entry
            for entry in answer_entries
            if entry.get("source_pdf") == source_pdf
            and entry.get("stock_code") == identity["stock_code"]
            and entry.get("period_label") == identity["period_label"]
            and entry.get("report_kind") == identity["report_kind"]
        ]
        if not report_entries:
            raise ValueError(f"L1 答案集没有样本条目：{payload['sample']}")
        located = sum(bool(entry.get("page")) for entry in report_entries)
        unlocated = len(report_entries) - located
        source_values = _l0_source_value_count(payload)
        for statement, rows in payload["statements"].items():
            for row in rows:
                for column, value in row.items():
                    if column in {"item", "page", "source_text_label"}:
                        continue
                    key = _l0_key(payload, column, row["item"], statement)
                    if value is None:
                        l0_expected.setdefault(key, None)
                    else:
                        l0_expected[key] = value
        aggregate_l1 += len(report_entries)
        aggregate_located += located
        aggregate_unlocated += unlocated
        reports.append(
            {
                "sample": payload["sample"],
                "stock_code": identity["stock_code"],
                "period_label": identity["period_label"],
                "report_kind": identity["report_kind"],
                "source_pdf": source_pdf,
                "source_pdf_sha256": _sha256(pdf_path),
                "active_yaml": _relative(active_yaml, repo),
                "active_yaml_sha256": _sha256(active_yaml),
                "source_values": source_values,
                "l1_values": len(report_entries),
                "l1_located": located,
                "l1_unlocated": unlocated,
            }
        )

    report_order = {row["sample"]: index for index, row in enumerate(mapping_rows)}
    reports.sort(key=lambda row: report_order[row["sample"]])
    coverage = {
        "l0_values": len(l0_expected),
        "l1_values": aggregate_l1,
        "l1_located": aggregate_located,
        "l1_unlocated": aggregate_unlocated,
    }
    # 2026-09-29 ZTO 2026Q1 接入（第 6 项数据扩张）：14→15 份、L0 1532→1579、L1 1776→1823
    if coverage != {
        "l0_values": 1579,
        "l1_values": 1823,
        "l1_located": 1823,
        "l1_unlocated": 0,
    }:
        raise ValueError(f"当前样本覆盖与已验证基线不一致：{coverage}")

    return {
        "schema": "flow.public_financial_sample_freeze.v1",
        "freeze_id": "flow-public-c-level-2026-09-29-v1",
        "frozen_date": "2026-09-29",
        "purpose": (
            "公开财报 C 级出口的样本与实现输入身份冻结；不代表独立oracle、盲评或holdout验收通过。"
        ),
        "implementation_sha": implementation_sha,
        "implementation": {
            "commit_sha": implementation_sha,
            "ci_run_id": EXPECTED_CI_RUN,
            "ci_result": "success:17/17",
        },
        "inputs": {
            "freeze_generator": {
                "path": FREEZE_GENERATOR.as_posix(),
                "sha256": _sha256(repo / FREEZE_GENERATOR),
            },
            "l1_generator": {
                "path": L1_GENERATOR.as_posix(),
                "sha256": _sha256(repo / L1_GENERATOR),
            },
            "row_identity_adapter": {
                "path": ROW_IDENTITY_ADAPTER.as_posix(),
                "sha256": _sha256(repo / ROW_IDENTITY_ADAPTER),
            },
            "l0_l1_benchmark": {
                "path": L0_BENCHMARK.as_posix(),
                "sha256": _sha256(repo / L0_BENCHMARK),
            },
            "source_identity_map": {
                "path": SOURCES_MAP.as_posix(),
                "sha256": _sha256(repo / SOURCES_MAP),
            },
            "answer_set_l1": {
                "path": ANSWER_SET.as_posix(),
                "sha256": _sha256(repo / ANSWER_SET),
                "version": answer_payload.get("version"),
            },
            "row_identity_corrections": {
                "path": CORRECTION_MAP.as_posix(),
                "sha256": _sha256(repo / CORRECTION_MAP),
            },
            "financial_report_registry": {
                "path": SOURCE_MANIFEST.as_posix(),
                "sha256": _sha256(repo / SOURCE_MANIFEST),
                "yaml_parse_status": "valid",
            },
        },
        "report_count": len(reports),
        "coverage": coverage,
        "reports": reports,
        "independent_validation": _independent_validation_audit(repo, reports, registry_payload),
        "c_level_passed": False,
    }


def write_manifest(manifest: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(
            manifest,
            allow_unicode=True,
            sort_keys=False,
            width=110,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--implementation-sha", default=EXPECTED_IMPLEMENTATION_SHA)
    parser.add_argument("--out", type=Path, default=ROOT / FREEZE_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest(args.repo, implementation_sha=args.implementation_sha)
    write_manifest(manifest, args.out)
    print(
        f"已冻结 {manifest['report_count']} 份报告；"
        f"L0 {manifest['coverage']['l0_values']}，"
        f"L1 {manifest['coverage']['l1_located']}/{manifest['coverage']['l1_values']}；"
        f"输出 {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
