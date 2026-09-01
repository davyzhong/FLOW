#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://localhost:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"

cd "$repo_root/services/api"
uv run alembic upgrade head
uv run pytest tests/analysis tests/integration/test_analysis_*.py -q
uv run pytest tests/metrics tests/integration/test_metric_*.py -q
uv run pytest tests/integration/test_intake_e2e.py -q
uv run ruff check src tests migrations
uv run mypy src
uv run python ../../scripts/check_migrations.py
uv run python ../../scripts/summarize_analysis.py
