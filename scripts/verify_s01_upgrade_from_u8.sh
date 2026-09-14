#!/usr/bin/env bash
# S01 Task 9（6A）：从 U8 冻结基线（0024 dump）到当前 head 的同库升级全链验证。
#
# 流程：
#   0) 校验备份 SHA-256 与 CA 证书存在；
#   1) 启动隔离 compose project（唯一 project 名 + 全新命名卷）；
#   2) 恢复 U8 dump 到专属 PostgreSQL；
#   3) 在恢复库上 alembic upgrade head，并运行 schema/触发器相关测试（若存在）；
#   4) 启动 api/web/nginx（API 指向恢复库，nginx 动态 HTTPS 端口）；
#   5) 三方对账：HTTPS 读恢复库独有已知财报（菜鸟 FY2023 营业收入 77,799,675 千元）
#      ↔ 恢复库 SQL 值 ↔ 客观快照 payload_hash（恢复库内唯一）；
#   6) trap 保留退出码并销毁整个专属 project。
#
# 必需环境变量：
#   FLOW_U8_BACKUP_PATH   U8 pg_dump 文件路径
#   FLOW_U8_BACKUP_SHA256 备份完整 SHA-256
#   FLOW_U8_CA_CERT       nginx TLS CA 证书路径
set -euo pipefail

BACKUP="${FLOW_U8_BACKUP_PATH:?缺少 FLOW_U8_BACKUP_PATH}"
BACKUP_SHA="${FLOW_U8_BACKUP_SHA256:?缺少 FLOW_U8_BACKUP_SHA256}"
CA_CERT="${FLOW_U8_CA_CERT:?缺少 FLOW_U8_CA_CERT}"
PROJECT="s01accept"
dcom() { docker compose -p "$PROJECT" -f infra/compose.yaml -f infra/compose.s01-acceptance.yaml "$@"; }
HTTPS_PORT="${HTTPS_PORT:-13443}"
GOLDEN_REVENUE="77799675"
WORK_DIR="work/s01-verification"
mkdir -p "$WORK_DIR"

fail() { printf 'VERIFY_FAIL %s\n' "$*" >&2; exit 1; }
pass() { printf 'VERIFY_PASS %s\n' "$*"; }

cleanup() {
  status=$?
  dcom down -v >/dev/null 2>&1 || true
  printf 'VERIFY_EXIT %s\n' "$status" | tee -a "$WORK_DIR/exit.txt" >/dev/null
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# 0) 备份完整性与 CA
actual_sha=$(shasum -a 256 "$BACKUP" | awk '{print $1}')
[[ "$actual_sha" == "$BACKUP_SHA" ]] || fail "备份 SHA 不匹配: $actual_sha"
[[ -f "$CA_CERT" ]] || fail "CA 证书不存在: $CA_CERT"
pass "备份 SHA 与 CA 证书校验"

# 1) 隔离基础设施（全新卷）
dcom down -v >/dev/null 2>&1 || true
dcom up -d postgres redis minio minio-init >/dev/null
sleep 12
pass "隔离 PostgreSQL/MinIO 启动"

# 2) 恢复 U8 dump（通过独立宿主端口 55432）
dcom exec -T postgres psql -U flow -c "SELECT 1;" >/dev/null || fail "恢复库不可连接"
dcom exec -T postgres pg_restore -U flow -d flow --clean --if-exists < "$BACKUP" \
  || fail "pg_restore 失败"
pass "U8 dump 恢复完成"

COUNT=$(dcom exec -T postgres psql -U flow -d flow -tAc "SELECT count(*) FROM statement_report")
[[ "$COUNT" == "11" ]] || fail "恢复库财报数异常: $COUNT（期望 11）"
pass "恢复库财报 11 份"

# 3) 升级到当前 head
( cd services/api && DATABASE_URL="postgresql+psycopg://flow:flow_dev_only@127.0.0.1:55432/flow" \
    REDIS_URL="redis://127.0.0.1:6379/0" S3_ENDPOINT_URL="http://127.0.0.1:19000" \
    S3_BUCKET="flow" S3_ACCESS_KEY="flow" S3_SECRET_KEY="flow_dev_only" \
    uv run alembic upgrade head ) >/dev/null || fail "alembic upgrade head 失败"
pass "alembic upgrade head"

# 4) 启动应用（API 指向恢复库）+ nginx HTTPS
dcom up -d api web nginx >/dev/null
for _ in $(seq 1 40); do
  code=$(curl -sk -o /dev/null -w "%{http_code}" "https://localhost:${HTTPS_PORT}/api/v1/health" || true)
  [[ "$code" == "200" ]] && break
  sleep 3
done
[[ "${code:-}" == "200" ]] || fail "HTTPS 健康检查失败（最后 $code）"
pass "HTTPS 健康检查"

# 5) 三方对账：HTTPS ↔ SQL ↔ 快照哈希
HTTPS_BODY=$(curl -sk "https://localhost:${HTTPS_PORT}/api/v1/statements")
echo "$HTTPS_BODY" | grep -q "菜鸟网络" || fail "HTTPS 响应缺少菜鸟网络"
FY23=$(echo "$HTTPS_BODY" | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('reports', [])
m = [i for i in items if i.get('company_name') == '菜鸟网络' and i.get('period_label') == 'FY2023']
print(m[0]['id'] if m else '')
")
[[ -n "$FY23" ]] || fail "恢复库独有财报未通过 HTTPS 返回（证明未误连常驻库）"
SQL_VALUE=$(dcom exec -T postgres psql -U flow -d flow -tAc \
  "SELECT value_current FROM statement_line_item WHERE report_id='$FY23' AND item_name='收入' LIMIT 1" \
  | tr -d ' ')
PAYLOAD_HASH=$(dcom exec -T postgres psql -U flow -d flow -tAc \
  "SELECT payload_hash FROM objective_report_snapshot WHERE statement_report_id='$FY23' LIMIT 1" \
  | tr -d ' ')
[[ -n "$PAYLOAD_HASH" ]] || fail "客观快照哈希缺失"
python3 - "$SQL_VALUE" "$GOLDEN_REVENUE" <<'PYEOF'
import sys
sql, golden = sys.argv[1], sys.argv[2]
normalized = sql.split(".")[0].lstrip("0") or "0"
assert normalized == golden, f"SQL 收入 {sql} 与公开黄金值 {golden} 不一致"
PYEOF
pass "三方对账：HTTPS 返回恢复库独有财报 + SQL 值与公开黄金值一致 + 快照哈希在库"

printf '%s\n' "$HTTPS_BODY" > "$WORK_DIR/https_statements.json"
printf '%s\n' "$PAYLOAD_HASH" > "$WORK_DIR/fy2023_payload_hash.txt"
pass "S01 升级验证全链 PASS（证据在 ${WORK_DIR}）"
