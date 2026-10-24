#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/services/api"

uv run pytest tests/data_contract tests/fixtures -q
if [[ "${GITHUB_ACTIONS:-false}" != "true" ]]; then
  # Local aggregate mode keeps the full suite; GitHub integration owns these
  # integration tests and static-python owns lint/type checks.
  uv run pytest \
    tests/integration/test_data_contract_persistence.py \
    tests/integration/test_excel_database_round_trip.py \
    -q
  uv run ruff check src tests
  uv run mypy src
fi
uv run python ../../scripts/summarize_data_contract.py
