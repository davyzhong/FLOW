#!/usr/bin/env python3
"""S01 FLOW CI 结果核验器（三 Agent 并行计划 Task 0 Step 8）。

用法：
    python3 scripts/ci/verify_workflow_jobs.py \
        --run-id <run_id> --expected-sha <checkpoint_sha> \
        --phase <bootstrap|task6|wave2|final>

断言：workflow 名为 FLOW CI、head_sha 精确匹配 expected、conclusion success、
清单中每个 job success 且无 skipped。仅标准库。
"""

from __future__ import annotations

import argparse
import json
import os
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
    jobs = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    duplicates = sorted({job for job in jobs if jobs.count(job) > 1})
    if duplicates:
        raise ValueError(f"required job 重复: {', '.join(duplicates)}")
    return jobs


def verify(
    run: dict,
    *,
    expected_sha: str,
    jobs: list[str] | None,
    phase: str,
) -> list[str]:
    """核验一次 FLOW CI 运行；返回错误列表（空 = 通过）。"""
    jobs = jobs if jobs is not None else load_required_jobs()
    errors: list[str] = []

    duplicates = sorted({job for job in jobs if jobs.count(job) > 1})
    if duplicates:
        errors.append(f"required job 重复: {', '.join(duplicates)}")

    exempt = PHASE_EXEMPTIONS[phase]
    required = [job for job in jobs if job not in exempt]
    if not required:
        errors.append("非豁免 required job 集合为空")

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

    for job in required:
        info = by_name.get(job)
        if info is None:
            errors.append(f"清单 job 缺失: {job}")
            continue
        if info.get("conclusion") == "skipped":
            errors.append(f"清单 job 被跳过: {job}")
        elif info.get("conclusion") != "success":
            errors.append(f"清单 job 未成功: {job} ({info.get('conclusion')!r})")
    return errors


def _request_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers=_request_headers(),
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def fetch_run(run_id: str) -> dict:
    base_url = f"https://api.github.com/repos/davyzhong/FLOW/actions/runs/{run_id}"
    details = _fetch_json(base_url)
    jobs: list[dict] = []
    page = 1
    while True:
        payload = _fetch_json(f"{base_url}/jobs?per_page=100&page={page}")
        page_jobs = payload.get("jobs")
        total_count = payload.get("total_count")
        if not isinstance(page_jobs, list) or not isinstance(total_count, int):
            raise TypeError("GitHub jobs 响应缺少 jobs 或 total_count")
        jobs.extend(page_jobs)
        if len(jobs) >= total_count:
            break
        if not page_jobs:
            raise ValueError(
                f"GitHub jobs 分页不完整: 期望 {total_count}，实际 {len(jobs)}"
            )
        page += 1

    return {
        "name": details.get("name"),
        "headSha": details.get("head_sha"),
        "status": details.get("status"),
        "conclusion": details.get("conclusion"),
        "jobs": jobs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--phase", required=True, choices=sorted(PHASE_EXEMPTIONS))
    args = parser.parse_args(argv)

    try:
        run = fetch_run(args.run_id)
        errors = verify(
            run,
            expected_sha=args.expected_sha,
            jobs=None,
            phase=args.phase,
        )
    except (OSError, TypeError, ValueError) as error:
        errors = [f"GitHub run 核验失败: {error}"]
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    print(f"verify: {'PASS' if not errors else 'FAIL'} "
          f"(run {args.run_id}, sha {args.expected_sha[:12]}, phase {args.phase})")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
