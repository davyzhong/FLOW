#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$repo_root/services/api"
uv run alembic upgrade head
# P4：先把引擎目录 YAML 幂等入库（已知答案门禁在库内文档加载路径下执行）
uv run python -c "from flow_api.infrastructure.db import get_session_factory; from flow_api.metrics_store import import_metric_catalog_document; s = get_session_factory()(); import_metric_catalog_document(s, '../../config/metrics/flow_v1_metrics.yaml'); s.commit(); print('catalog document imported')"
uv run pytest tests/metrics tests/integration/test_metric_*.py -q
uv run pytest tests/integration/test_intake_e2e.py -q
uv run ruff check src tests migrations
uv run mypy src
uv run python ../../scripts/check_migrations.py
uv run python ../../scripts/summarize_metrics.py
