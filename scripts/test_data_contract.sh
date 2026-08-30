#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/services/api"

uv run pytest tests/data_contract tests/fixtures -q
uv run pytest \
  tests/integration/test_data_contract_persistence.py \
  tests/integration/test_excel_database_round_trip.py \
  -q
uv run ruff check src tests
uv run mypy src
uv run python ../../scripts/summarize_data_contract.py
