PNPM := npx --yes pnpm@10.17.1
UV := uv
COMPOSE := docker compose -f infra/compose.yaml

.PHONY: bootstrap infra-up infra-down stack-up stack-down dev-api dev-web test-api test-web test lint typecheck

bootstrap:
	$(PNPM) install --frozen-lockfile
	cd services/api && $(UV) sync --all-groups --frozen

infra-up:
	$(COMPOSE) up -d postgres redis minio minio-init
	$(UV) run scripts/wait_for_services.py localhost:5432 localhost:6379 localhost:9000

infra-down:
	$(COMPOSE) down

stack-up: infra-up

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
