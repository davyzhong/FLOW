#!/usr/bin/env bash
# 大麦 synthetic 演示全旅程 E2E 门禁（Task C2）：
#   独立 compose 栈（15432/16379/19000，验收后 down -v 销毁）
#   + 迁移 + damai seed + dev principal + verify 对账
#   + 动态端口 API/Web + 八页面 Playwright（无 page mock）。
# 用法：bash scripts/test_damai_demo_e2e.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

COMPOSE=(docker compose -p damai-demo-iso -f infra/compose.damai-isolated.yaml)

export DATABASE_URL="postgresql+psycopg://flow:flow_dev_only@127.0.0.1:15432/flow"
export REDIS_URL="redis://127.0.0.1:16379/0"
export S3_ENDPOINT_URL="http://127.0.0.1:19000"
export S3_BUCKET="flow"
export S3_ACCESS_KEY="flow"
export S3_SECRET_KEY="flow_dev_only"
# S01 §2.2：development 模式认证边界需要显式 dev actor（与 scripts/seed_dev_principal.py 一致）
export FLOW_DEV_ACTOR_ID="${FLOW_DEV_ACTOR_ID:-flow-dev-bp}"

read -r api_port web_port < <(uv run python scripts/find_free_port.py 2)
export FLOW_API_INTERNAL_URL="http://127.0.0.1:${api_port}"
export PLAYWRIGHT_BASE_URL="http://127.0.0.1:${web_port}"

logs_dir="$(mktemp -d)"
api_pid=""
web_pid=""
stack_up=0
web_app_dir=""

cleanup() {
  status=$?
  if [[ -n "${web_pid}" ]]; then kill "${web_pid}" 2>/dev/null || true; wait "${web_pid}" 2>/dev/null || true; fi
  if [[ -n "${api_pid}" ]]; then kill "${api_pid}" 2>/dev/null || true; wait "${api_pid}" 2>/dev/null || true; fi
  if [[ ${status} -ne 0 ]]; then
    tail -80 "${logs_dir}/api.log" 2>/dev/null || true
    tail -80 "${logs_dir}/web.log" 2>/dev/null || true
  fi
  if [[ ${stack_up} -eq 1 ]]; then
    # down -v 偶发只移除网络不移除容器，重试一次确保卷真正销毁
    "${COMPOSE[@]}" down -v >/dev/null 2>&1 || true
    "${COMPOSE[@]}" down -v >/dev/null 2>&1 || true
  fi
  case "${web_app_dir}" in
    "${ROOT}"/work/damai-demo/web-app.*) rm -rf "${web_app_dir}" ;;
  esac
  rm -rf "${logs_dir}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# minio-init 是一次性容器：--wait 会把它的 exit(0) 误判为失败，故只对长驻服务等待，
# bucket 初始化用 run --rm 显式执行（mb --ignore-existing，幂等）
"${COMPOSE[@]}" up -d --wait --wait-timeout 180 postgres redis minio
stack_up=1
"${COMPOSE[@]}" run --rm --no-deps minio-init

(cd services/api && uv run alembic upgrade head)

mkdir -p work/damai-demo
(cd services/api && uv run python ../../scripts/seed_damai_demo.py \
  --output "${ROOT}/work/damai-demo/e2e_seed_receipt.json")
(cd services/api && uv run python ../../scripts/seed_dev_principal.py)

# 在本轮临时副本启动 Next：并行开发服务可继续使用 apps/web/.next，Next 自动更新的
# next-env.d.ts/tsconfig.json 也只落在临时副本内，不污染共享工作区。
web_app_dir="$(mktemp -d "${ROOT}/work/damai-demo/web-app.XXXXXX")"
rsync -a \
  --exclude='node_modules/' \
  --exclude='.next/' \
  --exclude='.next-damai-e2e.*/' \
  --exclude='test-results/' \
  --exclude='playwright-report/' \
  --exclude='*.tsbuildinfo' \
  "${ROOT}/apps/web/" "${web_app_dir}/"
ln -s "${ROOT}/apps/web/node_modules" "${web_app_dir}/node_modules"

python3 scripts/run_service.py --cwd services/api -- .venv/bin/python -m uvicorn flow_api.main:app --host 127.0.0.1 --port "${api_port}" \
  >"${logs_dir}/api.log" 2>&1 &
api_pid=$!

python3 scripts/run_service.py --cwd "${web_app_dir}" -- node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port "${web_port}" \
  >"${logs_dir}/web.log" 2>&1 &
web_pid=$!

uv run scripts/wait_for_services.py "127.0.0.1:${api_port}" "127.0.0.1:${web_port}"

# 先跑验收对账：上传旅程会追加新批次，必须在 verify 之后执行
(cd services/api && uv run python ../../scripts/verify_damai_demo.py \
  --api-url "http://127.0.0.1:${api_port}" --check-storage \
  --output "${ROOT}/work/damai-demo/e2e_verify_receipt.json")

npx --yes playwright test e2e/damai-demo.spec.ts
