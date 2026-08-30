#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$repo_root/.env" ]]; then
  set -a
  source "$repo_root/.env"
  set +a
elif [[ -f "$repo_root/.env.example" ]]; then
  set -a
  source "$repo_root/.env.example"
  set +a
fi

cd "$repo_root/services/api"
uv run python -c 'import json; from flow_api.main import create_app; print(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2))' > "$repo_root/packages/contracts/openapi.json"

cd "$repo_root"
npx --yes pnpm@10.17.1 --filter @flow/contracts generate
