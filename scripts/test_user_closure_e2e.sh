#!/usr/bin/env bash
# Pilot Readiness Phase 1 — 用户闭环端到端门禁（Task 9）。
# 串联：基础设施 → API 全量 → 契约漂移 → Intake/发布/Investigation/Dashboard 回归 →
#       前端 lint/typecheck/vitest → Playwright 浏览器闭环。
set -euo pipefail

REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPOSITORY_ROOT"


echo "== 1/7 基础设施 =="
make infra-up

echo "== 2/7 API 全量测试 =="
(cd services/api && uv run pytest -q)

echo "== 3/7 契约漂移检查 =="
make contracts
make contracts-check

echo "== 4/7 Phase 3/9/7/6 回归门禁 =="
bash scripts/test_intake_e2e.sh
bash scripts/test_publishing_golden.sh
bash scripts/test_investigation_e2e.sh
bash scripts/test_dashboard.sh

echo "== 5/7 前端 lint/typecheck/vitest =="
npx --yes pnpm@10.17.1 --filter @flow/web lint
npx --yes pnpm@10.17.1 --filter @flow/web exec tsc --noEmit
npx --yes pnpm@10.17.1 --filter @flow/web exec vitest run

echo "== 6/7 浏览器闭环 (Playwright) =="
bash scripts/test_dashboard.sh 2>/dev/null || true   # 确保栈已起（幂等）
npx --yes pnpm@10.17.1 --filter @flow/web exec playwright test e2e/user-closure.spec.ts

echo "== 7/7 完成 =="
echo "user-closure e2e gate PASSED"
