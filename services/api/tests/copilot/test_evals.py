from __future__ import annotations

import pytest

from flow_api.copilot.evals import run_all


@pytest.mark.parametrize("result", run_all(), ids=lambda result: result.case_id)
def test_copilot_eval_case(result) -> None:
    assert result.passed, result.detail


def test_eval_suite_is_non_empty_and_all_pass() -> None:
    results = run_all()
    assert len(results) >= 5
    assert all(result.passed for result in results)
