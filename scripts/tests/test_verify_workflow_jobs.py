"""S01 FLOW CI 结果核验器的 fail-closed 契约测试。"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/ci/verify_workflow_jobs.py"
REQUIRED_JOBS_PATH = ROOT / "config/ci/required_jobs_s01.txt"
WORKFLOW_PATH = ROOT / ".github/workflows/ci.yml"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_workflow_jobs", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response(io.BytesIO):
    def __init__(self, payload: dict):
        super().__init__(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _success_run(*, jobs: list[dict], sha: str = "a" * 40) -> dict:
    return {
        "name": "FLOW CI",
        "headSha": sha,
        "status": "completed",
        "conclusion": "success",
        "jobs": jobs,
    }


def _success_job(name: str) -> dict:
    return {"name": name, "status": "completed", "conclusion": "success"}


def test_required_jobs_file_is_unique_and_lists_s01_jobs() -> None:
    module = _load_module()
    jobs = module.load_required_jobs(REQUIRED_JOBS_PATH)
    assert "static-python" in jobs
    assert "module-boundaries-e2e" in jobs
    assert len(jobs) == 17
    assert len(jobs) == len(set(jobs))


def test_load_required_jobs_rejects_duplicates(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "required.txt"
    path.write_text("static-python\nstatic-python\n", encoding="utf-8")
    with pytest.raises(ValueError, match="重复"):
        module.load_required_jobs(path)


def test_fetch_run_uses_real_github_shapes_and_separate_endpoints() -> None:
    module = _load_module()
    responses = [
        _Response({
            "name": "FLOW CI",
            "head_sha": "a" * 40,
            "status": "completed",
            "conclusion": "success",
        }),
        _Response({"total_count": 1, "jobs": [_success_job("static-python")]}),
    ]

    with mock.patch.object(module.urllib.request, "urlopen", side_effect=responses) as open_url:
        run = module.fetch_run("123")

    assert run == _success_run(jobs=[_success_job("static-python")])
    urls = [call.args[0].full_url for call in open_url.call_args_list]
    assert urls[0].endswith("/actions/runs/123")
    assert urls[1].endswith("/actions/runs/123/jobs?per_page=100&page=1")


def test_fetch_run_paginates_jobs() -> None:
    module = _load_module()
    first_page = [_success_job(f"job-{index}") for index in range(100)]
    responses = [
        _Response({
            "name": "FLOW CI",
            "head_sha": "a" * 40,
            "status": "completed",
            "conclusion": "success",
        }),
        _Response({"total_count": 101, "jobs": first_page}),
        _Response({"total_count": 101, "jobs": [_success_job("job-100")]}),
    ]

    with mock.patch.object(module.urllib.request, "urlopen", side_effect=responses) as open_url:
        run = module.fetch_run("456")

    assert len(run["jobs"]) == 101
    assert open_url.call_args_list[-1].args[0].full_url.endswith(
        "/actions/runs/456/jobs?per_page=100&page=2"
    )


@pytest.mark.parametrize("variable", ["GH_TOKEN", "GITHUB_TOKEN"])
def test_fetch_run_authenticates_with_supported_tokens(variable: str) -> None:
    module = _load_module()
    responses = [
        _Response({
            "name": "FLOW CI",
            "head_sha": "a" * 40,
            "status": "completed",
            "conclusion": "success",
        }),
        _Response({"total_count": 0, "jobs": []}),
    ]

    with (
        mock.patch.dict(module.os.environ, {variable: "secret-token"}, clear=True),
        mock.patch.object(
            module.urllib.request, "urlopen", side_effect=responses
        ) as open_url,
    ):
        module.fetch_run("789")

    for call in open_url.call_args_list:
        assert call.args[0].get_header("Authorization") == "Bearer secret-token"


def test_verify_accepts_matching_success_run() -> None:
    module = _load_module()
    required = module.load_required_jobs(REQUIRED_JOBS_PATH)
    run = _success_run(jobs=[_success_job(job) for job in required])
    assert module.verify(run, expected_sha="a" * 40, jobs=required, phase="final") == []


@pytest.mark.parametrize("phase", ["bootstrap", "task6"])
def test_early_phases_only_exempt_module_boundaries(phase: str) -> None:
    module = _load_module()
    required = ["static-python", "module-boundaries-e2e"]
    run = _success_run(jobs=[_success_job("static-python")])
    assert module.verify(run, expected_sha="a" * 40, jobs=required, phase=phase) == []


@pytest.mark.parametrize("phase", ["wave2", "final"])
def test_late_phases_do_not_exempt_module_boundaries(phase: str) -> None:
    module = _load_module()
    required = ["static-python", "module-boundaries-e2e"]
    run = _success_run(jobs=[_success_job("static-python")])
    errors = module.verify(run, expected_sha="a" * 40, jobs=required, phase=phase)
    assert any("module-boundaries-e2e" in error and "缺失" in error for error in errors)


def test_verify_rejects_empty_non_exempt_set() -> None:
    module = _load_module()
    run = _success_run(jobs=[])
    errors = module.verify(
        run,
        expected_sha="a" * 40,
        jobs=["module-boundaries-e2e"],
        phase="bootstrap",
    )
    assert any("非豁免" in error and "为空" in error for error in errors)


def test_verify_rejects_duplicate_required_jobs() -> None:
    module = _load_module()
    run = _success_run(jobs=[_success_job("static-python")])
    errors = module.verify(
        run,
        expected_sha="a" * 40,
        jobs=["static-python", "static-python"],
        phase="final",
    )
    assert any("重复" in error for error in errors)


@pytest.mark.parametrize(
    ("override", "expected_fragment"),
    [
        ({"name": "Other CI"}, "workflow"),
        ({"headSha": "b" * 40}, "head_sha"),
        ({"status": "in_progress"}, "未完成"),
        ({"conclusion": "failure"}, "conclusion"),
    ],
)
def test_verify_rejects_wrong_run_identity_or_result(
    override: dict, expected_fragment: str
) -> None:
    module = _load_module()
    run = _success_run(jobs=[_success_job("static-python")])
    run.update(override)
    errors = module.verify(
        run, expected_sha="a" * 40, jobs=["static-python"], phase="final"
    )
    assert any(expected_fragment in error for error in errors)


@pytest.mark.parametrize(
    ("jobs", "expected_job", "expected_fragment"),
    [
        ([], "static-python", "缺失"),
        ([{"name": "static-python", "status": "completed", "conclusion": "failure"}],
         "static-python", "未成功"),
        ([{"name": "static-python", "status": "completed", "conclusion": "skipped"}],
         "static-python", "跳过"),
    ],
)
def test_verify_rejects_missing_failed_and_skipped_jobs(
    jobs: list[dict], expected_job: str, expected_fragment: str
) -> None:
    module = _load_module()
    errors = module.verify(
        _success_run(jobs=jobs),
        expected_sha="a" * 40,
        jobs=["static-python"],
        phase="final",
    )
    assert any(expected_job in error and expected_fragment in error for error in errors)


def test_cli_rejects_arbitrary_exemptions() -> None:
    module = _load_module()
    with pytest.raises(SystemExit) as exc_info:
        module.main([
            "--run-id", "123",
            "--expected-sha", "a" * 40,
            "--phase", "final",
            "--exempt", "static-python",
        ])
    assert exc_info.value.code == 2


def test_static_python_preserves_governance_tests_and_runs_verifier_pytest() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "cd services/api && uv run python -m unittest discover "
        "-s ../../scripts/tests -t ../.. -v"
    ) in workflow
    assert (
        "cd services/api && uv run pytest "
        "../../scripts/tests/test_verify_workflow_jobs.py -q"
    ) in workflow
