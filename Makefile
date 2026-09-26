PNPM := npx --yes pnpm@10.17.1
UV := uv
COMPOSE := docker compose -f infra/compose.yaml

.PHONY: docs-check plan-views bootstrap contracts contracts-check infra-up infra-down stack-up stack-down dev-api dev-web test-api test-web test lint typecheck phase-1-acceptance test-data-contract test-intake-e2e test-metrics-known-answers test-analysis-invariants test-dashboard test-investigation-e2e test-copilot-evals test-publishing-golden test-user-closure-e2e test-statements-e2e test-module-boundaries-e2e

bootstrap:
	$(PNPM) install --frozen-lockfile
	cd services/api && $(UV) sync --all-groups --frozen

contracts:
	bash scripts/generate_contracts.sh

contracts-check:
	bash scripts/check_contracts.sh

infra-up:
	$(COMPOSE) up -d --wait --wait-timeout 120 postgres redis minio
	$(COMPOSE) up minio-init
	$(UV) run scripts/wait_for_services.py localhost:5432 localhost:6379 localhost:9000

infra-down:
	$(COMPOSE) down

stack-up:
	$(MAKE) infra-up
	$(COMPOSE) up -d --build --wait --wait-timeout 120 api worker web
	$(UV) run scripts/wait_for_services.py localhost:5432 localhost:6379 localhost:9000 localhost:8000 localhost:3000
	cd services/api && DATABASE_URL="$${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow}" $(UV) run alembic upgrade head
	cd services/api && $(UV) run python ../../scripts/seed_dev_principal.py

stack-down: infra-down

dev-api:
	cd services/api && $(UV) run uvicorn flow_api.main:app --reload --port 8000

dev-web:
	$(PNPM) --filter @flow/web dev

test-api:
	cd services/api && $(UV) run pytest -q

test-web:
	$(PNPM) --filter @flow/web test

test: test-api test-web

lint:
	cd services/api && $(UV) run ruff check src tests
	$(PNPM) --filter @flow/web lint

typecheck:
	cd services/api && $(UV) run mypy src
	$(PNPM) --filter @flow/web typecheck

phase-1-acceptance:
	bash scripts/accept_phase_1.sh

test-data-contract: infra-up
	bash scripts/test_data_contract.sh

test-intake-e2e: infra-up
	bash scripts/test_intake_e2e.sh

test-metrics-known-answers: infra-up
	bash scripts/test_metrics_known_answers.sh

test-analysis-invariants: infra-up
	bash scripts/test_analysis_invariants.sh

test-dashboard: infra-up
	bash scripts/test_dashboard.sh

test-investigation-e2e: infra-up
	bash scripts/test_investigation_e2e.sh

test-copilot-evals:
	bash scripts/test_copilot_evals.sh

test-publishing-golden: infra-up
	bash scripts/test_publishing_golden.sh

acceptance: infra-up
	bash scripts/acceptance.sh

test-user-closure-e2e:
	bash scripts/test_user_closure_e2e.sh

test-module-boundaries-e2e:
	bash scripts/test_module_boundaries_e2e.sh

test-statements-e2e: infra-up
	bash scripts/test_statements_e2e.sh

docs-check:
	python3 scripts/check_docs.py --phase m6

# ---------------------------------------------------------------------------
# 大麦 synthetic 演示（Task C1）：stack-up 保持空环境语义，大麦走独立命令
# ---------------------------------------------------------------------------
.PHONY: damai-demo-build damai-demo-seed damai-demo-verify damai-demo-up test-damai-demo-e2e

DAMAI_WORK := $(shell pwd)/work/damai-demo

damai-demo-build:
	PYTHONPATH=services/api/src python3 scripts/build_damai_demo.py --output fixtures/damai --check
	python3 scripts/build_damai_metric_coverage.py

damai-demo-seed:
	mkdir -p $(DAMAI_WORK)
	cd services/api && $(UV) run python ../../scripts/seed_damai_demo.py --output $(DAMAI_WORK)/seed_receipt.json

damai-demo-verify:
	mkdir -p $(DAMAI_WORK)
	cd services/api && $(UV) run python ../../scripts/verify_damai_demo.py \
		--api-url $${DAMAI_API_URL:-http://localhost:8000} --check-storage \
		--output $(DAMAI_WORK)/verify_receipt.json

damai-demo-up:
	$(MAKE) infra-up
	$(COMPOSE) up -d --build --wait --wait-timeout 120 api worker web
	$(UV) run scripts/wait_for_services.py localhost:5432 localhost:6379 localhost:9000 localhost:8000 localhost:3000
	cd services/api && DATABASE_URL="$${DATABASE_URL:-postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow}" $(UV) run alembic upgrade head
	cd services/api && $(UV) run python ../../scripts/seed_dev_principal.py
	$(MAKE) damai-demo-seed
	$(MAKE) damai-demo-verify

# Task C2：八页面真实 E2E 门禁（独立隔离栈，脚本内自清理）
test-damai-demo-e2e:
	bash scripts/test_damai_demo_e2e.sh

plan-views:
	python3 scripts/documentation/plan_views.py --write
	python3 scripts/documentation/plan_views.py --check
	python3 scripts/documentation/links.py --check
	$(UV) run --project services/api python -m unittest discover -s scripts/tests -p 'test_*.py'
