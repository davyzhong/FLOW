#!/usr/bin/env bash
# 把 docs/implementation/p5/ 下全部 P5 反向解析财报 YAML 导入 statement_report。
# 幂等：同一 (stock_code, period_label, report_kind) 内容哈希不变则重建行项目，
# 内容变化按重述递增版本（见 flow_api.statements.importer）。
#
# 用法（仓库根目录）：
#   bash scripts/seed_p5_statements.sh
# 需要 DATABASE_URL 指向目标库（缺省取本机 Compose 开发库），
# 以及 services/api 的 Python 环境（优先 .venv，其次 uv run）。
set -euo pipefail
cd "$(dirname "$0")/.."

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://localhost:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"

if [ -x services/api/.venv/bin/python ]; then
  PY=(services/api/.venv/bin/python)
else
  PY=(uv run --directory services/api python)
fi

# .venv 的 editable 安装可能指向历史 worktree；强制以本仓库源码为准。
export PYTHONPATH="$PWD/services/api/src${PYTHONPATH:+:$PYTHONPATH}"

seed() {
  # $1 yaml 文件名  $2 公司  $3 股票代码  $4 报告类型  $5 期间标签
  "${PY[@]}" scripts/seed_statement_reports.py \
    --yaml "docs/implementation/p5/$1" \
    --company "$2" --stock-code "$3" \
    --report-kind "$4" --period-label "$5"
}

seed sf_2026q1_statements.yaml       顺丰控股   002352.SZ   一季报       2026Q1
seed tencent_2026q2_statements.yaml  腾讯控股   0700.HK     中期业绩公告 2026Q2
seed jdl_2025fy_statements.yaml      京东物流   2618.HK     年报         FY2025
for y in 2019 2020 2021 2022 2023 2024 2025 2026; do
  seed "alibaba_${y}fy_statements.yaml" 阿里巴巴 9988.HK 年报 "FY${y}"
done
for y in 2021 2022 2023; do
  seed "cainiao_${y}fy_statements.yaml" 菜鸟集团 PVT.CAINIAO 招股书申报稿 "FY${y}"
done

# S01 §3.2：legacy Bearer（AUTH_TOKEN）需要 DB 里存在一条 active service_account
# RoleBinding，否则全部 API 401。本地开发库幂等补一条。
"${PY[@]}" - <<'PY'
import os
import psycopg

url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
with psycopg.connect(url, autocommit=True) as conn:
    conn.execute(
        """
        INSERT INTO role_binding (actor_id, role, enterprise_id, is_service_account, active)
        SELECT 'local-dev-web', 'service_account', gen_random_uuid(), true, true
        WHERE NOT EXISTS (
            SELECT 1 FROM role_binding
            WHERE role = 'service_account' AND is_service_account AND active
        )
        """
    )
print("role_binding: service_account 绑定已确认（幂等）")
PY

echo "P5 财报种子完成：5 家公司 14 份报告。"
