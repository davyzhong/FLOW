#!/usr/bin/env bash
# U8-D 最终部署验收：隔离 compose project（全新卷=干净目标环境）复跑
# 迁移 → 启动健康 → 关键旅程（报表/指标库/驾驶舱）→ 备份恢复演练。
# 结束时销毁隔离环境并恢复常驻栈。
set -euo pipefail

PROJECT="u8accept"
COMPOSE="docker compose -p $PROJECT -f infra/compose.yaml"
API="http://localhost:8000"
WEB="http://localhost:3000"
OUT="docs/operations/u8d-acceptance.md"

say() { printf '%s\n' "$*"; }
{
  echo "# U8-D 干净环境部署验收记录"
  echo
  echo "- 时间：$(date '+%F %T %z')"
  echo "- 方式：隔离 compose project（${PROJECT}，全新卷）模拟干净目标环境"
  echo
} > "$OUT"

say "[1/6] 停常驻栈，释放端口"
docker compose -f infra/compose.yaml down >/dev/null 2>&1 || true

say "[2/6] 启动隔离栈（全新卷）"
$COMPOSE up -d postgres redis minio minio-init >/dev/null 2>&1
sleep 12

say "[3/6] 迁移到 head"
export DATABASE_URL="postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow" \
  REDIS_URL="redis://127.0.0.1:6379/0" S3_ENDPOINT_URL="http://127.0.0.1:9000" \
  S3_BUCKET="flow" S3_ACCESS_KEY="flow" S3_SECRET_KEY="flow_dev_only"
( cd services/api && uv run alembic upgrade head 2>&1 | tail -1 ) | tee -a "$OUT"

say "[4/6] 启动应用并做健康检查"
$COMPOSE up -d --wait --wait-timeout 300 api web worker >/dev/null 2>&1
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API/api/v1/health")
WEB_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$WEB/")
echo "- 健康检查：api=${API_CODE} web=${WEB_CODE}（期望 200/200）" >> "$OUT"
say "健康：api=${API_CODE} web=${WEB_CODE}"

say "[5/6] 关键旅程：空态读取 + 种子导入 + 发布冻结下载（U8-A 脚本复跑）"
EMPTY_STATEMENTS=$(curl -s "$API/api/v1/statements" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('reports', [])))")
echo "- 干净库空态：statements=${EMPTY_STATEMENTS}（期望 0）" >> "$OUT"
( cd services/api && .venv/bin/python -c "
from pathlib import Path
from flow_api.infrastructure.db import get_session_factory
from flow_api.metric_library_store.importer import import_all
with get_session_factory()() as s:
    print('种子导入:', import_all(s, Path('/Users/qiming/workspace/FLOW/config/metrics'))); s.commit()
" ) | tee -a "$OUT"
# 干净环境补一份最小财报种子（含冻结），随后复跑 U8-A 旅程脚本
( cd services/api && .venv/bin/python ../../scripts/seed_statement_reports.py \
    --yaml /Users/qiming/workspace/FLOW/docs/implementation/p5/cainiao_2021fy_statements.yaml \
    --company 菜鸟网络 --stock-code CAINIAO --report-kind 年报 --period-label FY2021 >/dev/null
  .venv/bin/python - <<'PYEOF'
from sqlalchemy import select
from flow_api.infrastructure.db import get_session_factory
from flow_api.infrastructure.models.statement import StatementReport
from flow_api.statements.normalization import normalize_report
from flow_api.statements.review import ReviewService
from flow_api.publishing.objective_freeze import freeze_objective_statement_report
with get_session_factory()() as s:
    for r in s.scalars(select(StatementReport)).all():
        normalize_report(s, r)
        ReviewService(s).publish(r.id, operator="flow.u8d.acceptance")
        freeze_objective_statement_report(s, report_id=r.id)
    s.commit()
    print("最小财报种子+冻结:", len(list(s.scalars(select(StatementReport)).all())))
PYEOF
) | tee -a "$OUT"
bash scripts/u8a_storage_journey.sh | tee -a "$OUT"

say "[6/6] 备份恢复演练（复跑 U8 备份脚本）"
if [[ -f scripts/backup_restore_drill.sh ]]; then
  COMPOSE_PROJECT=u8accept bash scripts/backup_restore_drill.sh 2>&1 | tail -3 | tee -a "$OUT"
fi

echo
echo "## 已知限制" >> "$OUT"
echo "- 自签 TLS 仅用于本地验收（infra/nginx），生产需换真实 CA 证书" >> "$OUT"
echo "- 量价类指标（volume_growth/price_change_rate）依赖 L2 内部数据，绑定如实缺失" >> "$OUT"

say "销毁隔离环境并恢复常驻栈"
$COMPOSE down -v >/dev/null 2>&1 || true
docker compose -f infra/compose.yaml up -d >/dev/null 2>&1
say "U8-D 验收记录写入 $OUT"
