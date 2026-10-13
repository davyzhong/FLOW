from __future__ import annotations

import argparse
from datetime import UTC, datetime

import uvicorn

from flow_api.api.routes.dashboard import get_dashboard_now
from flow_api.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, type=int)
    arguments = parser.parse_args()

    app = create_app()
    app.dependency_overrides[get_dashboard_now] = lambda: datetime(
        2026, 9, 1, tzinfo=UTC
    )
    uvicorn.run(app, host="127.0.0.1", port=arguments.port)


if __name__ == "__main__":
    main()
