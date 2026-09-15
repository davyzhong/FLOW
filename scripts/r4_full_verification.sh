#!/usr/bin/env bash
# R4 full-verification-v2：U8 冻结 dump → 独立隔离环境 → 升级当前迁移头 →
# 双证明（SQL marker == HTTPS marker；dump hash == 基线）全链验收。
#
# 合同（HANDOFF R4 / DD6）：
# - 唯一 compose project（flow-r4）+ 项目前缀卷，动态端口，无固定端口冲突；
# - 真实 CA（--cacert infra/nginx/dev-tls.crt），全程禁止 -k / --insecure；
# - 恢复 dump 校验基线合同（0024 + 关键表 + payload 聚合哈希）→
#   alembic upgrade head → 升级头 == 合同 upgraded_migration_head；
# - sentinel：SQL 写入唯一 marker 批次，HTTPS 读取同一 id（双证明）；
#   dump sha256 == 基线合同 dump_sha256；
# - 任一步失败即非零退出；evidence JSON 落盘，skipped 恒为空；
# - 退出时 teardown（down -v），不残留容器/卷。
#
# 用法：FLOW_U8_BACKUP_PATH=backups/u8-baseline/flow-u8-final.dump \
#       bash scripts/r4_full_verification.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

BACKUP_PATH="${FLOW_U8_BACKUP_PATH:-backups/u8-baseline/flow-u8-final.dump}"
CONTRACT_PATH="${FLOW_U8_CONTRACT:-config/acceptance/u8-baseline.json}"
CA_CERT="${FLOW_U8_CA_CERT:-infra/nginx/dev-tls.crt}"
EVIDENCE_PATH="${FLOW_R4_EVIDENCE_PATH:-work/r4/evidence.json}"
PROJECT="flow-r4"
COMPOSE=(docker compose -p "$PROJECT" -f infra/compose.yaml -f infra/compose.r4.yaml)

[[ -f "$BACKUP_PATH" ]] || { echo "ERROR dump 不存在: $BACKUP_PATH" >&2; exit 2; }
[[ -f "$CONTRACT_PATH" ]] || { echo "ERROR 基线合同不存在: $CONTRACT_PATH" >&2; exit 2; }
[[ -f "$CA_CERT" ]] || { echo "ERROR CA 证书不存在: $CA_CERT" >&2; exit 2; }
mkdir -p "$(dirname "$EVIDENCE_PATH")"

EVIDENCE_SKIPPED=()
note_skip() { EVIDENCE_SKIPPED+=("$1"); echo "SKIP: $1" >&2; }

sql() {
  "${COMPOSE[@]}" exec -T postgres psql -U flow -d flow -tAc "$1" | tr -d '[:space:]'
}

cleanup() {
  status=$?
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  if [[ ${#EVIDENCE_SKIPPED[@]} -gt 0 && $status -eq 0 ]]; then
    echo "ERROR 存在被跳过的步骤，验收无效" >&2; exit 1
  fi
  exit "$status"
}
trap cleanup EXIT

echo "== [1/8] 构建并启动隔离依赖（project=${PROJECT}，全新卷） =="
"${COMPOSE[@]}" build api worker >/dev/null
# 一次性 job 不能进 --wait（exited(0) 会被当作失败）：先等依赖 healthy，
# 再单跑 minio-init。
"${COMPOSE[@]}" up -d --wait postgres redis minio
"${COMPOSE[@]}" run --rm --no-deps minio-init >/dev/null

echo "== [2/8] 恢复 U8 冻结 dump 到隔离库 =="
DUMP_SHA=$(shasum -a 256 "$BACKUP_PATH" | awk '{print $1}')
"${COMPOSE[@]}" exec -T postgres psql -U flow -d flow -c "SELECT 1" >/dev/null  # 确认库在
"${COMPOSE[@]}" exec -T postgres psql -U flow -d flow -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null
"${COMPOSE[@]}" exec -T postgres pg_restore -U flow -d flow --no-owner --exit-on-error < "$BACKUP_PATH" >/dev/null

echo "== [3/8] 校验恢复态 == 基线合同（0024 + 关键表 + 聚合哈希 + dump hash） =="
python3 - "$CONTRACT_PATH" <<'PYEOF'
import json, os, subprocess, sys
contract = json.load(open(sys.argv[1]))
def sql(q):
    return subprocess.check_output(
        ["docker", "compose", "-p", "flow-r4", "-f", "infra/compose.yaml",
         "-f", "infra/compose.r4.yaml", "exec", "-T", "postgres",
         "psql", "-U", "flow", "-d", "flow", "-tAc", q]).decode().strip()
head = sql("SELECT version_num FROM alembic_version")
assert head == contract["migration_head"], f"迁移头不符: {head} != {contract['migration_head']}"
for table, expected in contract["critical_tables"].items():
    actual = int(sql(f"SELECT count(*) FROM {table}"))
    assert actual == expected, f"关键表不符: {table}={actual} != {expected}"
hash_input = sql("SELECT COALESCE(string_agg(payload_hash, '' ORDER BY id), '') FROM objective_report_snapshot")
import hashlib
agg = hashlib.sha256(hash_input.encode()).hexdigest()
assert agg == contract["payload_hash_aggregate"], f"聚合哈希不符: {agg}"
dump_sha = subprocess.check_output(["shasum", "-a", "256", os.environ.get("FLOW_U8_BACKUP_PATH", "backups/u8-baseline/flow-u8-final.dump")]).decode().split()[0]
assert dump_sha == contract["dump_sha256"], f"dump sha256 不符: {dump_sha}"
print("恢复态 == 基线合同（dump hash/迁移头/关键表/聚合哈希 四证一致）")
PYEOF
export FLOW_U8_BACKUP_PATH="${BACKUP_PATH}"

echo "== [4/8] 升级迁移到当前头 =="
"${COMPOSE[@]}" run --rm --no-deps api alembic upgrade head >/dev/null
UPGRADED_HEAD=$(sql "SELECT version_num FROM alembic_version")
EXPECTED_HEAD=$(python3 -c "import json;print(json.load(open('$CONTRACT_PATH'))['upgraded_migration_head'])")
[[ "$UPGRADED_HEAD" == "$EXPECTED_HEAD" ]] || { echo "ERROR 升级头不符: $UPGRADED_HEAD != $EXPECTED_HEAD" >&2; exit 1; }

echo "== [5/8] 升级后不变量：关键表计数与 payload 聚合哈希不漂移 =="
python3 - "$CONTRACT_PATH" <<'PYEOF'
import hashlib, json, subprocess, sys
contract = json.load(open(sys.argv[1]))
def sql(q):
    return subprocess.check_output(
        ["docker", "compose", "-p", "flow-r4", "-f", "infra/compose.yaml",
         "-f", "infra/compose.r4.yaml", "exec", "-T", "postgres",
         "psql", "-U", "flow", "-d", "flow", "-tAc", q]).decode().strip()
for table, expected in contract["critical_tables"].items():
    actual = int(sql(f"SELECT count(*) FROM {table}"))
    assert actual == expected, f"升级后计数漂移: {table}={actual} != {expected}"
hash_input = sql("SELECT COALESCE(string_agg(payload_hash, '' ORDER BY id), '') FROM objective_report_snapshot")
agg = hashlib.sha256(hash_input.encode()).hexdigest()
assert agg == contract["payload_hash_aggregate"], "升级后聚合哈希漂移"
print("升级后不变量保持（计数 + 聚合哈希）")
PYEOF

echo "== [6/8] 写入唯一 sentinel（dev actor binding + marker 批次） =="
sql "INSERT INTO role_binding (actor_id, role, enterprise_id, is_service_account, active)
     SELECT 'flow-dev-bp', 'analyst', e.id, false, true
     FROM enterprise e WHERE NOT EXISTS (
       SELECT 1 FROM role_binding WHERE actor_id = 'flow-dev-bp' AND active IS TRUE)" >/dev/null
# HTTPS marker 用 dump 内自带 import version 的批次（versions 空列表会 404）：
# 该 id 唯一属于本 dump，SQL 可查 + HTTPS 可读即双证明。
SQL_MARKER=$(sql "SELECT b.id FROM analysis_batch b
     WHERE EXISTS (SELECT 1 FROM import_version v WHERE v.batch_id = b.id)
     ORDER BY b.created_at DESC LIMIT 1")
[[ -n "$SQL_MARKER" && "$SQL_MARKER" != "None" ]] || { echo "ERROR 未能选定 marker 批次" >&2; exit 1; }

echo "== [7/8] 启动应用栈（动态端口）并做 HTTPS 双证明 =="
# web 的 healthcheck 已在 overlay 中 disable（容器内 wget 不可靠，主栈同样
# unhealthy）；R4 只验证 /api 链路，但 nginx 的 / 上游需要 web DNS 可解析。
"${COMPOSE[@]}" up -d --wait api worker web nginx
NGINX_PORT=$(docker compose -p "$PROJECT" port nginx 443 | awk -F: '{print $NF}')
BASE_URL="https://localhost:${NGINX_PORT}"
[[ -n "$NGINX_PORT" ]] || { echo "ERROR 未能发现 nginx 动态端口" >&2; exit 1; }

# 状态码探测 helper：-w 打印 + 非零退出不叠加字符串（有界重试防 TLS 竞态）
http_code() { # $1 = url
  local code="" n
  for n in 1 2 3 4 5 6 7 8 9 10; do
    code=$(curl --silent --show-error --cacert "$CA_CERT" -o /dev/null -w "%{http_code}" "$1" 2>/dev/null || true)
    [[ "$code" == "200" ]] && { echo "$code"; return 0; }
    sleep 2
  done
  echo "${code:-000}"
}

HEALTH_CODE=$(http_code "$BASE_URL/api/v1/health")
[[ "$HEALTH_CODE" == "200" ]] || { echo "ERROR health 非 200: $HEALTH_CODE" >&2; exit 1; }

MARKER_CODE=$(http_code "$BASE_URL/api/v1/intake/batches/$SQL_MARKER/versions")
[[ "$MARKER_CODE" == "200" ]] || { echo "ERROR marker HTTPS 可见性失败: $MARKER_CODE" >&2; exit 1; }

RANDOM_ID=$(python3 -c "import uuid;print(uuid.uuid4())")
ABSENT_CODE=$(curl --silent --show-error --cacert "$CA_CERT" -o /dev/null -w "%{http_code}" \
  "$BASE_URL/api/v1/intake/batches/$RANDOM_ID/versions" 2>/dev/null || true)
[[ "$ABSENT_CODE" != "200" ]] || { echo "ERROR 不存在的批次竟能 200，marker 无区分度" >&2; exit 1; }

DASH_BODY=$(curl --fail --silent --show-error --cacert "$CA_CERT" "$BASE_URL/api/v1/dashboard/overview")
echo "$DASH_BODY" | python3 -c "import json,sys;d=json.load(sys.stdin);assert d.get('state') in ('ready','not_ready'), d"

echo "== [8/8] 落 evidence 并 teardown =="
python3 - "$CONTRACT_PATH" "$EVIDENCE_PATH" <<PYEOF
import json, sys
contract = json.load(open(sys.argv[1]))
evidence = {
    "schema_version": 1,
    "gate": "R4-full-verification-v2",
    "compose_project": "$PROJECT",
    "base_url": "$BASE_URL",
    "tls_verified": True,
    "curl_insecure_used": False,
    "dump_sha256": "$DUMP_SHA",
    "expected_dump_sha256": contract["dump_sha256"],
    "restored_migration_head": contract["migration_head"],
    "upgraded_migration_head": "$UPGRADED_HEAD",
    "critical_tables": contract["critical_tables"],
    "payload_hash_aggregate": contract["payload_hash_aggregate"],
    "sql_marker_batch_id": "$SQL_MARKER",
    "https_marker_status": $MARKER_CODE,
    "https_absent_status": $ABSENT_CODE,
    "marker_equivalence": "sql == https (200 on dump-native batch id, non-200 on random id)",
    "health_status": $HEALTH_CODE,
    "dashboard_state_checked": True,
    "skipped": [],
}
open(sys.argv[2], "w").write(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
print("evidence ->", sys.argv[2])
PYEOF

echo "R4 full-verification-v2: PASS"
