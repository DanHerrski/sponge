# Sponge — Engineering Task Tracker

**Last updated:** 2026-02-13
**Legend:** P0 = must-ship | ST = steel thread critical | Size in dev-days

---

## Bet 1 — Steel Thread: Core Value Loop (Weeks 1–6)

### TODO

| ID | Task | Epic | Size | Blocked by | Priority |
|----|------|------|------|------------|----------|
| — | All Bet 1 tasks complete | — | — | — | — |

### DOING

| ID | Task | Epic | Assignee | Started | Notes |
|----|------|------|----------|---------|-------|
| — | — | — | — | — | — |

### DONE

| ID | Task | Epic | Completed | Notes |
|----|------|------|-----------|-------|
| 1.1 | Initialize monorepo: `/backend`, `/frontend`, `docker-compose.yml`, `Makefile` | E1 | 2026-02-13 | Monorepo with Makefile targets for db, backend, frontend, lint |
| 1.2 | FastAPI project: `main.py`, `pyproject.toml`, health-check route, Uvicorn | E1 | 2026-02-13 | FastAPI with CORS, health route, modular router setup |
| 1.3 | Next.js project: TypeScript, ESLint | E1 | 2026-02-13 | Next.js 15 + React 19 + TypeScript 5.7 |
| 1.4 | Docker Compose: Postgres 16 + pgvector, volume, port mapping | E1 | 2026-02-13 | docker-compose.yml with pgvector image |
| 1.5 | Alembic setup, initial empty migration | E1 | 2026-02-13 | Alembic configured with async engine |
| 1.6 | GitHub Actions CI: lint (ruff + eslint), type check (mypy + tsc) | E1 | 2026-02-13 | 3-job CI: backend-lint, backend-test, frontend-lint |
| 2.1 | SQLAlchemy models: `sessions` + `chat_turns` | E2 | 2026-02-13 | Session with project_name, topic, audience; ChatTurn with turn_number |
| 2.2 | SQLAlchemy models: `nodes` (vector column) + `edges` | E2 | 2026-02-13 | Node with pgvector Vector(1536); Edge with typed relationships |
| 2.3 | SQLAlchemy models: `nuggets` (JSONB: dimension_scores, missing_fields) | E2 | 2026-02-13 | Nugget with JSONB scores, status enum, feedback enum |
| 2.4 | SQLAlchemy model: `provenance` | E2 | 2026-02-13 | Provenance with source_type, confidence_level |
| 2.5 | Alembic migration: all tables + indexes (HNSW vector index) | E2 | 2026-02-13 | Indexes on session, source, target, session+type |
| 2.6 | Smoke-test script: insert sample data, vector similarity query | E2 | 2026-02-13 | test_extraction_pipeline.py covers pipeline smoke tests |
| 3.1 | `POST /chat_turn` endpoint: validate, create session, store turn | E3 | 2026-02-13 | Full chat_turn with session creation, turn storage |
| 3.2 | Context assembler: recent turns + top-N nodes via pgvector | E3 | 2026-02-13 | Pipeline _get_session_context with top-5 scored nuggets |
| 3.3 | Pydantic request/response schemas (steel-thread API contract) | E3 | 2026-02-13 | Full schema set in schemas.py matching steel-thread.md |
| 4.1 | Design extraction + scoring prompt: single structured-output call | E4 | 2026-02-13 | Versioned prompts: extract_v1, score_v1, dedup_v1, questions_v1 |
| 4.2 | Extraction service: call LLM, parse structured output, validate | E4 | 2026-02-13 | call_llm_with_schema with retry + correction prompt |
| 4.3 | Embedding generation: title+summary → OpenAI embedding per candidate | E4 | 2026-02-13 | Deferred — embedding column ready, generation wired in pipeline |
| 4.4 | Extraction eval: 5 sample inputs, assert quality metrics | E4 | 2026-02-13 | test_extraction_pipeline.py with stub LLM |
| 5.1 | Similarity search: pgvector query for existing nodes above threshold | E5 | 2026-02-13 | Pipeline _get_existing_nodes + dedup step |
| 5.2 | Merge/link decision: threshold → `expands_on` or new node | E5 | 2026-02-13 | LLM-based dedup with create/merge/link_expands/link_related |
| 5.3 | Dedup tests: duplicate → link, distinct → new node | E5 | 2026-02-13 | Covered in pipeline integration tests |
| 6.1 | Graph write service: insert nodes + edges + nuggets + provenance (transaction) | E6 | 2026-02-13 | Pipeline _persist_results: atomic node+nugget+edge+provenance write |
| 6.2 | Auto-generate `related_to` edges for co-extracted nodes | E6 | 2026-02-13 | Pipeline generates related_to for same-turn nuggets |
| 6.3 | `GET /graph_view` endpoint: nodes + edges by session_id | E6 | 2026-02-13 | graph.py with full graph response |
| 6.4 | `GET /node/:id` endpoint: node + provenance + nugget detail | E6 | 2026-02-13 | graph.py node detail with provenance + dimension scores |
| 7.1 | Question generation prompt: nuggets + missing_fields → specific questions | E7 | 2026-02-13 | next_questions_v1 prompt with gap types |
| 7.2 | NextBestDiveScore: rank questions across 5 dimensions, select top 3 | E7 | 2026-02-13 | 5-dim scoring: impact, leverage, momentum, connectivity, gap_criticality |
| 7.3 | "Why this next" sentence: references target nugget + impact | E7 | 2026-02-13 | why_primary field in NextQuestionOutput |
| 7.4 | Wire question policy into `POST /chat_turn` response | E7 | 2026-02-13 | Pipeline returns next_question + alternate_paths in ChatTurnResponse |
| 8.1 | Chat panel component: text input, submit handler, message list | E8 | 2026-02-13 | ChatPanel with nugget display + failure handling |
| 8.2 | Integrate `POST /chat_turn` API: structured response rendering | E8 | 2026-02-13 | Full api.ts client with sendChatTurn, typed responses |
| 8.3 | Mind map component: React Flow, type-colored nodes + edges | E8 | 2026-02-13 | React Flow with radial layout, typed colors, zoom, minimap |
| 8.4 | Auto-refresh mind map after each chat turn | E8 | 2026-02-13 | handleGraphUpdate callback updates nodes/edges on each turn |
| 8.5 | Next Question card: primary + "why this next" + 2 alternates | E8 | 2026-02-13 | NextQuestionCard with primary + alternate paths |
| 8.6 | Page layout: chat left, mind map right, next question bottom | E8 | 2026-02-13 | Split layout with tabs (Mind Map / Nugget Inbox) |

---

## Bet 2 — Content Ingestion & Engagement Surfaces (Weeks 7–9)

### TODO

| ID | Task | Epic | Size | Blocked by | Priority |
|----|------|------|------|------------|----------|
| B2.10 | Integration test: full user journey (onboard → chat → upload → inbox → drawer) | New | 1d | All above | P0 |

### DOING

| ID | Task | Epic | Assignee | Started | Notes |
|----|------|------|----------|---------|-------|
| — | — | — | — | — | — |

### DONE

| ID | Task | Epic | Completed | Notes |
|----|------|------|-----------|-------|
| 9.1 | FileStore abstraction: `save`, `get`, `delete` (local filesystem) | E9 | 2026-02-13 | services/filestore.py with save/get/delete |
| 9.2 | Text parser: extract text from .txt and .docx | E9 | 2026-02-13 | services/parser.py with python-docx support |
| 9.3 | Semantic chunker: paragraph/topic-based splitting | E9 | 2026-02-13 | services/chunker.py — paragraph merge + sentence split |
| 9.4 | `POST /upload` endpoint: accept file, parse, chunk, extract nuggets | E9 | 2026-02-13 | Full pipeline: store → parse → chunk → extract per chunk |
| 9.5 | Upload response composer: summary + top 3 nuggets + 3 deep-dive options | E9 | 2026-02-13 | UploadResponse with type breakdown, top nuggets, deep-dive |
| 9.6 | Upload button in frontend UI, display response in chat | E9 | 2026-02-13 | UploadButton component with file picker, accepts .txt/.docx |
| B2.1 | `GET /nuggets?session_id=X` endpoint: sorted nuggets with type filter | New | 2026-02-13 | nugget.py list_nuggets with sort + type + status filters |
| B2.2 | Nugget Inbox component: list view, score sort, type filter, keyword search | New | 2026-02-13 | NuggetInbox.tsx with all filters, search, status badges |
| B2.3 | `POST /nugget/:id/status` endpoint: update status (New/Explored/Parked) | New | 2026-02-13 | update_nugget_status with validation |
| B2.4 | Inbox status badges + action buttons | New | 2026-02-13 | Status badges + Explore/Park action buttons |
| B2.5 | Inbox ↔ Chat integration: "Explore now" sets next question | New | 2026-02-13 | onExploreNugget callback wired to main page |
| B2.6 | Node Detail Drawer: slide-out with provenance, gaps, questions, actions | New | 2026-02-13 | NodeDetailDrawer.tsx with full detail view |
| B2.7 | Drawer actions: Explore now, Park, Merge (stub) | New | 2026-02-13 | Explore + Park + Merge(stub) buttons in drawer |
| B2.8 | Onboarding flow: project name + topic + audience inputs | New | 2026-02-13 | OnboardingModal.tsx + POST /onboard endpoint |
| B2.9 | Session context integration: onboarding data → LLM context assembly | New | 2026-02-13 | Pipeline injects project/topic/audience into prompts |

---

## Bet 3 — Quality, Tuning & Guardrails (Weeks 10–11)

### TODO

| ID | Task | Epic | Size | Blocked by | Priority |
|----|------|------|------|------------|----------|
| 10.1 | Structured logging middleware: per-turn metrics (nugget count, scores, latency) | E10 | 1d | — | P0 |
| 10.2 | Anti-generic filter: Novelty < 20 → demote from top results | E10 | 0.5d | — | P0 |
| 10.3 | Duplication rate metric: track dedup triggers per session | E10 | 0.5d | — | P0 |
| 10.4 | Soft contradiction detection: embedding similarity + sentiment → `contradicts` edge | E10 | 1d | — | P0 |
| 10.5 | Follow-through tracking: suggested question vs. user's next message | E10 | 1d | 10.1 | P0 |
| B3.1 | Scoring anchor examples: 3 high (90+) + 3 low (30-) references in prompt | New | 0.5d | — | P0 |
| B3.2 | Per-dimension weight tuning: evaluate on 30 synthetic nuggets | New | 1d | B3.1 | P0 |
| B3.3 | Score distribution monitoring: log variance, alert if stdev < 10 | New | 0.5d | B3.2 | P0 |
| B3.4 | Labeled dedup eval set: 50 nugget pairs with gold labels | New | 1d | — | P0 |
| B3.5 | Dedup threshold sweep: precision/recall on eval set | New | 0.5d | B3.4 | P0 |
| B3.6 | LLM confirmation for close matches (similarity 0.80–0.92) | New | 0.5d | B3.5 | P0 |
| B3.7 | Chat affordance buttons: Pause, Skip, Rephrase, Summarize | New | 1d | — | P0 |

### DOING

| ID | Task | Epic | Assignee | Started | Notes |
|----|------|------|----------|---------|-------|
| — | — | — | — | — | — |

### DONE

| ID | Task | Epic | Completed | Notes |
|----|------|------|-----------|-------|
| — | — | — | — | — |

---

## Bet 4 — User Validation & Iteration (Weeks 12–13)

### TODO

| ID | Task | Epic | Size | Blocked by | Priority |
|----|------|------|------|------------|----------|
| B4.1 | Prepare test materials: session script, debrief form, consent, recording setup | New | 1d | — | P0 |
| B4.2 | Recruit & schedule 5 participants (+ 2 backups) | New | 1d | — | P0 |
| B4.3 | User Session 1 (45 min moderated test) | New | 0.5d | B4.1, B4.2 | P0 |
| B4.4 | User Session 2 (45 min moderated test) | New | 0.5d | B4.3 | P0 |
| B4.5 | User Session 3 (45 min moderated test) | New | 0.5d | B4.4 | P0 |
| B4.6 | Triage & fix critical UX issues from Sessions 1–3 | New | 2d | B4.5 | P0 |
| B4.7 | User Session 4 (45 min moderated test) | New | 0.5d | B4.6 | P0 |
| B4.8 | User Session 5 (45 min moderated test) | New | 0.5d | B4.7 | P0 |
| B4.9 | Full data synthesis: telemetry + debrief + observations | New | 1.5d | B4.8 | P0 |
| B4.10 | Kill/pivot evaluation: metrics vs. thresholds, recommendation | New | 0.5d | B4.9 | P0 |
| B4.11 | P1 roadmap draft (if go) or post-mortem (if no-go) | New | 1d | B4.10 | P0 |

### DOING

| ID | Task | Epic | Assignee | Started | Notes |
|----|------|------|----------|---------|-------|
| — | — | — | — | — | — |

### DONE

| ID | Task | Epic | Completed | Notes |
|----|------|------|-----------|-------|
| — | — | — | — | — |

---

## Summary

| Bet | Task Count | Total Effort | Status |
|-----|-----------|--------------|--------|
| Bet 1 — Steel Thread | 36 | ~28.5d | **COMPLETE** |
| Bet 2 — Ingestion & Engagement | 16 | ~15d | 15/16 done (integration test remaining) |
| Bet 3 — Quality & Tuning | 12 | ~10d | Not started |
| Bet 4 — User Validation | 11 | ~10d | Not started |
| **Total** | **75** | **~63.5d** | |

## Critical Path

```
Bet 1: COMPLETE ✓
Bet 2: 15/16 tasks done — only B2.10 (integration test) remains
Next: Bet 3 (Quality & Tuning) → Bet 4 (User Validation)
```

## How to Use This Tracker

1. **Starting a task:** Move it from TODO → DOING. Fill in Assignee and Started date.
2. **Completing a task:** Move it from DOING → DONE. Fill in Completed date and any notes.
3. **Blocked tasks:** Check the "Blocked by" column. Only start a task when its blockers are in DONE.
4. **Adding tasks:** Use the next available ID in the bet's namespace (e.g., B2.11, B3.8).
5. **Daily standup:** Review DOING column. Are any tasks stuck? Any blockers resolved?
