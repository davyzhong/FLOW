#!/usr/bin/env bash
# U8-A 真实存储完整旅程验收：冻结 → 发布（真实 MinIO）→ 下载 → SHA-256 校验
# + 失败态（404 未知尝试 / 409 对象缺失）。
# 前置：compose 栈健康、库内有已发布财报（种子链已跑）。
# 用法：bash scripts/u8a_storage_journey.sh [report_id]
set -euo pipefail

API="${API:-http://localhost:8000}"
REPORT_ID="${1:-}"
OUT="${OUT:-docs/operations/u8a-journey-evidence.jsonl}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$(dirname "$OUT")"
: > "$OUT"

log() { printf '{"step":"%s","detail":%s}\n' "$1" "$2" >> "$OUT"; }
say() { printf '%s\n' "$*"; }

# 1. 选一份财报
if [[ -z "$REPORT_ID" ]]; then
  REPORT_ID=$(curl -sf "$API/api/v1/statements" | python3 -c "import json,sys; items=json.load(sys.stdin).get('reports', []); print(items[0]['id'] if items else '')")
fi
if [[ -z "$REPORT_ID" ]]; then
  say "FAIL: 库内无财报，先跑种子链"
  exit 1
fi
say "U8-A 旅程开始 report_id=${REPORT_ID}"
log "journey_start" "\"report_id\":\"$REPORT_ID\""

# 2. 冻结客观快照（幂等）
freeze=$(curl -sf -X POST "$API/api/v1/statements/$REPORT_ID/objective-snapshot")
SNAPSHOT_ID=$(echo "$freeze" | python3 -c "import json,sys; print(json.load(sys.stdin)['snapshot_id'])")
PAYLOAD_HASH=$(echo "$freeze" | python3 -c "import json,sys; print(json.load(sys.stdin)['payload_hash'])")
say "冻结快照 snapshot_id=${SNAPSHOT_ID}"
log "objective_frozen" "{\"snapshot_id\":\"$SNAPSHOT_ID\",\"payload_hash\":\"$PAYLOAD_HASH\"}"

# 3. 经营概览发布（冻结→渲染→写真实 MinIO→登记尝试）
publish=$(curl -sf -X POST "$API/api/v1/operations/overview/$REPORT_ID/publish" \
  -H "Content-Type: application/json" \
  -d '{"formats":["html","pdf"],"actor":"flow.u8a.journey"}')
PUB_SNAPSHOT=$(echo "$publish" | python3 -c "import json,sys; print(json.load(sys.stdin)['report_snapshot_id'])")
say "运营发布完成 pub_snapshot=${PUB_SNAPSHOT}"
log "operations_published" "{\"snapshot_id\":\"$PUB_SNAPSHOT\"}"

# 4. 逐个下载并校验 SHA-256
export PUB_SNAPSHOT API
# 渲染异步进行：轮询等待任一尝试可下载（最长 60s）
ATTEMPTS_JSON=""
for _ in $(seq 1 30); do
  ATTEMPTS_JSON=$(curl -sf "$API/api/v1/operations/snapshots/$PUB_SNAPSHOT/attempts" || true)
  READY=$(echo "$ATTEMPTS_JSON" | python3 -c "import json,sys; a=json.load(sys.stdin).get('attempts', []); print(sum(1 for x in a if x.get('download_available')))" 2>/dev/null || echo 0)
  [[ "$READY" != "0" ]] && break
  sleep 2
done
printf '%s' "$ATTEMPTS_JSON" > /tmp/u8a_attempts.json
python3 "$SCRIPT_DIR/u8a_download_attempts.py" /tmp/u8a_attempts.json
log "downloads" "\"见 u8a_download_attempts.py 输出（checked=N sha_ok=N）\""

# 5. 失败态：未知尝试（404）
BAD_ID="00000000-0000-0000-0000-000000000000"
code404=$(curl -s -o /dev/null -w "%{http_code}" \
  "$API/api/v1/publishing/attempts/$BAD_ID/download")
say "失败态 未知尝试 HTTP ${code404}（期望 404）"
log "failure_unknown_attempt" "{\"http\":$code404}"

# 6. 失败态：删 MinIO 对象后下载（409 missing_object）
OBJECT_KEY=$(PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -m1 postgres)
docker exec "$PG_CONTAINER" psql -U flow -d flow -t -A -c \
  "SELECT so.object_key FROM stored_object so JOIN publication_attempt pa ON pa.stored_object_id = so.id WHERE (pa.report_snapshot_id = '$PUB_SNAPSHOT' OR pa.objective_report_snapshot_id = '$PUB_SNAPSHOT') AND pa.status='succeeded' AND pa.stored_object_id IS NOT NULL LIMIT 1" \
  | head -1)
FIRST_ATTEMPT=$(echo "$ATTEMPTS_JSON" | python3 -c "import json,sys; a=[x for x in json.load(sys.stdin)['attempts'] if x.get('download_available')]; print(a[0]['attempt_id'] if a else '')")
if [[ -n "$OBJECT_KEY" && -n "$FIRST_ATTEMPT" ]]; then
  SERVICES_API="$(cd "$SCRIPT_DIR/../services/api" && pwd)"
  "$SERVICES_API/.venv/bin/python" "$SCRIPT_DIR/flow_delete_object.py" "$OBJECT_KEY"
  say "已从 MinIO 删除对象 $OBJECT_KEY"
  code_missing=$(curl -s -o /dev/null -w "%{http_code}" \
    "$API/api/v1/publishing/attempts/$FIRST_ATTEMPT/download")
  say "失败态 对象缺失 HTTP ${code_missing}（期望 409）"
  log "failure_object_missing" "{\"http\":$code_missing,\"deleted_key\":\"$OBJECT_KEY\"}"
else
  say "（无可删对象，跳过对象缺失用例）"
fi

say "U8-A 旅程结束，证据写入 $OUT"
