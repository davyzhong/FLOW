#!/usr/bin/env python3
"""S01 FLOW CI 结果核验器（三 Agent 并行计划 Task 0 Step 8）。

用法：
    python3 scripts/ci/verify_workflow_jobs.py \
        --run-id <run_id> --expected-sha <checkpoint_sha> \
        --phase <bootstrap|task6|wave2|final> \
        [--exempt module-boundaries-e2e ...]

断言：workflow 名为 FLOW CI、head_sha 精确匹配 expected、conclusion success、
清单中每个 job success 且无 skipped。仅标准库。
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_JOBS_FILE = ROOT / "config/ci/required_jobs_s01.txt"
WORKFLOW_NAME = "FLOW CI"

# 阶段豁免：该 checkpoint 尚未接入 CI 的清单 job（显式声明，不静默缺失）
PHASE_EXEMPTIONS: dict[str, set[str]] = {
    "bootstrap": {"module-boundaries-e2e"},
    "task6": {"module-boundaries-e2e"},
    "wave2": set(),
    "final": set(),
}


def load_required_jobs(path: Path = REQUIRED_JOBS_FILE) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def verify(
    run: dict,
    *,
    expected_sha: str,
    jobs: list[str] | None,
    exempt: set[str] | None = None,
) -> list[str]:
    """核验一次 FLOW CI 运行；返回错误列表（空 = 通过）。"""
    exempt = exempt or set()
    jobs = jobs if jobs is not None else load_required_jobs()
    errors: list[str] = []

    if run.get("name") != WORKFLOW_NAME:
        errors.append(f"workflow 名称不是 {WORKFLOW_NAME}: {run.get('name')!r}")
    if run.get("headSha") != expected_sha:
        errors.append(
            f"head_sha 不匹配: 期望 {expected_sha}，实际 {run.get('headSha')}"
        )
    if run.get("status") != "completed":
        errors.append(f"运行未完成: status={run.get('status')!r}")
    if run.get("conclusion") != "success":
        errors.append(f"conclusion 不是 success: {run.get('conclusion')!r}")

    by_name: dict[str, dict] = {}
    for job in run.get("jobs", []):
        by_name[job.get("name", "")] = job

    for job in jobs:
        if job in exempt:
            continue
        info = by_name.get(job)
        if info is None:
            errors.append(f"清单 job 缺失: {job}")
            continue
        if info.get("conclusion") != "success":
            errors.append(f"清单 job 未成功: {job} ({info.get('conclusion')!r})")
        if info.get("skipped"):
            errors.append(f"清单 job 被跳过: {job}")
    return errors


def fetch_run(run_id: str) -> dict:
    request = urllib.request.Request(
        f"https://api.github.com/repos/davyzhong/FLOW/actions/runs/{run_id}?per_page=100",
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--phase", required=True, choices=sorted(PHASE_EXEMPTIONS))
    parser.add_argument("--exempt", action="append", default=[])
    args = parser.parse_args(argv)

    payload = fetch_run(args.run_id)
    run = {
        "name": payload.get("name"),
        "headSha": payload.get("head_sha"),
        "status": payload.get("status"),
        "conclusion": payload.get("conclusion"),
        "jobs": [
            {"name": j.get("name"), "conclusion": j.get("conclusion"),
             "skipped": bool(j.get("conclusion") == "skipped")}
            for j in (payload.get("jobs") or {}).get("jobs", [])
        ],
    }
    exempt = PHASE_EXEMPTIONS.get(args.phase, set()) | set(args.exempt)
    errors = verify(run, expected_sha=args.expected_sha, jobs=None, exempt=exempt)
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    print(f"verify: {'PASS' if not errors else 'FAIL'} "
          f"(run {args.run_id}, sha {args.expected_sha[:12]}, phase {args.phase})")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
