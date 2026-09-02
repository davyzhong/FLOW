from __future__ import annotations

import argparse
import socket


def find_free_ports(count: int = 1) -> tuple[int, ...]:
    if count < 1:
        raise ValueError("count must be at least one")

    listeners: list[socket.socket] = []
    try:
        for _ in range(count):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind(("127.0.0.1", 0))
            listeners.append(listener)
        return tuple(listener.getsockname()[1] for listener in listeners)
    finally:
        for listener in listeners:
            listener.close()


def find_free_port() -> int:
    return find_free_ports()[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Print unused loopback TCP ports.")
    parser.add_argument("count", nargs="?", type=int, default=1)
    args = parser.parse_args()
    print(*find_free_ports(args.count))


if __name__ == "__main__":
    main()
