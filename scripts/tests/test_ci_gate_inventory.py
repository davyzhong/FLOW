from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

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
}


class CiGateInventoryTests(unittest.TestCase):
    def test_ci_contains_all_fifteen_acceptance_gates(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        jobs = workflow.split("\njobs:\n", maxsplit=1)[1]
        actual = set(re.findall(r"^  ([a-z0-9-]+):\s*$", jobs, re.MULTILINE))

        self.assertEqual(actual, EXPECTED_GATES)


if __name__ == "__main__":
    unittest.main()
