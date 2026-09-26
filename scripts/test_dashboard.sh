#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow_test}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://127.0.0.1:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"
# S01 §2.2：development 模式认证边界需要显式 dev actor（与 scripts/seed_dev_principal.py 一致）
export FLOW_DEV_ACTOR_ID="${FLOW_DEV_ACTOR_ID:-flow-dev-bp}"

read -r dashboard_db_host dashboard_db_name < <(
  uv run python -c 'import os; from urllib.parse import unquote, urlsplit; url = urlsplit(os.environ["DATABASE_URL"]); print(url.hostname or "", unquote(url.path.lstrip("/")))'
)
if [[ "${dashboard_db_host}" != "127.0.0.1" && "${dashboard_db_host}" != "localhost" ]] \
  || [[ "${dashboard_db_name}" != "flow_test" ]]; then
  echo "Refusing dashboard acceptance writes: expected local flow_test, got host=${dashboard_db_host} database=${dashboard_db_name}" >&2
  exit 2
fi

(cd services/api && uv run python - <<'PY'
import os
from urllib.parse import urlsplit, urlunsplit

import psycopg

database_url = urlsplit(os.environ["DATABASE_URL"])
admin_url = urlunsplit(
    ("postgresql", database_url.netloc, "/postgres", "", "")
)
with psycopg.connect(admin_url, autocommit=True) as connection:
    exists = connection.execute(
        "SELECT 1 FROM pg_database WHERE datname = 'flow_test'"
    ).fetchone()
    if not exists:
        connection.execute('CREATE DATABASE "flow_test"')
PY
)

read -r api_port web_port < <(uv run python scripts/find_free_port.py 2)
export FLOW_API_INTERNAL_URL="http://127.0.0.1:${api_port}"
export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${web_port}"

dashboard_logs="$(mktemp -d)"
api_pid=""
web_pid=""
web_app_dir=""

cleanup() {
  status=$?
  if [[ -n "${web_pid}" ]]; then kill "${web_pid}" 2>/dev/null || true; wait "${web_pid}" 2>/dev/null || true; fi
  if [[ -n "${api_pid}" ]]; then kill "${api_pid}" 2>/dev/null || true; wait "${api_pid}" 2>/dev/null || true; fi
  if [[ ${status} -ne 0 ]]; then
    tail -80 "${dashboard_logs}/api.log" 2>/dev/null || true
    tail -80 "${dashboard_logs}/web.log" 2>/dev/null || true
  fi
  case "${web_app_dir}" in
    "${ROOT}"/work/dashboard-e2e/web-app.*) rm -rf "${web_app_dir}" ;;
  esac
  rm -rf "${dashboard_logs}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

(cd services/api && uv run alembic upgrade head)
(cd services/api && uv run python ../../scripts/seed_dashboard_demo.py --fresh-batch)
(cd services/api && uv run python ../../scripts/seed_dev_principal.py)

python3 scripts/run_service.py --cwd services/api -- .venv/bin/python -m uvicorn flow_api.main:app --host 127.0.0.1 --port "${api_port}" \
  >"${dashboard_logs}/api.log" 2>&1 &
api_pid=$!

mkdir -p work/dashboard-e2e
web_app_dir="$(mktemp -d "${ROOT}/work/dashboard-e2e/web-app.XXXXXX")"
rsync -a \
  --exclude='node_modules/' \
  --exclude='.next/' \
  --exclude='.next-damai-e2e.*/' \
  --exclude='test-results/' \
  --exclude='playwright-report/' \
  --exclude='*.tsbuildinfo' \
  "${ROOT}/apps/web/" "${web_app_dir}/"
ln -s "${ROOT}/apps/web/node_modules" "${web_app_dir}/node_modules"

python3 scripts/run_service.py --cwd "${web_app_dir}" -- node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port "${web_port}" \
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
