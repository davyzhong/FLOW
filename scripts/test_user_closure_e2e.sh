#!/usr/bin/env bash
# Pilot Readiness Phase 1 — 用户闭环端到端门禁（Task 9）。
# 顺序：起完整栈 → Playwright 浏览器用户闭环 → 契约漂移 → Phase 3/6/7/9 回归 →
#       API 全量 → 前端 lint/typecheck/vitest。
set -euo pipefail

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://127.0.0.1:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"

make infra-up

read -r api_port web_port < <(uv run python scripts/find_free_port.py 2)
export FLOW_API_INTERNAL_URL="http://127.0.0.1:${api_port}"
export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${web_port}"

closure_logs="$(mktemp -d)"
api_pid=""
web_pid=""

cleanup() {
  status=$?
  if [[ -n "${web_pid}" ]]; then kill "${web_pid}" 2>/dev/null || true; fi
  if [[ -n "${api_pid}" ]]; then kill "${api_pid}" 2>/dev/null || true; fi
  if [[ ${status} -ne 0 ]]; then
    tail -60 "${closure_logs}/api.log" 2>/dev/null || true
    tail -60 "${closure_logs}/web.log" 2>/dev/null || true
  fi
  rm -rf "${closure_logs}"
}
trap cleanup EXIT

(cd services/api && uv run alembic upgrade head)
(cd services/api && uv run uvicorn flow_api.main:app --host 127.0.0.1 --port "${api_port}") \
  >"${closure_logs}/api.log" 2>&1 &
api_pid=$!

npx --yes pnpm@10.17.1 --filter @flow/web exec next dev --hostname 127.0.0.1 --port "${web_port}" \
  >"${closure_logs}/web.log" 2>&1 &
web_pid=$!

echo "DEBUG api_port=${api_port} web_port=${web_port} PLAYWRIGHT_BASE_URL=${PLAYWRIGHT_BASE_URL-UNSET}"
uv run scripts/wait_for_services.py "127.0.0.1:${api_port}" "127.0.0.1:${web_port}"
(cd services/api && uv run python ../../scripts/seed_dashboard_demo.py --fresh-batch)

echo "== 1/6 浏览器用户闭环（Playwright） =="
npx --yes pnpm@10.17.1 --filter @flow/web exec playwright test e2e/user-closure.spec.ts

echo "== 2/6 契约漂移 =="
make contracts
make contracts-check

echo "== 3/6 Phase 3/6/7/9 回归门禁 =="
bash scripts/test_intake_e2e.sh
bash scripts/test_dashboard.sh
bash scripts/test_investigation_e2e.sh
bash scripts/test_publishing_golden.sh

echo "== 4/6 API 全量 =="
(cd services/api && uv run pytest -q)

echo "== 5/6 前端 lint/typecheck/vitest =="
npx --yes pnpm@10.17.1 --filter @flow/web lint
npx --yes pnpm@10.17.1 --filter @flow/web exec tsc --noEmit
npx --yes pnpm@10.17.1 --filter @flow/web exec vitest run

echo "== 6/6 完成 =="
echo "user-closure e2e gate PASSED"
