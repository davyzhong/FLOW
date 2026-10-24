#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$repo_root/services/api"
uv run pytest tests/intake -q
if [[ "${GITHUB_ACTIONS:-false}" != "true" ]]; then
  # Local aggregate mode keeps the full suite. In GitHub Actions the dedicated
  # integration, data-contract, static, migration, and contracts gates own these.
  uv run pytest tests/api/test_intake.py -q
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
  bash scripts/check_contracts.sh
  npx --yes pnpm@10.17.1 lint
  npx --yes pnpm@10.17.1 typecheck
else
  # static-python owns src/tests lint; preserve the migration-only lint check.
  uv run ruff check migrations
fi
uv run python ../../scripts/summarize_intake.py

cd "$repo_root"
npx --yes pnpm@10.17.1 test
