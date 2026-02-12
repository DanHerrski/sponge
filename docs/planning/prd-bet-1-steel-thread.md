# PRD-lite: Bet 1 — Steel Thread (Core Value Loop)

**Timeframe:** Weeks 1–6 | **Effort:** ~28.5 dev-days | **Owner:** Eng Lead
**Epics:** 1 (Scaffolding), 2 (Data Model), 3 (Chat Ingestion), 4 (Extraction + Scoring), 5 (Dedup), 6 (Graph Write), 7 (Next-Best Question), 8 (UI)

---

## Problem Statement

Busy executives have expertise but no efficient way to capture, organize, and prioritize their ideas for content creation. Existing tools are either too manual (docs, spreadsheets) or too shallow (simple chat). Sponge must prove that a conversational AI can extract structured insights, build a knowledge graph, and guide the user toward their highest-value content paths — all in a single, fluid session.

## Objective

Deliver a functional end-to-end steel thread: a user chats, the system extracts nuggets, scores them, deduplicates against existing nodes, writes to a knowledge graph, selects the next-best question, and renders the result in a chat + mind map + next question UI.

## Success Criteria

| Metric | Target |
|--------|--------|
| Chat input → structured response | Works for 3+ consecutive turns |
| Nuggets extracted per turn | 1–4 with titles, types, scores |
| Score variance | Scores differ across nuggets (not all identical) |
| Dedup | Same idea sent twice creates link, not duplicate |
| Graph persistence | 3+ nodes, 2+ edges after 3 turns |
| Next-best question | Targets specific nugget + gap type |
| End-to-end latency | p50 < 3s first token, p95 < 8s complete |
| UI renders | Chat panel + mind map + next question card |

## User Flow

```
1. User opens Sponge → sees empty chat + empty mind map
2. User types a brain-dump message → hits send
3. System responds with:
   - 2–4 captured nugget bullets (title, type, score)
   - "Mind map updated" summary (1 sentence)
   - Next-best question (1 primary)
   - "Why this next" (1 sentence)
   - 2 alternate paths
4. Mind map pane shows new nodes (colored by type) + edges
5. User continues chatting → graph grows → questions get more targeted
```

## Components

### Backend

| Component | Description | Backlog Ref |
|-----------|-------------|-------------|
| Project scaffolding | FastAPI + Next.js + Docker Compose + Alembic + CI | Epic 1 |
| Data model | 6 tables (sessions, chat_turns, nodes, edges, nuggets, provenance) + pgvector | Epic 2 |
| Chat ingestion | `POST /chat_turn` + session auto-create + context assembly | Epic 3 |
| Extraction + scoring | Single LLM call → structured JSON with types, scores, gaps | Epic 4 |
| Embedding generation | title+summary → OpenAI embedding (1536d) per nugget | Epic 4 |
| Dedup | pgvector similarity search → merge/link decision | Epic 5 |
| Graph write | Transaction: insert nodes + edges + nuggets + provenance | Epic 6 |
| Graph retrieval | `GET /graph_view` + `GET /node/:id` | Epic 6 |
| Next-best question | LLM question generation + NextBestDiveScore ranking | Epic 7 |

### Frontend

| Component | Description | Backlog Ref |
|-----------|-------------|-------------|
| Chat panel | Text input, message list, structured response rendering | Epic 8 |
| Mind map | React Flow graph visualization, type-colored nodes, edges | Epic 8 |
| Next Question card | Primary question + "why this next" + 2 alternates | Epic 8 |
| Layout | Chat left, mind map right, next question bottom | Epic 8 |
| API integration | `POST /chat_turn`, `GET /graph_view` from frontend | Epic 8 |

## API Contracts

**POST /chat_turn** — `{ session_id, message }` → `{ turn_id, captured_nuggets[], graph_update_summary, next_question, alternate_paths[] }`

**GET /graph_view** — `?session_id=X` → `{ nodes[], edges[] }`

**GET /node/:id** — → `{ node_id, title, summary, provenance[], nugget }`

Full contracts in [steel-thread.md](../architecture/steel-thread.md).

## Technical Decisions

- PostgreSQL + pgvector (single DB for relational + vector)
- FastAPI (async, Pydantic, strong LLM ecosystem)
- Next.js + React Flow (graph visualization)
- Simple sequential pipeline (no LangGraph)
- Consolidated LLM call for extraction + scoring (latency mitigation)

Full rationale in [technical-decisions.md](../architecture/technical-decisions.md).

## Risks (Bet 1-specific)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Extraction quality too low | Critical | Eval harness with 20 synthetic transcripts; iterate prompts before shipping |
| LLM latency > 5s | High | Consolidate to single LLM call; stream response; use faster model (Haiku/4o-mini) |
| Dedup too aggressive/permissive | High | Two-stage: embedding recall + LLM precision; configurable threshold |
| Mind map confuses users | High | Force-directed layout; max 10 nodes visible; progressive disclosure |

## Out of Scope (Bet 1)

- Resource upload ingestion
- Nugget Inbox view
- Node Detail Drawer
- Chat affordance buttons (Pause, Skip, Rephrase)
- Onboarding flow
- Observability / telemetry
- Contradiction flagging

## Definition of Done

The steel thread passes when a live demo shows: a user sends 3+ chat messages, sees extracted nuggets with meaningful scores, views a growing mind map, and receives targeted next-best questions that reference specific nuggets and gaps — with no manual intervention or mocked data.
