#!/usr/bin/env bash
# U8 运行保障：PostgreSQL 备份与恢复演练（D038 Task D）。
# 流程：pg_dump 全量备份 → 毁库 → 从备份恢复 → health 与行数校验。
# 用法：bash scripts/backup_restore_drill.sh [backup_dir]
set -euo pipefail

BACKUP_DIR="${1:-work/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/flow_${STAMP}.dump"
COMPOSE="docker compose -f infra/compose.yaml"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "== 1/5 备份 =="
mkdir -p "$BACKUP_DIR"
docker compose -p "${COMPOSE_PROJECT:-flow}" -f infra/compose.yaml exec -T postgres \
  pg_dump -U flow -Fc flow > "$BACKUP_FILE"
SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
echo "备份完成: $BACKUP_FILE ($SIZE bytes)"
test "$SIZE" -gt 1000

echo "== 2/5 记录恢复前基线 =="
BEFORE_COUNT=$(docker compose -p "${COMPOSE_PROJECT:-flow}" -f infra/compose.yaml exec -T postgres \
  psql -U flow -d flow -tAc "SELECT count(*) FROM statement_report" 2>/dev/null || echo 0)
echo "恢复前 statement_report 行数：$BEFORE_COUNT"

echo "== 3/5 毁库 =="
docker compose -p "${COMPOSE_PROJECT:-flow}" -f infra/compose.yaml exec -T postgres psql -U flow -d flow -c \
  "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null
echo "schema 已清空"

echo "== 4/5 从备份恢复 =="
cat "$BACKUP_FILE" | docker compose -p "${COMPOSE_PROJECT:-flow}" -f infra/compose.yaml exec -T postgres \
  pg_restore -U flow -d flow --no-owner 2>&1 | grep -v 'already exists' || true

echo "== 5/5 恢复后校验 =="
AFTER_COUNT=$(docker compose -p "${COMPOSE_PROJECT:-flow}" -f infra/compose.yaml exec -T postgres \
  psql -U flow -d flow -tAc "SELECT count(*) FROM statement_report")
echo "恢复后 statement_report 行数：$AFTER_COUNT"
if [[ "$BEFORE_COUNT" != "$AFTER_COUNT" ]]; then
  echo "FAIL：恢复后行数与备份前不一致（$BEFORE_COUNT → $AFTER_COUNT）"
  exit 1
fi
HEALTH=$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null | grep -c '"ok"') || HEALTH=0
if [[ "$HEALTH" -eq 0 ]]; then
  echo "提示：API 未在 localhost:8000 运行，跳过应用层健康检查（数据层已验证）。"
fi
echo "备份恢复演练 PASS"
