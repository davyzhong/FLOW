"""Task 0 Step 8（S01 编排）：FLOW CI 结果核验器的红灯测试。

核验器契约（三 Agent 并行计划 Task 0 Step 8）：
- 接收 run id 与 expected SHA；
- 断言 workflow 名为 FLOW CI、head_sha 精确匹配、conclusion 为 success；
- 清单（config/ci/required_jobs_s01.txt）中每个 job success 且无 skipped；
- 阶段参数（bootstrap|task6|wave2|final）选择清单版本，未接入的 job 显式豁免。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/ci/verify_workflow_jobs.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_workflow_jobs", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_exists() -> None:
    assert MODULE_PATH.is_file(), "核验器脚本必须存在"


def test_required_jobs_file_lists_s01_jobs() -> None:
    module = _load_module()
    jobs = module.load_required_jobs(ROOT / "config/ci/required_jobs_s01.txt")
    assert "static-python" in jobs
    assert "module-boundaries-e2e" in jobs
    assert len(jobs) == 17


def test_verify_accepts_matching_success_run() -> None:
    module = _load_module()
    run = {
        "name": "FLOW CI",
        "headSha": "a" * 40,
        "conclusion": "success",
        "status": "completed",
        "jobs": [
            {"name": job, "conclusion": "success", "skipped": False}
            for job in module.load_required_jobs(ROOT / "config/ci/required_jobs_s01.txt")
        ],
    }
    errors = module.verify(run, expected_sha="a" * 40, jobs=None)
    assert errors == []


def test_verify_rejects_sha_mismatch() -> None:
    module = _load_module()
    run = {"name": "FLOW CI", "headSha": "b" * 40, "conclusion": "success",
           "status": "completed", "jobs": []}
    errors = module.verify(run, expected_sha="a" * 40, jobs=[])
    assert any("head_sha" in e for e in errors)


def test_verify_rejects_non_success_and_wrong_workflow() -> None:
    module = _load_module()
    run = {"name": "Other CI", "headSha": "a" * 40, "conclusion": "failure",
           "status": "completed", "jobs": []}
    errors = module.verify(run, expected_sha="a" * 40, jobs=[])
    assert any("workflow" in e for e in errors)
    assert any("conclusion" in e for e in errors)


def test_verify_rejects_missing_and_skipped_jobs() -> None:
    module = _load_module()
    run = {"name": "FLOW CI", "headSha": "a" * 40, "conclusion": "success",
           "status": "completed",
           "jobs": [{"name": "static-python", "conclusion": "success", "skipped": False},
                    {"name": "unit", "conclusion": "success", "skipped": True}]}
    errors = module.verify(run, expected_sha="a" * 40,
                           jobs=["static-python", "unit", "smoke"])
    assert any("smoke" in e for e in errors)
    assert any("skipped" in e and "unit" in e for e in errors)


def test_phase_exempts_not_yet_wired_jobs() -> None:
    module = _load_module()
    run = {"name": "FLOW CI", "headSha": "a" * 40, "conclusion": "success",
           "status": "completed",
           "jobs": [{"name": "static-python", "conclusion": "success", "skipped": False}]}
    # bootstrap 阶段：清单中未接入的 job 显式豁免，不阻断
    errors = module.verify(run, expected_sha="a" * 40,
                           jobs=module.load_required_jobs(
                               ROOT / "config/ci/required_jobs_s01.txt"),
                           exempt={"module-boundaries-e2e"})
    assert errors == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
