"""Own a service process group until the caller terminates this supervisor.

Launch directly with Python (not through a package-manager wrapper). Browser
acceptance scripts can then terminate and wait for one PID without leaking
Next/Uvicorn descendants or touching unrelated development servers.
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time


def stop_group(process: subprocess.Popen[bytes]) -> None:
    group = process.pid
    try:
        os.killpg(group, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        process.poll()  # Reap the immediate child while descendants shut down.
        try:
            os.killpg(group, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    # A descendant may ignore TERM; contain cleanup to this owned session.
    try:
        os.killpg(group, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a service command is required after --")
    stop_signal: int | None = None

    def request_stop(signum: int, _frame: object) -> None:
        nonlocal stop_signal
        stop_signal = signum

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    process = subprocess.Popen(command, cwd=args.cwd, start_new_session=True)
    try:
        while stop_signal is None:
            try:
                return process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
        return 128 + stop_signal
    finally:
        stop_group(process)


if __name__ == "__main__":
    raise SystemExit(main())
