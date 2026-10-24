"""CI data-contract test shard mapping.

Each shard is a set of test files, not a runtime-order slice. Separate GitHub
jobs use separate databases, so fixture tests that create/reset data do not
race with one another.
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
API_TEST_ROOT = REPOSITORY_ROOT / "services/api/tests"

SHARDS: dict[str, tuple[str, ...]] = {
    "contracts": (
        "tests/data_contract/test_committed_artifacts.py",
        "tests/data_contract/test_contract.py",
        "tests/data_contract/test_semantic_round_trip.py",
        "tests/data_contract/test_workbook_generation.py",
        "tests/data_contract/test_workbook_parser.py",
    ),
    "canonical-statements": (
        "tests/fixtures/test_damai_canonical.py",
        "tests/fixtures/test_damai_statements.py",
    ),
    "generator-source": (
        "tests/fixtures/test_damai_generator.py",
        "tests/fixtures/test_damai_source_registry.py",
        "tests/fixtures/test_damai_metric_coverage.py",
    ),
    "profile-known-workflow": (
        "tests/fixtures/test_damai_profile.py",
        "tests/fixtures/test_known_answers.py",
        "tests/fixtures/test_damai_loader_workflow.py",
        "tests/fixtures/test_damai_loader_analytics.py",
    ),
    "loader-atomicity-edges": (
        "tests/fixtures/test_damai_loader_atomicity.py",
        "tests/fixtures/test_generator.py",
        "tests/fixtures/test_damai_loader.py",
        "tests/fixtures/test_damai_metric_grain.py",
    ),
}


def all_test_files() -> set[str]:
    return {
        path.relative_to(REPOSITORY_ROOT / "services/api").as_posix()
        for base in (API_TEST_ROOT / "data_contract", API_TEST_ROOT / "fixtures")
        for path in base.glob("test_*.py")
    }


def validate_shards() -> list[str]:
    errors: list[str] = []
    flattened = [path for paths in SHARDS.values() for path in paths]
    duplicates = sorted({path for path in flattened if flattened.count(path) > 1})
    if duplicates:
        errors.append(f"重复分配测试文件：{', '.join(duplicates)}")

    expected = all_test_files()
    actual = set(flattened)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"未分配测试文件：{', '.join(missing)}")
    if unexpected:
        errors.append(f"分配了范围外测试文件：{', '.join(unexpected)}")

    for path in flattened:
        if not (REPOSITORY_ROOT / "services/api" / path).is_file():
            errors.append(f"测试文件不存在：{path}")
    return errors


def paths_for_shard(name: str) -> tuple[str, ...]:
    return SHARDS[name]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--run-shard", choices=tuple(SHARDS))
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)

    if args.verify:
        errors = validate_shards()
        for error in errors:
            print(f"ERROR {error}")
        print(f"data-contract shard map: {'PASS' if not errors else 'FAIL'}")
        return int(bool(errors))

    return subprocess.run(
        ["uv", "run", "pytest", *paths_for_shard(args.run_shard), "-q"],
        cwd=REPOSITORY_ROOT / "services/api",
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
