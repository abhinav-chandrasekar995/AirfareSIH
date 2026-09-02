.PHONY: help up down seed migrate backend frontend test lint seed-local

help:
	@echo "India Airfare Intelligence"
	@echo "  make up          - docker compose up (full portable stack + seed)"
	@echo "  make down        - stop the stack"
	@echo "  make migrate     - run DB migrations (needs DATABASE_URL)"
	@echo "  make seed        - load the deterministic seed dataset"
	@echo "  make backend     - run the API locally (uvicorn)"
	@echo "  make frontend    - run the Next.js dev server"
	@echo "  make test        - run backend tests"
	@echo "  make lint        - ruff + import-boundary check"

up:
	docker compose up --build

down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m seeds.load_seed

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app && lint-imports
