#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://127.0.0.1:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"
export FLOW_API_INTERNAL_URL="http://127.0.0.1:18080"
export PLAYWRIGHT_BASE_URL="http://127.0.0.1:13100"

dashboard_logs="$(mktemp -d)"
api_pid=""
web_pid=""

cleanup() {
  status=$?
  if [[ -n "${web_pid}" ]]; then kill "${web_pid}" 2>/dev/null || true; fi
  if [[ -n "${api_pid}" ]]; then kill "${api_pid}" 2>/dev/null || true; fi
  if [[ ${status} -ne 0 ]]; then
    tail -80 "${dashboard_logs}/api.log" 2>/dev/null || true
    tail -80 "${dashboard_logs}/web.log" 2>/dev/null || true
  fi
  rm -rf "${dashboard_logs}"
}
trap cleanup EXIT

(cd services/api && uv run alembic upgrade head)
(cd services/api && uv run python ../../scripts/seed_dashboard_demo.py)

(cd services/api && uv run uvicorn flow_api.main:app --host 127.0.0.1 --port 18080) \
  >"${dashboard_logs}/api.log" 2>&1 &
api_pid=$!

npx --yes pnpm@10.17.1 --filter @flow/web exec next dev --hostname 127.0.0.1 --port 13100 \
  >"${dashboard_logs}/web.log" 2>&1 &
web_pid=$!

uv run scripts/wait_for_services.py 127.0.0.1:18080 127.0.0.1:13100
uv run scripts/summarize_dashboard.py "${PLAYWRIGHT_BASE_URL}"
if [[ "${PLAYWRIGHT_UPDATE_SNAPSHOTS:-0}" == "1" ]]; then
  npx --yes playwright test --update-snapshots
else
  npx --yes playwright test
fi
