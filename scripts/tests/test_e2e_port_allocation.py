from __future__ import annotations

import socket
import unittest
from pathlib import Path

from scripts.find_free_port import find_free_port

REPO_ROOT = Path(__file__).resolve().parents[2]


class E2ePortAllocationTests(unittest.TestCase):
    def test_find_free_port_returns_a_bindable_loopback_port(self) -> None:
        port = find_free_port()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", port))

    def test_browser_gates_do_not_use_fixed_service_ports(self) -> None:
        for relative_path in (
            "scripts/test_dashboard.sh",
            "scripts/test_investigation_e2e.sh",
        ):
            script = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("scripts/find_free_port.py", script)
            self.assertNotIn("18080", script)
            self.assertNotIn("13100", script)

    def test_dashboard_gate_excludes_investigation_specs(self) -> None:
        script = (REPO_ROOT / "scripts/test_dashboard.sh").read_text(encoding="utf-8")

        self.assertIn(
            "playwright test apps/web/e2e/dashboard*.spec.ts",
            script,
        )


if __name__ == "__main__":
    unittest.main()
