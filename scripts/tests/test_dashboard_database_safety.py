from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/test_dashboard.sh"
FLOW_URL = "postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow"


def _run_with_database_url(*, ci: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = FLOW_URL
    env["FLOW_DASHBOARD_DATABASE_URL_CHECK"] = "1"
    if ci:
        env["CI"] = "true"
    else:
        env.pop("CI", None)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_ci_compose_database_url_is_redirected_to_flow_test() -> None:
    result = _run_with_database_url(ci=True)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("/flow_test")


def test_local_explicit_flow_database_is_rejected_before_writes() -> None:
    result = _run_with_database_url(ci=False)

    assert result.returncode == 2
    assert "expected local flow_test" in result.stderr
    assert "database=flow" in result.stderr
