#!/usr/bin/env bash
# Restore the frozen U8 dump into a disposable database and validate its contract.
set -euo pipefail

BACKUP_PATH="${1:?backup path required}"
RESTORE_DATABASE="${2:?isolated database name required}"
EVIDENCE_PATH="${3:?evidence path required}"
BASE_URL="${FLOW_U8_BASE_URL:?FLOW_U8_BASE_URL is required}"
CA_CERT="${FLOW_U8_CA_CERT:-infra/nginx/dev-tls.crt}"
CONTRACT_PATH="${FLOW_U8_BASELINE_CONTRACT:-config/acceptance/u8-baseline.json}"
COMPOSE=(docker compose -p flow -f infra/compose.yaml)

[[ "$RESTORE_DATABASE" =~ ^flow_u8_accept_[a-zA-Z0-9_]+$ ]] || {
  echo "ERROR isolated database must start with flow_u8_accept_" >&2
  exit 2
}
[[ -f "$BACKUP_PATH" ]] || { echo "ERROR backup not found: $BACKUP_PATH" >&2; exit 2; }
[[ -f "$CONTRACT_PATH" ]] || { echo "ERROR baseline contract not found: $CONTRACT_PATH" >&2; exit 2; }
[[ -f "$CA_CERT" ]] || { echo "ERROR CA certificate not found: $CA_CERT" >&2; exit 2; }
mkdir -p "$(dirname "$EVIDENCE_PATH")"

cleanup() {
  "${COMPOSE[@]}" exec -T postgres dropdb -U flow --if-exists "$RESTORE_DATABASE" >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup
"${COMPOSE[@]}" exec -T postgres createdb -U flow "$RESTORE_DATABASE"
"${COMPOSE[@]}" exec -T postgres pg_restore -U flow -d "$RESTORE_DATABASE" --no-owner --exit-on-error < "$BACKUP_PATH"

psql_value() {
  "${COMPOSE[@]}" exec -T postgres psql -U flow -d "$RESTORE_DATABASE" -tAc "$1" | tr -d '[:space:]'
}
STATEMENTS=$(psql_value "SELECT count(*) FROM statement_report")
SNAPSHOTS=$(psql_value "SELECT count(*) FROM objective_report_snapshot")
METRICS=$(psql_value "SELECT count(*) FROM metric_dictionary_entry")
MIGRATION=$(psql_value "SELECT version_num FROM alembic_version")
HASH_INPUT=$(psql_value "SELECT string_agg(payload_hash, '' ORDER BY id) FROM objective_report_snapshot")
RESTORED_HASH=$(printf '%s' "$HASH_INPUT" | shasum -a 256 | awk '{print $1}')
API_CODE=$(curl --fail --silent --show-error --cacert "$CA_CERT" -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/health")
WEB_CODE=$(curl --fail --silent --show-error --cacert "$CA_CERT" -o /dev/null -w "%{http_code}" "$BASE_URL/")

export CONTRACT_PATH EVIDENCE_PATH BASE_URL API_CODE WEB_CODE
export STATEMENTS SNAPSHOTS METRICS MIGRATION RESTORED_HASH
python3 - <<'PYEOF'
import json
import os
from pathlib import Path

contract = json.loads(Path(os.environ["CONTRACT_PATH"]).read_text(encoding="utf-8"))
actual = {
    "statement_report": int(os.environ["STATEMENTS"]),
    "objective_report_snapshot": int(os.environ["SNAPSHOTS"]),
    "metric_dictionary_entry": int(os.environ["METRICS"]),
}
if os.environ["MIGRATION"] != contract["migration_head"]:
    raise SystemExit(f"migration mismatch: {os.environ['MIGRATION']} != {contract['migration_head']}")
for table, expected in contract["critical_tables"].items():
    if actual.get(table) != expected:
        raise SystemExit(f"critical table mismatch: {table}={actual.get(table)} expected={expected}")
if os.environ["RESTORED_HASH"] != contract["payload_hash_aggregate"]:
    raise SystemExit("frozen payload hash mismatch")
evidence = {
    "schema_version": 1,
    "mode": "restore-u8-baseline",
    "base_url": os.environ["BASE_URL"],
    "tls_verified": True,
    "health_status": int(os.environ["API_CODE"]),
    "web_status": int(os.environ["WEB_CODE"]),
    "downloads": [],
    "restore_exit_code": 0,
    "critical_tables": {
        table: {"before": expected, "after": actual[table]}
        for table, expected in contract["critical_tables"].items()
    },
    "expected_payload_hash": contract["payload_hash_aggregate"],
    "restored_payload_hash": os.environ["RESTORED_HASH"],
    "skipped": [],
}
Path(os.environ["EVIDENCE_PATH"]).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
PYEOF
