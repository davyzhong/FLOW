#!/usr/bin/env bash
# Fail-closed U8 production gate. No acceptance step may be skipped.
set -euo pipefail

MODE="${1:-}"
BASE_URL="${FLOW_U8_BASE_URL:-}"

case "$MODE" in
  full|restore-u8-baseline) ;;
  *) echo "ERROR unknown mode: ${MODE:-<missing>}" >&2; exit 2 ;;
esac

if [[ -z "$BASE_URL" ]]; then
  echo "ERROR FLOW_U8_BASE_URL is required" >&2
  exit 2
fi
case "$BASE_URL" in
  https://*) ;;
  *) echo "ERROR FLOW_U8_BASE_URL must use https://" >&2; exit 2 ;;
esac

if [[ "$MODE" == "restore-u8-baseline" ]]; then
  if [[ -z "${FLOW_U8_BACKUP_PATH:-}" ]]; then
    echo "ERROR FLOW_U8_BACKUP_PATH is required" >&2
    exit 2
  fi
  if [[ -z "${FLOW_U8_RESTORE_DATABASE:-}" ]]; then
    echo "ERROR FLOW_U8_RESTORE_DATABASE is required and must be isolated" >&2
    exit 2
  fi
fi

EVIDENCE_PATH="${FLOW_U8_EVIDENCE_PATH:-work/u8-acceptance/evidence.json}"
if [[ "${FLOW_U8_VALIDATE_ONLY:-0}" != "1" ]]; then
  if [[ "$MODE" == "full" ]]; then
    U8D_EVIDENCE_PATH="$EVIDENCE_PATH" bash scripts/u8d_acceptance.sh
  else
    bash scripts/restore_u8_baseline.sh "$FLOW_U8_BACKUP_PATH" "$FLOW_U8_RESTORE_DATABASE" "$EVIDENCE_PATH"
  fi
fi
[[ -f "$EVIDENCE_PATH" ]] || { echo "ERROR evidence does not exist: $EVIDENCE_PATH" >&2; exit 1; }
python3 scripts/u8_acceptance_evidence.py "$EVIDENCE_PATH"
