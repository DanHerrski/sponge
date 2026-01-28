.PHONY: db dev backend frontend migrate lint typecheck

# Start Postgres (pgvector)
db:
	docker compose up -d db

# Run backend (FastAPI + Uvicorn)
backend:
	cd backend && uvicorn app.main:app --reload --port 8000

# Run frontend (Next.js dev)
frontend:
	cd frontend && npm run dev

# Start everything
dev: db
	@echo "Database started. Run 'make backend' and 'make frontend' in separate terminals."

# Run Alembic migrations
migrate:
	cd backend && alembic upgrade head

# Rollback last migration
migrate-down:
	cd backend && alembic downgrade -1

# Lint
lint:
	cd backend && ruff check .
	cd frontend && npm run lint 2>/dev/null || true

# Type check
typecheck:
	cd backend && mypy app/ 2>/dev/null || true
	cd frontend && npx tsc --noEmit 2>/dev/null || true
