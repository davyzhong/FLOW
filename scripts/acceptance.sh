#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export S3_ENDPOINT_URL="${S3_ENDPOINT_URL:-http://127.0.0.1:9000}"
export S3_BUCKET="${S3_BUCKET:-flow}"
export S3_ACCESS_KEY="${S3_ACCESS_KEY:-flow}"
export S3_SECRET_KEY="${S3_SECRET_KEY:-flow_dev_only}"

echo "[1/7] contract round trip"
bash scripts/test_data_contract.sh

echo "[2/7] metric known answers"
bash scripts/test_metrics_known_answers.sh

echo "[3/7] analysis invariants"
bash scripts/test_analysis_invariants.sh

echo "[4/7] intake e2e"
bash scripts/test_intake_e2e.sh

echo "[5/7] publishing golden"
bash scripts/test_publishing_golden.sh

echo "[6/7] investigation e2e"
bash scripts/test_investigation_e2e.sh

echo "[7/7] dashboard e2e"
bash scripts/test_dashboard.sh

echo "FLOW V1 acceptance suite passed."
