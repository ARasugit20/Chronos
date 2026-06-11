.PHONY: up down migrate seed test test-ci check-live lint

up:
	docker compose -f infra/docker-compose.yml up --build -d

down:
	docker compose -f infra/docker-compose.yml down -v

migrate:
	docker compose -f infra/docker-compose.yml exec backend alembic upgrade head

seed:
	docker compose -f infra/docker-compose.yml exec backend python -m app.seeds.seed

seed-demo:
	docker compose -f infra/docker-compose.yml exec backend python -m app.seed_demo

test-backend:
	docker compose -f infra/docker-compose.yml exec backend pytest tests/ -v --tb=short

test-postgres:
	bash scripts/start_test_postgres.sh start

test-ci: test-postgres
	bash scripts/run_ci_tests.sh tests/ -v --tb=short

check-live:
	python3 scripts/check_live_deploy.py $${CHRONOS_API_URL:-http://localhost:8000}

test-frontend:
	cd frontend && npm run test

lint-backend:
	cd backend && ruff check . && mypy app/

lint-frontend:
	cd frontend && npm run lint

logs:
	docker compose -f infra/docker-compose.yml logs -f backend worker
