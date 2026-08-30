from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
DEFAULT_DATABASE_URL = "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow"
SERVICE_DEFAULTS = {
    "REDIS_URL": "redis://localhost:6379/0",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_BUCKET": "flow",
    "S3_ACCESS_KEY": "flow",
    "S3_SECRET_KEY": "flow_dev_only",
}


def schema_url(database_url: str, schema: str) -> str:
    parts = urlsplit(database_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["options"] = f"-csearch_path={schema}"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def psycopg_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def run_alembic(database_url: str, *args: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    for name, value in SERVICE_DEFAULTS.items():
        environment.setdefault(name, value)
    subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=API_DIR,
        env=environment,
        check=True,
    )


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    schema = f"flow_migration_check_{uuid4().hex}"

    with psycopg.connect(psycopg_url(database_url), autocommit=True) as connection:
        connection.execute(sql.SQL("create schema {}").format(sql.Identifier(schema)))

    try:
        isolated_url = schema_url(database_url, schema)
        run_alembic(isolated_url, "upgrade", "head")
        run_alembic(isolated_url, "downgrade", "base")
        run_alembic(isolated_url, "upgrade", "head")
    finally:
        with psycopg.connect(psycopg_url(database_url), autocommit=True) as connection:
            connection.execute(
                sql.SQL("drop schema {} cascade").format(sql.Identifier(schema))
            )

    print("Migration round trip passed in isolated schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
