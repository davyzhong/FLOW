"""固定、可审计的 integration CI 分片。

各分片在独立 runner 和数据库中运行。映射按测试文件名分类，并由 --verify
证明覆盖 workflow 原有的 4 个 pytest 根目录（含 API 排除项）。
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services/api"
ROOTS = ("integration", "investigation", "copilot", "api")
EXCLUDED = {"tests/api/test_auth_boundary.py", "tests/api/test_workspace.py"}
SHARD_NAMES = ("analysis-dashboard", "intake-metrics", "core", "api")


def all_test_files() -> set[str]:
    return {
        path.relative_to(API_ROOT).as_posix()
        for root in ROOTS
        for path in (API_ROOT / "tests" / root).glob("test_*.py")
        if path.relative_to(API_ROOT).as_posix() not in EXCLUDED
    }


def shard_for(path: str) -> str:
    name = Path(path).name
    auxiliary_roots = ("tests/api/", "tests/copilot/", "tests/investigation/")
    if path.startswith(auxiliary_roots):
        return "api"
    if name.startswith(("test_analysis_", "test_dashboard_")):
        return "analysis-dashboard"
    if name.startswith(("test_intake_", "test_metric_")):
        return "intake-metrics"
    return "core"


def files_for_shard(name: str) -> tuple[str, ...]:
    if name not in SHARD_NAMES:
        raise KeyError(name)
    return tuple(sorted(path for path in all_test_files() if shard_for(path) == name))


def validate() -> list[str]:
    errors: list[str] = []
    files = all_test_files()
    assigned = [path for name in SHARD_NAMES for path in files_for_shard(name)]
    if len(assigned) != len(set(assigned)):
        errors.append("同一测试文件被分配到多个 integration shard")
    if set(assigned) != files:
        missing = sorted(files - set(assigned))
        extra = sorted(set(assigned) - files)
        errors.append(f"分片映射不完整：missing={missing}, extra={extra}")
    for path in assigned:
        if not (API_ROOT / path).is_file():
            errors.append(f"测试文件不存在：{path}")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--run-shard", choices=SHARD_NAMES)
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    if args.verify:
        errors = validate()
        for error in errors:
            print(f"ERROR {error}")
        result = "PASS" if not errors else "FAIL"
        print(f"integration shard map: {result}; {len(all_test_files())} files")
        return int(bool(errors))
    return subprocess.run(
        ["uv", "run", "pytest", *files_for_shard(args.run_shard), "-q"],
        cwd=API_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
