PNPM := npx --yes pnpm@10.17.1
UV := uv
COMPOSE := docker compose -f infra/compose.yaml

.PHONY: bootstrap contracts contracts-check infra-up infra-down stack-up stack-down dev-api dev-web test-api test-web test lint typecheck phase-1-acceptance test-data-contract test-intake-e2e test-metrics-known-answers test-analysis-invariants

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
