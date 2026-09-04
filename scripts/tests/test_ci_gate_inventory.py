from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
PUBLISHING_GATE = REPO_ROOT / "scripts" / "test_publishing_golden.sh"

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
}


class CiGateInventoryTests(unittest.TestCase):
    def test_ci_contains_all_sixteen_acceptance_gates(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        jobs = workflow.split("\njobs:\n", maxsplit=1)[1]
        actual = set(re.findall(r"^  ([a-z0-9-]+):\s*$", jobs, re.MULTILINE))

        self.assertEqual(actual, EXPECTED_GATES)

    def test_ci_keeps_full_api_coverage_without_repeating_every_gate_in_closure(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("uv run pytest tests/dashboard -q", workflow)
        self.assertIn("uv run pytest tests/publishing -q", workflow)
        self.assertIn(
            "FLOW_USER_CLOSURE_ONLY=1 bash scripts/test_user_closure_e2e.sh",
            workflow,
        )

    def test_publishing_gate_uses_the_workspace_playwright_version(self) -> None:
        script = PUBLISHING_GATE.read_text(encoding="utf-8")

        self.assertIn("pnpm exec playwright pdf", script)
        self.assertNotIn("npx --yes playwright pdf", script)


if __name__ == "__main__":
    unittest.main()
