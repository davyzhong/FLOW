#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://127.0.0.1:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"
read -r api_port web_port < <(uv run python scripts/find_free_port.py 2)
export FLOW_API_INTERNAL_URL="http://127.0.0.1:${api_port}"
export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${web_port}"

investigation_logs="$(mktemp -d)"
api_pid=""
web_pid=""

cleanup() {
  status=$?
  if [[ -n "${web_pid}" && "${web_pid}" =~ ^[0-9]+$ ]]; then kill "${web_pid}" 2>/dev/null || true; wait "${web_pid}" 2>/dev/null || true; fi
  if [[ -n "${api_pid}" && "${api_pid}" =~ ^[0-9]+$ ]]; then kill "${api_pid}" 2>/dev/null || true; wait "${api_pid}" 2>/dev/null || true; fi
  if [[ ${status} -ne 0 ]]; then
    tail -80 "${investigation_logs}/api.log" 2>/dev/null || true
    tail -80 "${investigation_logs}/web.log" 2>/dev/null || true
  fi
  rm -rf "${investigation_logs}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

(cd services/api && uv run alembic upgrade head)
(cd services/api && uv run python ../../scripts/seed_dashboard_demo.py --fresh-batch)

python3 scripts/run_service.py --cwd services/api -- .venv/bin/python -m uvicorn flow_api.main:app --host 127.0.0.1 --port "${api_port}" \
  >"${investigation_logs}/api.log" 2>&1 &
api_pid=$!

python3 scripts/run_service.py --cwd apps/web -- node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port "${web_port}" \
  >"${investigation_logs}/web.log" 2>&1 &
web_pid=$!

uv run scripts/wait_for_services.py "127.0.0.1:${api_port}" "127.0.0.1:${web_port}"
npx --yes playwright test apps/web/e2e/investigation.spec.ts apps/web/e2e/dashboard.spec.ts
