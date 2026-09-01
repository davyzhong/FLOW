from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "services" / "api"
CHECK_SCHEMA = "flow_migration_check"
SCHEMA_PATTERN = re.compile(r"[a-z0-9_]+")
SERVICE_ENV_KEYS = (
    "REDIS_URL",
    "S3_ENDPOINT_URL",
    "S3_BUCKET",
    "S3_ACCESS_KEY",
    "S3_SECRET_KEY",
)


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def resolve_database_url() -> str:
    from_environment = os.environ.get("DATABASE_URL")
    if from_environment:
        return from_environment
    for name in (".env", ".env.example"):
        value = load_env_file(ROOT / name).get("DATABASE_URL")
        if value:
            print(f"check_migrations: DATABASE_URL sourced from {name}", file=sys.stderr)
            return value
    print(
        "check_migrations: DATABASE_URL is required (environment, .env, or .env.example)",
        file=sys.stderr,
    )
    raise SystemExit(2)


def schema_url(database_url: str) -> str:
    parts = urlsplit(database_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["options"] = f"-csearch_path={CHECK_SCHEMA}"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def psycopg_url(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def reset_check_schema(database_url: str) -> None:
    with psycopg.connect(psycopg_url(database_url), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("drop schema if exists flow_migration_check cascade")
            cursor.execute("create schema flow_migration_check")


def run_alembic(database_url: str, env_file: dict[str, str], *args: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    for name in SERVICE_ENV_KEYS:
        environment.setdefault(name, env_file.get(name, ""))
    subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=API_DIR,
        env=environment,
        check=True,
    )


def main() -> int:
    database_url = resolve_database_url()
    env_file = load_env_file(ROOT / ".env") or load_env_file(ROOT / ".env.example")
    if not SCHEMA_PATTERN.fullmatch(CHECK_SCHEMA):
        raise ValueError("migration check schema name must be a plain identifier")

    reset_check_schema(database_url)
    try:
        isolated_url = schema_url(database_url)
        run_alembic(isolated_url, env_file, "upgrade", "head")
        run_alembic(isolated_url, env_file, "downgrade", "base")
        run_alembic(isolated_url, env_file, "upgrade", "head")
    finally:
        with psycopg.connect(psycopg_url(database_url), autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("drop schema if exists flow_migration_check cascade")

    print("Migration round trip passed in isolated schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
