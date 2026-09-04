from __future__ import annotations

import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = ROOT / "scripts/run_service.py"


def wait_until(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.025)
    raise AssertionError("condition did not become true before timeout")


def listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.1):
            return True
    except OSError:
        return False


class ServiceLifecycleTests(unittest.TestCase):
    def test_browser_gates_use_owned_supervisors_and_wait_for_cleanup(self) -> None:
        for name in ("test_dashboard.sh", "test_investigation_e2e.sh", "test_user_closure_e2e.sh"):
            with self.subTest(script=name):
                script = (ROOT / "scripts" / name).read_text()
                self.assertIn("scripts/run_service.py", script)
                self.assertIn('wait "${web_pid}"', script)
                self.assertIn('wait "${api_pid}"', script)
                self.assertNotIn("pkill", script)

    def test_termination_releases_grandchild_port_without_killing_other_services(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            child = folder / "child.py"
            child.write_text(
                "import socket,sys,time,os\n"
                "s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen()\n"
                "open(sys.argv[1]+'.tmp','w').write(str(s.getsockname()[1]))\n"
                "os.replace(sys.argv[1]+'.tmp',sys.argv[1])\n"
                "time.sleep(60)\n"
            )
            unrelated_file = folder / "unrelated.port"
            unrelated = subprocess.Popen([sys.executable, str(child), str(unrelated_file)])
            try:
                wait_until(unrelated_file.exists)
                unrelated_port = int(unrelated_file.read_text())
                for attempt in range(2):
                    port_file = folder / f"owned-{attempt}.port"
                    # Launcher creates a grandchild, just like Next's development launcher.
                    command = (
                        "import subprocess,sys,time; "
                        "subprocess.Popen(sys.argv[1:]); time.sleep(60)"
                    )
                    process = subprocess.Popen(
                        [sys.executable, str(SUPERVISOR), "--cwd", str(folder), "--",
                         sys.executable, "-c", command, sys.executable, str(child), str(port_file)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                    try:
                        wait_until(port_file.exists)
                        port = int(port_file.read_text())
                        self.assertTrue(listening(port))
                        process.send_signal(signal.SIGTERM if attempt == 0 else signal.SIGINT)
                        process.wait(timeout=8)
                        wait_until(lambda port=port: not listening(port))
                        self.assertTrue(listening(unrelated_port))
                    finally:
                        if process.poll() is None:
                            process.terminate()
                            process.wait(timeout=8)
            finally:
                unrelated.terminate()
                unrelated.wait(timeout=5)

    def test_preserves_service_exit_status(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SUPERVISOR), "--cwd", str(ROOT), "--",
             sys.executable, "-c", "raise SystemExit(7)"],
            capture_output=True, timeout=8, check=False,
        )
        self.assertEqual(result.returncode, 7, result.stderr.decode())


if __name__ == "__main__":
    unittest.main()
