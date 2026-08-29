from __future__ import annotations

import socket
import sys
import time


def wait_for(host: str, port: int, timeout_seconds: float = 60.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for {host}:{port}")


def main(addresses: list[str]) -> None:
    for address in addresses:
        host, raw_port = address.rsplit(":", 1)
        wait_for(host, int(raw_port))


if __name__ == "__main__":
    main(sys.argv[1:])
