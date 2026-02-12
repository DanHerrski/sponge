# Sponge

Conversational knowledge graph that helps busy executives brain-dump ideas and surfaces the highest-value content paths to explore next.

## P0 Steel Thread

The MVP is built around a single end-to-end steel thread: chat input → nugget extraction → scoring → dedup → graph write → next-best question → UI render.

### Planning & Product

- [`docs/planning/90-day-bets-memo.md`](./docs/planning/90-day-bets-memo.md) — 90-day strategic bets (executive summary)
- [`docs/planning/engineering-tracker.md`](./docs/planning/engineering-tracker.md) — Kanban task tracker (Todo / Doing / Done)
- [`docs/planning/backlog.md`](./docs/planning/backlog.md) — P0 backlog (10 epics, 47 tasks)
- [`docs/planning/risks.md`](./docs/planning/risks.md) — Top 10 risks + kill/pivot criteria

### Architecture

- [`mvp_spec.md`](./mvp_spec.md) — Full MVP specification (P0 scope)
- [`docs/architecture/steel-thread.md`](./docs/architecture/steel-thread.md) — Steel thread definition + API contracts
- [`docs/architecture/technical-decisions.md`](./docs/architecture/technical-decisions.md) — P0 infrastructure decisions
- [`docs/architecture/schema.md`](./docs/architecture/schema.md) — Database schema (all P0 tables, fields, indexes)

See [`docs/README.md`](./docs/README.md) for the full documentation index.

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
docs/
  planning/          # Bets, PRDs, sprints, tracker
  architecture/      # Steel thread, tech decisions, schema
  setup/             # Local dev, deploy, storage guides
```
