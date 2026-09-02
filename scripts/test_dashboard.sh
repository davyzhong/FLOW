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
(cd services/api && uv run python ../../scripts/seed_dashboard_demo.py --fresh-batch)

(cd services/api && uv run uvicorn flow_api.main:app --host 127.0.0.1 --port "${api_port}") \
  >"${dashboard_logs}/api.log" 2>&1 &
api_pid=$!

npx --yes pnpm@10.17.1 --filter @flow/web exec next dev --hostname 127.0.0.1 --port "${web_port}" \
  >"${dashboard_logs}/web.log" 2>&1 &
web_pid=$!

uv run scripts/wait_for_services.py "127.0.0.1:${api_port}" "127.0.0.1:${web_port}"
curl -sf "http://127.0.0.1:${api_port}/api/v1/dashboard/overview" \
  -o "${dashboard_logs}/dashboard_overview.json"
uv run scripts/summarize_dashboard.py "${dashboard_logs}/dashboard_overview.json"
if [[ "${PLAYWRIGHT_UPDATE_SNAPSHOTS:-0}" == "1" ]]; then
  npx --yes playwright test apps/web/e2e/dashboard*.spec.ts --update-snapshots
else
  npx --yes playwright test apps/web/e2e/dashboard*.spec.ts
fi
