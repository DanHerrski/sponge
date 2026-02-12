# Sprint Plan: Bet 1 — Steel Thread (Weeks 1–6)

**Goal:** Deliver a working end-to-end steel thread: chat → extract → score → dedup → graph → next question → UI.
**Capacity assumption:** 1 full-stack engineer, 5 dev-days per week.

---

## Week 1 — Scaffolding & Data Model Foundation

**Theme:** Get from zero to a running dev environment with all tables in place.

| Day | Task | Epic | Acceptance |
|-----|------|------|------------|
| Mon | 1.1 Initialize monorepo: `/backend`, `/frontend`, `docker-compose.yml`, `Makefile` | E1 | Directories exist, Makefile has `dev` target |
| Mon | 1.4 Docker Compose: Postgres 16 + pgvector, volume, port mapping | E1 | `docker compose up -d db` starts Postgres with pgvector |
| Tue | 1.2 FastAPI project: `main.py`, `pyproject.toml`, health-check route, Uvicorn | E1 | `GET /health → 200` |
| Tue | 1.3 Next.js project: TypeScript, ESLint, Tailwind CSS | E1 | `localhost:3000` loads blank page |
| Wed | 1.5 Alembic setup, initial empty migration | E1 | `alembic upgrade head` runs cleanly |
| Wed | 2.1 SQLAlchemy models: `sessions` + `chat_turns` | E2 | Models importable, fields match schema.md |
| Thu | 2.2 SQLAlchemy models: `nodes` (with vector column) + `edges` | E2 | pgvector column defined, enums for node_type/edge_type |
| Fri | 2.3 SQLAlchemy models: `nuggets` (JSONB: dimension_scores, missing_fields) | E2 | JSONB columns, nugget_type enum, status enum |
| Fri | 2.4 SQLAlchemy model: `provenance` | E2 | source_type/confidence enums, FK to nodes |

**Week 1 exit criteria:** `make dev` starts both backend and frontend. All 6 tables defined in SQLAlchemy models.

---

## Week 2 — Data Model Completion & Chat Ingestion

**Theme:** Finalize schema in the database and get the first API endpoint working.

| Day | Task | Epic | Acceptance |
|-----|------|------|------------|
| Mon | 2.5 Alembic migration: all tables + indexes (including HNSW vector index) | E2 | Migration creates all 6 tables, pgvector index exists |
| Tue | 2.6 Smoke-test script: insert sample data into all tables, vector similarity query | E2 | Script runs cleanly, similarity query returns results |
| Wed | 3.1 `POST /chat_turn` endpoint: validate, create session if needed, store turn | E3 | Endpoint accepts `{session_id, message}`, returns `turn_id` |
| Thu | 3.2 Context assembler: retrieve recent turns + top-N nodes via pgvector similarity | E3 | Returns current message + last 5 turns + top 10 nodes |
| Fri | 3.3 Pydantic request/response schemas matching steel-thread API contract | E3 | Schemas validate against steel-thread.md contracts |

**Week 2 exit criteria:** Database has all tables with indexes. `POST /chat_turn` stores a message, creates a session, and returns a turn_id. Context assembler retrieves history + relevant nodes.

---

## Week 3 — Nugget Extraction & Scoring

**Theme:** Build the LLM-powered extraction and scoring pipeline — the core intelligence.

| Day | Task | Epic | Acceptance |
|-----|------|------|------------|
| Mon–Tue | 4.1 Design extraction + scoring prompt: single structured-output call | E4 | Prompt documented; returns candidates with types, summaries, scores, gaps |
| Wed | 4.2 Extraction service: call LLM, parse structured output, validate with Pydantic | E4 | Given sample input, returns 1–5 nuggets as validated Pydantic models |
| Thu | 4.3 Embedding generation: title+summary → OpenAI embedding per candidate | E4 | Each candidate has a 1536-dim embedding vector |
| Fri | 4.4 Extraction eval: 5 sample inputs, assert nugget count, type validity, score ranges | E4 | Eval passes: precision > 70%, recall > 60% on sample set |

**Week 3 exit criteria:** Given a brain-dump message, the system extracts 1–5 nuggets with types, scores across 6 dimensions, missing_fields, and embeddings. Eval harness validates quality.

---

## Week 4 — Dedup & Graph Write

**Theme:** Prevent duplicate nodes and persist everything to the knowledge graph.

| Day | Task | Epic | Acceptance |
|-----|------|------|------------|
| Mon | 5.1 Similarity search: query pgvector for existing nodes above cosine threshold | E5 | Returns matching nodes above configurable threshold |
| Tue | 5.2 Merge/link decision: above threshold → `expands_on` edge; below → new node | E5 | Same idea twice → link; distinct ideas → separate nodes |
| Wed | 5.3 Dedup tests: duplicate creates link, distinct creates new node | E5 | Test suite passes |
| Thu | 6.1 Graph write service: insert nodes + edges + nuggets + provenance in transaction | E6 | Single transaction; rollback on failure |
| Fri | 6.2 Auto-generate `related_to` edges between co-extracted nodes from same turn | E6 | Nodes from same turn connected with `related_to` |

**Week 4 exit criteria:** Sending the same idea twice creates a link (not a duplicate). New nodes, edges, nuggets, and provenance are persisted in a single transaction.

---

## Week 5 — Graph Retrieval & Next-Best Question

**Theme:** Serve the graph for visualization and select the best question to ask next.

| Day | Task | Epic | Acceptance |
|-----|------|------|------------|
| Mon | 6.3 `GET /graph_view` endpoint: return nodes + edges by session_id | E6 | Returns all session nodes + edges with correct types |
| Mon | 6.4 `GET /node/:id` endpoint: return node + provenance + nugget detail | E6 | Full node detail with provenance and scores |
| Tue | 7.1 Question generation prompt: given nuggets + missing_fields → specific questions per gap | E7 | LLM produces targeted questions (not generic) |
| Wed | 7.2 NextBestDiveScore: rank questions across 5 dimensions, select top 3 | E7 | Top 3 ranked by Impact, Leverage, Momentum, Connectivity, Gap Criticality |
| Thu | 7.3 "Why this next" sentence: references impact + momentum | E7 | Sentence mentions target nugget by name |
| Fri | 7.4 Wire into `POST /chat_turn` response: full structured response with questions | E7 | API response includes nuggets + graph summary + question + alternates |

**Week 5 exit criteria:** Full API pipeline works end-to-end. `POST /chat_turn` returns extracted nuggets, graph updates, and a targeted next-best question with rationale. Graph endpoints serve data for visualization.

---

## Week 6 — Steel Thread UI

**Theme:** Build the frontend that makes the loop visible and interactive.

| Day | Task | Epic | Acceptance |
|-----|------|------|------------|
| Mon | 8.1 Chat panel component: text input, submit handler, message list | E8 | User can type and send messages; see user + assistant messages |
| Tue | 8.2 Integrate `POST /chat_turn` API: display structured response (nugget bullets + graph summary) | E8 | API call fires on submit; response renders with nuggets |
| Wed | 8.3 Mind map component: React Flow, type-colored nodes + edges from `GET /graph_view` | E8 | Graph renders with colored nodes and labeled edges |
| Thu | 8.4 Auto-refresh mind map after each chat turn | E8 | Map updates live after every turn response |
| Thu | 8.5 Next Question card: primary question + "why this next" + 2 alternates | E8 | Card renders below/beside chat with full content |
| Fri | 8.6 Page layout: chat left, mind map right, next question bottom (responsive) | E8 | Layout matches spec §4.1; responsive at common breakpoints |

**Week 6 exit criteria:** Steel thread demo-ready. User chats → sees nuggets + growing mind map + targeted questions. Full loop works with no mocked data.

---

## Bet 1 Milestone Checklist

- [ ] `make dev` starts full stack (backend + frontend + database)
- [ ] All 6 database tables exist with indexes
- [ ] `POST /chat_turn` extracts 1–4 nuggets with scores
- [ ] Dedup prevents duplicate nodes across turns
- [ ] `GET /graph_view` returns 3+ nodes, 2+ edges after 3 turns
- [ ] Next-best question targets specific nugget and gap type
- [ ] Chat panel renders structured responses
- [ ] Mind map shows type-colored nodes and edges, updates live
- [ ] Next Question card shows 1 primary + "why" + 2 alternates
- [ ] End-to-end latency p95 < 8 seconds
