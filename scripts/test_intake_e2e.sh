#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$repo_root/services/api"
uv run pytest tests/intake -q
uv run pytest \
  tests/integration/test_intake_audit_schema.py \
  tests/integration/test_intake_service.py \
  tests/integration/test_intake_atomicity.py \
  tests/integration/test_versioned_canonical_persistence.py \
  tests/integration/test_intake_e2e.py \
  -q
uv run pytest tests/data_contract tests/fixtures -q
uv run ruff check src tests migrations
uv run mypy src
uv run python ../../scripts/check_migrations.py
uv run python ../../scripts/summarize_intake.py

cd "$repo_root"
bash scripts/check_contracts.sh
npx --yes pnpm@10.17.1 test
npx --yes pnpm@10.17.1 lint
npx --yes pnpm@10.17.1 typecheck
