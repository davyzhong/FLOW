#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$repo_root/services/api"
uv run pytest tests/metrics tests/integration/test_metric_*.py -q
uv run pytest tests/integration/test_intake_e2e.py -q
uv run ruff check src tests migrations
uv run mypy src
uv run python ../../scripts/check_migrations.py
uv run python ../../scripts/summarize_metrics.py
