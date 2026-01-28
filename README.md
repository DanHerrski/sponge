# Sponge

Conversational knowledge graph that helps busy executives brain-dump ideas and surfaces the highest-value content paths to explore next.

## P0 Steel Thread

The MVP is built around a single end-to-end steel thread: chat input → nugget extraction → scoring → dedup → graph write → next-best question → UI render. All planning docs are in `/docs`:

- [`mvp_spec.md`](./mvp_spec.md) — Full MVP specification (P0 scope)
- [`docs/risks.md`](./docs/risks.md) — Top 10 risks + kill/pivot criteria
- [`docs/technical-decisions.md`](./docs/technical-decisions.md) — P0 infrastructure decisions
- [`docs/steel-thread.md`](./docs/steel-thread.md) — Steel thread definition + API contracts + acceptance criteria
- [`docs/backlog.md`](./docs/backlog.md) — P0 backlog (10 epics, 47 tasks)
- [`docs/schema.md`](./docs/schema.md) — Database schema (all P0 tables, fields, indexes)

## Quick Start

```bash
# Start Postgres (pgvector)
docker compose up -d db

# Install backend dependencies
cd backend && pip install -e ".[dev]"

# Run migrations
make migrate

# Start backend (http://localhost:8000)
make backend

# Start frontend (http://localhost:3000)
cd frontend && npm install && npm run dev
```

## Project Structure

```
backend/
  app/
    main.py          # FastAPI application
    config.py        # Environment settings
    database.py      # Async SQLAlchemy engine
    schemas.py       # Pydantic request/response models
    models/          # SQLAlchemy ORM models
    routes/          # API endpoint handlers
    services/        # Business logic (placeholder)
  alembic/           # Database migrations
frontend/
  src/
    app/             # Next.js pages
    components/      # React components
docs/                # Planning & architecture docs
```
