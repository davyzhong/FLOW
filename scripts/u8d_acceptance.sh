#!/usr/bin/env bash
# U8-D strict clean-environment acceptance. Every required check is fail-closed.
set -euo pipefail

PROJECT="${U8D_COMPOSE_PROJECT:-u8accept}"
COMPOSE=(docker compose -p "$PROJECT" -f infra/compose.yaml)
MAIN_COMPOSE=(docker compose -p flow -f infra/compose.yaml)
BASE_URL="${FLOW_U8_BASE_URL:?FLOW_U8_BASE_URL is required}"
CA_CERT="${FLOW_U8_CA_CERT:-infra/nginx/dev-tls.crt}"
OUT="${U8D_ACCEPTANCE_LOG:-work/u8-acceptance/u8d-acceptance.md}"
EVIDENCE_PATH="${U8D_EVIDENCE_PATH:-work/u8-acceptance/evidence.json}"
DOWNLOAD_SUMMARY="${U8_DOWNLOAD_SUMMARY:-work/u8-acceptance/downloads.json}"

case "$BASE_URL" in
  https://*) ;;
  *) echo "ERROR FLOW_U8_BASE_URL must use https://" >&2; exit 2 ;;
esac
[[ -f "$CA_CERT" ]] || { echo "ERROR CA certificate not found: $CA_CERT" >&2; exit 2; }
mkdir -p "$(dirname "$OUT")" "$(dirname "$EVIDENCE_PATH")" "$(dirname "$DOWNLOAD_SUMMARY")"

say() { printf '%s\n' "$*"; }
cleanup() {
  "${COMPOSE[@]}" down -v >/dev/null 2>&1 || true
  "${MAIN_COMPOSE[@]}" up -d >/dev/null 2>&1 || true
}
trap cleanup EXIT

cat > "$OUT" <<EOF
# U8-D 严格干净环境部署验收

- 时间：$(date '+%F %T %z')
- 方式：隔离 compose project（${PROJECT}，全新卷）
EOF

say "[1/7] 停常驻栈，释放验收端口"
"${MAIN_COMPOSE[@]}" down >/dev/null 2>&1

say "[2/7] 启动隔离基础设施（全新卷）"
"${COMPOSE[@]}" up -d postgres redis minio minio-init >/dev/null
"${COMPOSE[@]}" up -d --wait --wait-timeout 180 postgres redis minio >/dev/null

say "[3/7] 迁移到 head"
export DATABASE_URL="postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow"
export REDIS_URL="redis://127.0.0.1:6379/0"
export S3_ENDPOINT_URL="http://127.0.0.1:9000"
export S3_BUCKET="flow" S3_ACCESS_KEY="flow" S3_SECRET_KEY="flow_dev_only"
( cd services/api && uv run alembic upgrade head ) >> "$OUT" 2>&1

say "[4/7] 启动应用、TLS 入口和健康检查"
"${COMPOSE[@]}" up -d --build --wait --wait-timeout 300 api web worker nginx >/dev/null
API_CODE=$(curl --fail --silent --show-error --cacert "$CA_CERT" -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/health")
WEB_CODE=$(curl --fail --silent --show-error --cacert "$CA_CERT" -o /dev/null -w "%{http_code}" "$BASE_URL/")
[[ "$API_CODE" == "200" && "$WEB_CODE" == "200" ]]
echo "- TLS 健康检查：api=${API_CODE} web=${WEB_CODE}" >> "$OUT"

say "[5/7] 验证空态、导入种子并执行真实存储旅程"
EMPTY_STATEMENTS=$(curl --fail --silent --show-error --cacert "$CA_CERT" "$BASE_URL/api/v1/statements" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('reports', [])))")
[[ "$EMPTY_STATEMENTS" == "0" ]]
echo "- 干净库空态：statements=0" >> "$OUT"
( cd services/api && uv run python -c "
from pathlib import Path
from flow_api.infrastructure.db import get_session_factory
from flow_api.metric_library_store.importer import import_all
with get_session_factory()() as session:
    print('种子导入:', import_all(session, Path('../../config/metrics')))
    session.commit()
" ) >> "$OUT"
( cd services/api && uv run python ../../scripts/seed_statement_reports.py \
    --yaml ../../docs/implementation/p5/cainiao_2021fy_statements.yaml \
    --company 菜鸟网络 --stock-code CAINIAO --report-kind 年报 --period-label FY2021 >/dev/null
  uv run python - <<'PYEOF'
from sqlalchemy import select
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.statement import StatementReport
from flow_api.statements.normalization import normalize_report
from flow_api.statements.review import ReviewService
from flow_api.publishing.objective_freeze import freeze_objective_statement_report
with get_session_factory()() as session:
    reports = list(session.scalars(select(StatementReport)).all())
    for report in reports:
        normalize_report(session, report)
        ReviewService(session).publish(report.id, operator="flow.u8d.acceptance")
        freeze_objective_statement_report(session, report_id=report.id)
    session.commit()
    print("最小财报种子+冻结:", len(reports))
PYEOF
) >> "$OUT"
API="http://localhost:8000" OUT="work/u8-acceptance/u8a-journey-evidence.jsonl" \
  U8_DOWNLOAD_SUMMARY="$DOWNLOAD_SUMMARY" bash scripts/u8a_storage_journey.sh | tee -a "$OUT"

psql_value() {
  "${COMPOSE[@]}" exec -T postgres psql -U flow -d flow -tAc "$1" | tr -d '[:space:]'
}
BEFORE_STATEMENTS=$(psql_value "SELECT count(*) FROM statement_report")
BEFORE_SNAPSHOTS=$(psql_value "SELECT count(*) FROM objective_report_snapshot")
BEFORE_HASH_INPUT=$(psql_value "SELECT string_agg(payload_hash, '' ORDER BY id) FROM objective_report_snapshot")
EXPECTED_HASH=$(printf '%s' "$BEFORE_HASH_INPUT" | shasum -a 256 | awk '{print $1}')

say "[6/7] 严格备份恢复并验证应用健康"
COMPOSE_PROJECT="$PROJECT" BACKUP_HEALTH_URL="http://localhost:8000/api/v1/health" \
  bash scripts/backup_restore_drill.sh work/u8-acceptance/backups | tee -a "$OUT"
AFTER_STATEMENTS=$(psql_value "SELECT count(*) FROM statement_report")
AFTER_SNAPSHOTS=$(psql_value "SELECT count(*) FROM objective_report_snapshot")
AFTER_HASH_INPUT=$(psql_value "SELECT string_agg(payload_hash, '' ORDER BY id) FROM objective_report_snapshot")
RESTORED_HASH=$(printf '%s' "$AFTER_HASH_INPUT" | shasum -a 256 | awk '{print $1}')
[[ "$BEFORE_STATEMENTS" == "$AFTER_STATEMENTS" ]]
[[ "$BEFORE_SNAPSHOTS" == "$AFTER_SNAPSHOTS" ]]
[[ "$EXPECTED_HASH" == "$RESTORED_HASH" ]]

say "[7/7] 写入并验证机器证据"
export MODE=full BASE_URL API_CODE WEB_CODE BEFORE_STATEMENTS AFTER_STATEMENTS
export BEFORE_SNAPSHOTS AFTER_SNAPSHOTS EXPECTED_HASH RESTORED_HASH DOWNLOAD_SUMMARY EVIDENCE_PATH
python3 - <<'PYEOF'
import json
import os
from pathlib import Path

downloads = json.loads(Path(os.environ["DOWNLOAD_SUMMARY"]).read_text(encoding="utf-8"))["downloads"]
evidence = {
    "schema_version": 1,
    "mode": os.environ["MODE"],
    "base_url": os.environ["BASE_URL"],
    "tls_verified": True,
    "health_status": int(os.environ["API_CODE"]),
    "web_status": int(os.environ["WEB_CODE"]),
    "downloads": downloads,
    "restore_exit_code": 0,
    "critical_tables": {
        "statement_report": {"before": int(os.environ["BEFORE_STATEMENTS"]), "after": int(os.environ["AFTER_STATEMENTS"])},
        "objective_report_snapshot": {"before": int(os.environ["BEFORE_SNAPSHOTS"]), "after": int(os.environ["AFTER_SNAPSHOTS"])},
    },
    "expected_payload_hash": os.environ["EXPECTED_HASH"],
    "restored_payload_hash": os.environ["RESTORED_HASH"],
    "skipped": [],
}
Path(os.environ["EVIDENCE_PATH"]).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
PYEOF
python3 scripts/u8_acceptance_evidence.py "$EVIDENCE_PATH"
say "U8-D strict acceptance PASS"
