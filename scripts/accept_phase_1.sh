#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

make stack-up
make lint
make typecheck
make test
make contracts-check

cd services/api
uv run python ../../scripts/check_migrations.py
uv run pytest tests/integration -q
cd "$repo_root"

curl --fail --silent --show-error http://localhost:8000/api/v1/health > /dev/null
curl --fail --silent --show-error http://localhost:3000/ > /dev/null
docker compose -f infra/compose.yaml exec -T worker \
  celery -A flow_api.worker:celery_app inspect ping
