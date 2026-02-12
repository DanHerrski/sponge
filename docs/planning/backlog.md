# Sponge MVP — P0 Backlog

Reference: [`steel-thread.md`](../architecture/steel-thread.md) | [`mvp_spec.md`](../../mvp_spec.md) | [`technical-decisions.md`](../architecture/technical-decisions.md)

This backlog is organized around the steel thread. Epics 1–8 build the steel thread; Epics 9–10 extend it to complete P0 scope. Tasks within each epic are sized at ~0.5–2 days.

---

## Epic 1 — Project Scaffolding + Environments

**Objective:** Set up the monorepo structure, dev tooling, and local environment so any engineer can clone and run in under 10 minutes.

**Scope:**
- Backend: Python + FastAPI project with dependency management (Poetry or pip)
- Frontend: Next.js + TypeScript project with package manager (pnpm)
- Database: PostgreSQL + pgvector via Docker Compose
- CI: Linting + type checks on PR (GitHub Actions)

**Acceptance criteria:**
- `docker compose up` starts Postgres with pgvector enabled
- `make dev` (or equivalent) starts both backend and frontend
- Backend serves a health-check endpoint (`GET /health → 200`)
- Frontend loads a blank page at `localhost:3000`
- CI runs lint + type check on push

**Dependencies:** None (first epic)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 1.1 | Initialize monorepo structure: `/backend`, `/frontend`, root `docker-compose.yml`, `Makefile` | — (infra) | 0.5d |
| 1.2 | Set up FastAPI project: `main.py`, `pyproject.toml`, health-check route, Uvicorn config | — (infra) | 0.5d |
| 1.3 | Set up Next.js project: `create-next-app` with TypeScript, ESLint, Tailwind CSS | — (infra) | 0.5d |
| 1.4 | Docker Compose: Postgres 16 + pgvector image, volume, port mapping, env vars | — (infra) | 0.5d |
| 1.5 | Add Alembic for migrations, create initial empty migration | — (infra) | 0.5d |
| 1.6 | GitHub Actions CI: lint (ruff + eslint), type check (mypy + tsc), run on PR | — (infra) | 1d |

---

## Epic 2 — Core Data Model

**Objective:** Create the database schema that backs the knowledge graph, nuggets, and chat history.

**Scope:**
- All tables defined in [`steel-thread.md` § Minimal Persistence](../architecture/steel-thread.md#minimal-persistence-required)
- SQLAlchemy async models + Alembic migration
- Enum types for node_type, edge_type, nugget status, source_type, confidence
- pgvector column on nodes table

**Acceptance criteria:**
- Migration creates all 6 tables (sessions, chat_turns, nodes, edges, nuggets, provenance)
- All indexes from the steel thread doc are present
- Models can be imported and used in a test script that inserts + queries a sample row for each table
- pgvector similarity query works (`ORDER BY embedding <=> $1 LIMIT 5`)

**Dependencies:** Epic 1 (database running)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 2.1 | Define SQLAlchemy async models for `sessions` and `chat_turns` | Step 1 (Ingest) | 0.5d |
| 2.2 | Define SQLAlchemy async models for `nodes` (with vector column) and `edges` | Step 5 (Graph write) | 1d |
| 2.3 | Define SQLAlchemy async models for `nuggets` (JSONB fields for dimension_scores, missing_fields, next_questions) | Step 3 (Score) | 0.5d |
| 2.4 | Define SQLAlchemy async model for `provenance` | Step 5 (Graph write) | 0.5d |
| 2.5 | Create Alembic migration for all tables + indexes (including HNSW vector index) | All steps | 1d |
| 2.6 | Write smoke-test script: insert sample data into all tables, run a vector similarity query | All steps | 0.5d |

---

## Epic 3 — Chat Ingestion + Session Context

**Objective:** Accept a user chat message via API, store it, and assemble the context needed for downstream LLM calls.

**Scope:**
- `POST /chat_turn` endpoint (request parsing, validation, chat turn persistence)
- Session creation (auto-create on first turn)
- Context assembly: current message + recent chat history + existing top-N nodes (retrieved by embedding similarity)
- Return structured response (placeholder; full response composed in later epics)

**Acceptance criteria:**
- `POST /chat_turn` with `session_id` + `message` stores a chat turn and returns a `turn_id`
- If `session_id` is new, a session row is created automatically
- Context assembler returns: current message, last 5 turns, top 10 relevant nodes (or empty if none exist)

**Dependencies:** Epic 2 (tables exist)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 3.1 | Implement `POST /chat_turn` endpoint: validate request, create session if needed, store chat turn | Step 1 (Ingest) | 1d |
| 3.2 | Build context assembler: retrieve recent turns + top-N relevant nodes via pgvector similarity search | Step 1 (Ingest) | 1d |
| 3.3 | Add Pydantic request/response schemas for chat_turn (matching steel-thread API contract) | Step 7 (Compose) | 0.5d |

---

## Epic 4 — Nugget Extraction + Scoring

**Objective:** Given a user message and session context, extract candidate nuggets with types, summaries, and scores using an LLM structured-output call.

**Scope:**
- LLM prompt for nugget extraction (structured JSON output)
- Scoring across 6 dimensions (Specificity, Novelty, Authority, Actionability, Story Energy, Audience Resonance)
- Gap detection (missing_fields checklist)
- Consolidated single LLM call for extraction + scoring + gap detection (latency mitigation)

**Acceptance criteria:**
- Given a sample brain-dump message, the extractor returns 1–5 candidate nuggets as structured JSON
- Each nugget has: type, title, summary, key_phrases, total score, per-dimension scores, missing_fields
- Extraction + scoring completes in a single LLM call (not chained calls)
- Output validates against the Pydantic schema

**Dependencies:** Epic 3 (context assembler provides input)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 4.1 | Design extraction + scoring prompt: single structured-output call returning candidates with types, summaries, scores, and gaps | Steps 2+3 (Extract + Score) | 1.5d |
| 4.2 | Implement extraction service: call LLM, parse structured output, validate against Pydantic models | Steps 2+3 (Extract + Score) | 1d |
| 4.3 | Add embedding generation for each candidate (title + summary → OpenAI embedding) | Step 4 (Dedup) | 0.5d |
| 4.4 | Write extraction eval: 5 sample inputs, assert nugget count, type validity, score ranges | Steps 2+3 (Extract + Score) | 1d |

---

## Epic 5 — Deduplication + Merge Logic

**Objective:** Before persisting new nuggets, detect and handle duplicates by comparing embeddings against existing nodes.

**Scope:**
- Embedding similarity search against existing session nodes
- Threshold-based decision: merge, link as `expands_on`, or create new
- Handle edge case: first turn (no existing nodes → skip dedup)

**Acceptance criteria:**
- Sending the same idea in two separate turns does not create duplicate nodes
- The second occurrence is linked via `expands_on` edge to the original node
- Distinct ideas (even with similar vocabulary) remain as separate nodes
- Dedup threshold is configurable (env var or config)

**Dependencies:** Epic 4 (candidates have embeddings)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 5.1 | Implement similarity search: query pgvector for existing nodes above cosine similarity threshold | Step 4 (Dedup) | 1d |
| 5.2 | Implement merge/link decision logic: if above threshold → create `expands_on` edge; if below → insert new node | Step 4 (Dedup) | 1d |
| 5.3 | Write dedup tests: duplicate input returns link (not new node), distinct input creates new node | Step 4 (Dedup) | 0.5d |

---

## Epic 6 — Knowledge Graph Write + Retrieval

**Objective:** Persist extracted, scored, deduped nuggets as nodes + edges in the graph, and serve the graph for the mind map.

**Scope:**
- Insert nodes, edges, nuggets, and provenance rows in a single transaction
- Implement `GET /graph_view` returning nodes + edges for a session
- Implement `GET /node/:id` returning node detail with provenance and nugget data
- Auto-generate `related_to` edges between co-extracted nodes from the same turn

**Acceptance criteria:**
- After `POST /chat_turn`, new nodes, edges, nuggets, and provenance rows exist in the database
- `GET /graph_view?session_id=X` returns all nodes and edges for the session
- `GET /node/:id` returns node detail including provenance and nugget scores
- Co-extracted nodes are linked with `related_to` edges

**Dependencies:** Epic 5 (dedup determines which nodes to insert)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 6.1 | Implement graph write service: insert nodes + edges + nuggets + provenance in a single DB transaction | Step 5 (Graph write) | 1.5d |
| 6.2 | Auto-generate `related_to` edges between nodes extracted from the same turn | Step 5 (Graph write) | 0.5d |
| 6.3 | Implement `GET /graph_view` endpoint: return nodes + edges filtered by session_id | Step 7 (Compose) | 1d |
| 6.4 | Implement `GET /node/:id` endpoint: return node + provenance + nugget detail | Step 7 (Compose) | 0.5d |

---

## Epic 7 — Next-Best Question Policy

**Objective:** After extraction and graph write, select the single best deep-dive question plus 2 alternates, with a rationale sentence.

**Scope:**
- Question generation: LLM call targeting nuggets with highest gaps
- NextBestDiveScore computation across 5 dimensions (Impact, Leverage, Momentum, Connectivity, Gap Criticality)
- Select 1 primary + 2 alternates
- Generate "Why this next" sentence

**Acceptance criteria:**
- Given a session with 3+ nuggets, the policy returns 1 primary question + 2 alternates
- Each question targets a specific nugget and gap type (not generic)
- "Why this next" references the target nugget by name
- Question generation completes in < 3 seconds

**Dependencies:** Epic 6 (graph data available for scoring)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 7.1 | Design question generation prompt: given nuggets + missing_fields, produce specific questions per gap bucket | Step 6 (Next-best question) | 1d |
| 7.2 | Implement NextBestDiveScore: rank candidate questions across 5 dimensions, select top 3 | Step 6 (Next-best question) | 1d |
| 7.3 | Generate "Why this next" sentence referencing impact + momentum | Step 6 (Next-best question) | 0.5d |
| 7.4 | Wire into `POST /chat_turn` response: integrate question policy output into the API response schema | Step 7 (Compose) | 0.5d |

---

## Epic 8 — Steel-Thread UI (Chat + Mind Map + Next Question)

**Objective:** Build the minimal frontend that lets a user chat, see extracted nuggets, view the mind map, and see the next question — proving the full loop works visually.

**Scope:**
- Chat panel: text input, message list, structured assistant responses (nugget bullets + next question)
- Mind map panel: graph visualization of nodes + edges from `GET /graph_view`
- Next Question card: primary question + "Why this next" + 2 alternates
- No Nugget Inbox, no Node Detail Drawer, no affordance buttons (those are post-steel-thread)

**Acceptance criteria:**
- User can type a message and see a structured response with captured nuggets and next question
- Mind map renders nodes (colored/labeled by type) and edges after each turn
- Mind map updates after each chat turn (re-fetches graph)
- Next Question card shows 1 question + rationale + 2 alternates
- Layout matches spec §4.1: chat left, mind map right, next question card bottom/side

**Dependencies:** Epic 7 (full API response available)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 8.1 | Build chat panel component: text input, submit handler, message list (user + assistant) | UI render | 1d |
| 8.2 | Integrate `POST /chat_turn` API call from frontend, display structured response (nugget bullets + graph summary) | UI render | 1d |
| 8.3 | Build mind map component using React Flow: render nodes (type-colored) + edges from `GET /graph_view` | UI render | 1.5d |
| 8.4 | Auto-refresh mind map after each chat turn response | UI render | 0.5d |
| 8.5 | Build Next Question card component: primary question, "Why this next", 2 alternate paths | UI render | 1d |
| 8.6 | Implement page layout: chat left, mind map right, next question card bottom/side (responsive) | UI render | 0.5d |

---

## Epic 9 — Resource Upload Ingestion (Minimal)

**Objective:** Allow users to upload a document, extract nuggets from it, and feed them into the same graph pipeline as chat messages.

**Scope:**
- `POST /upload` endpoint: accept file, parse text, chunk, extract nuggets
- Supported formats: plain text, DOCX (PDF as best-effort)
- Post-upload response: "I found X ideas and Y stories" + top 3 nuggets + 3 deep-dive choices
- Local filesystem storage with FileStore abstraction

**Acceptance criteria:**
- User can upload a .txt or .docx file via the UI
- System extracts nuggets with provenance (document_id + chunk_id)
- Post-upload response matches spec §10.3 format
- Uploaded file is stored locally and retrievable

**Dependencies:** Epics 4–6 (extraction + scoring + graph write pipeline)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 9.1 | Implement FileStore abstraction: `save`, `get`, `delete` with local filesystem backend | — (infra) | 0.5d |
| 9.2 | Implement text parser: extract plain text from .txt and .docx files | — (ingestion) | 1d |
| 9.3 | Implement semantic chunker: split extracted text into coherent paragraph/topic-based chunks | — (ingestion) | 1d |
| 9.4 | Implement `POST /upload` endpoint: accept file, parse, chunk, run extraction pipeline per chunk | — (ingestion) | 1.5d |
| 9.5 | Compose upload response: summarize findings, return top 3 nuggets + 3 deep-dive options | — (ingestion) | 0.5d |
| 9.6 | Add upload button to frontend UI, display upload response in chat | — (UI) | 1d |

---

## Epic 10 — Observability + Guardrails

**Objective:** Add structured logging for key metrics and basic quality guardrails to prevent low-quality outputs.

**Scope:**
- Per-turn structured log: nugget count, avg score, selected question, user response length
- Anti-generic filter: suppress low-novelty nuggets from top results
- Duplication rate metric: track and log percentage of dedup-triggered turns
- Basic contradiction flag: detect and log (but don't block) contradicting ideas

**Acceptance criteria:**
- Each `POST /chat_turn` produces a structured log entry with all fields from spec §13.3
- Low-novelty nuggets (Novelty dimension < 20) are demoted in the response (not in top captured nuggets)
- Duplication rate is calculated and logged per session
- Contradicting nodes are flagged in the database (contradiction edge type) but not surfaced in UI for steel thread

**Dependencies:** Epics 4, 6, 7 (extraction, graph, question policy all active)

### Tasks

| # | Task | Steel Thread Step | Size |
|---|------|-------------------|------|
| 10.1 | Add structured logging middleware: log per-turn metrics (nugget count, avg score, selected question, latency) | — (observability) | 1d |
| 10.2 | Implement anti-generic filter: check Novelty dimension, demote low-scoring nuggets from top results | — (guardrails) | 0.5d |
| 10.3 | Add duplication rate metric: track dedup triggers per session, log rate | — (observability) | 0.5d |
| 10.4 | Implement soft contradiction detection: embedding similarity between nodes with opposing sentiment signals, flag as `contradicts` edge | — (guardrails) | 1d |
| 10.5 | Add follow-through tracking: compare suggested question with user's next message to estimate engagement | — (observability) | 1d |

---

## Backlog Summary

| Epic | Task Count | Estimated Size | Steel Thread? |
|------|-----------|----------------|---------------|
| 1. Project scaffolding | 6 | ~3.5d | Prerequisite |
| 2. Core data model | 6 | ~4d | Prerequisite |
| 3. Chat ingestion | 3 | ~2.5d | Steps 1, 7 |
| 4. Nugget extraction + scoring | 4 | ~4d | Steps 2, 3 |
| 5. Deduplication + merge | 3 | ~2.5d | Step 4 |
| 6. Graph write + retrieval | 4 | ~3.5d | Step 5 |
| 7. Next-best question | 4 | ~3d | Step 6 |
| 8. Steel-thread UI | 6 | ~5.5d | UI render |
| 9. Upload ingestion | 6 | ~5.5d | Post-thread P0 |
| 10. Observability + guardrails | 5 | ~4d | Post-thread P0 |
| **Total** | **47** | **~38d** | |

### Critical path (steel thread)

Epics 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

Epics 9 and 10 can start in parallel once Epics 4–6 are complete.
