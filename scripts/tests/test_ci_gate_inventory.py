from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PUBLISHING_GATE = REPO_ROOT / "scripts" / "test_publishing_golden.sh"
CI_DEDUP_GUARD = 'if [[ "${GITHUB_ACTIONS:-false}" != "true" ]]; then'

EXPECTED_GATES = {
    "static-python",
    "static-web",
    "unit",
    "integration",
    "data-contract",
    "intake-e2e",
    "metrics-known-answers",
    "analysis-invariants",
    "dashboard",
    "investigation-e2e",
    "contracts",
    "copilot-evals",
    "publishing-golden",
    "migrations",
    "smoke",
    "user-closure-e2e",
    "module-boundaries-e2e",
    "l0-baseline",
}


class CiGateInventoryTests(unittest.TestCase):
    def test_same_branch_runs_share_a_cancel_in_progress_group(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertRegex(workflow, r"(?m)^concurrency:\s*$")
        self.assertIn("github.event.pull_request.head.repo.full_name || github.repository", workflow)
        self.assertIn("github.event.pull_request.head.ref || github.ref_name", workflow)
        self.assertRegex(workflow, r"(?m)^  cancel-in-progress: true$")

    def test_ci_contains_all_seventeen_acceptance_gates(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        jobs = workflow.split("\njobs:\n", maxsplit=1)[1]
        actual = set(re.findall(r"^  ([a-z0-9-]+):\s*$", jobs, re.MULTILINE))

        self.assertEqual(actual, EXPECTED_GATES)

    def test_every_ci_gate_has_an_explicit_timeout(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        jobs = workflow.split("\njobs:\n", maxsplit=1)[1]
        matches = list(re.finditer(r"^  ([a-z0-9-]+):\s*$", jobs, re.MULTILINE))

        missing = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(jobs)
            if not re.search(r"^    timeout-minutes: [1-9][0-9]*$", jobs[match.end():end], re.MULTILINE):
                missing.append(match.group(1))

        self.assertEqual(missing, [])

    def test_ci_keeps_full_api_coverage_without_repeating_every_gate_in_closure(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("uv run pytest tests/dashboard -q", workflow)
        self.assertIn("uv run pytest tests/publishing -q", workflow)
        self.assertIn(
            "FLOW_USER_CLOSURE_ONLY=1 bash scripts/test_user_closure_e2e.sh",
            workflow,
        )

    def test_ci_specialized_scripts_keep_local_full_mode_and_skip_cross_gate_duplicates(self) -> None:
        local_full_runs = {
            "test_data_contract.sh": [
                "tests/integration/test_data_contract_persistence.py",
                "tests/integration/test_excel_database_round_trip.py",
            ],
            "test_intake_e2e.sh": [
                "uv run pytest tests/data_contract tests/fixtures -q",
                "uv run ruff check src tests migrations",
                "bash scripts/check_contracts.sh",
            ],
            "test_metrics_known_answers.sh": [
                "uv run pytest tests/integration/test_metric_*.py -q",
                "uv run pytest tests/integration/test_intake_e2e.py -q",
            ],
            "test_analysis_invariants.sh": [
                "uv run pytest tests/integration/test_analysis_*.py -q",
                "uv run pytest tests/integration/test_metric_*.py -q",
                "uv run pytest tests/integration/test_intake_e2e.py -q",
            ],
        }

        for filename, expected_runs in local_full_runs.items():
            with self.subTest(script=filename):
                script = (REPO_ROOT / "scripts" / filename).read_text(encoding="utf-8")
                self.assertIn(CI_DEDUP_GUARD, script)
                for command in expected_runs:
                    self.assertIn(command, script)

    def test_publishing_gate_uses_the_workspace_playwright_version(self) -> None:
        script = PUBLISHING_GATE.read_text(encoding="utf-8")

        # 本机/CI 无全局 pnpm，统一走 npx 定版 pnpm 调用工作区（apps/web）内的
        # playwright；禁止裸 npx playwright（可能拉到与工作区不同的版本）。
        self.assertIn(
            "npx --yes pnpm@10.17.1 --filter @flow/web exec playwright pdf",
            script,
        )
        self.assertNotIn("npx --yes playwright pdf", script)


if __name__ == "__main__":
    unittest.main()
