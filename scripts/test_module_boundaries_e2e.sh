#!/usr/bin/env bash
# Task 2C：模块边界 E2E 门禁（动态端口、受控启动、cleanup trap）。
# 页面为静态批准 fixture，不依赖 API/数据库——只启动 Next dev。
# 用法：make test-module-boundaries-e2e 或 bash scripts/test_module_boundaries_e2e.sh
set -euo pipefail

read -r web_port < <(python3 scripts/find_free_port.py 1)
export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${web_port}"

mb_logs="$(mktemp -d)"
web_pid=""

cleanup() {
  status=$?
  if [[ -n "${web_pid}" ]]; then kill "${web_pid}" 2>/dev/null || true; wait "${web_pid}" 2>/dev/null || true; fi
  if [[ ${status} -ne 0 ]]; then
    tail -60 "${mb_logs}/web.log" 2>/dev/null || true
  fi
  rm -rf "${mb_logs}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python3 scripts/run_service.py --cwd apps/web -- node node_modules/next/dist/bin/next dev \
  --hostname 127.0.0.1 --port "${web_port}" >"${mb_logs}/web.log" 2>&1 &
web_pid=$!

python3 scripts/wait_for_services.py "127.0.0.1:${web_port}"

npx --yes pnpm@10.17.1 --filter @flow/web exec playwright test \
  e2e/navigation.spec.ts e2e/module-boundaries.spec.ts
