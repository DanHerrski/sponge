# Sponge MVP — Steel Thread

Reference: [`mvp_spec.md`](../mvp_spec.md) | [`technical-decisions.md`](./technical-decisions.md) | [`risks.md`](./risks.md)

---

## Steel Thread Objective

The steel thread is the minimum end-to-end path that proves the core Sponge value loop works: a user sends a chat message, the system extracts and scores nuggets, writes them to a knowledge graph with edges, selects the next-best question with a rationale, and the UI renders captured nuggets alongside a mind map and the next question card. If this thin slice works, every other P0 feature is an extension of it. If it doesn't, no amount of polish elsewhere matters.

---

## In-Scope Components

- **Chat input:** User sends a free-text brain-dump message via the UI.
- **Nugget extraction:** LLM extracts candidate nodes (Idea, Story, Framework) with titles, summaries, and types from the user's message.
- **Nugget scoring:** Each extracted nugget receives a NuggetScore (0–100) with per-dimension breakdowns and a missing_fields checklist.
- **Deduplication:** Before persisting, new candidates are compared against existing nodes via embedding similarity; duplicates are merged or linked as `expands_on`.
- **Knowledge graph write:** New nodes and edges are persisted to PostgreSQL (nodes, edges, nuggets tables). Provenance is recorded.
- **Next-best question selection:** The system evaluates candidate deep-dive questions, selects 1 primary + 2 alternates, and generates a "Why this next" sentence.
- **API response:** `POST /chat_turn` returns a structured response containing captured nuggets, graph update summary, next question, rationale, and alternates.
- **UI rendering:** The frontend displays the chat response (nuggets + next question), and the mind map pane renders the current graph state.

---

## Out-of-Scope for Steel Thread

These are P0 features that are **not** part of the steel thread. They will be built after the thread is proven:

- Resource upload ingestion (`POST /upload`)
- Nugget Inbox view (list/filter/sort)
- Node Detail Drawer (full provenance, gap checklist, deep-dive questions)
- Node merge action (`POST /node/:id/merge`)
- Nugget status updates (`POST /nugget/:id/status`)
- Onboarding flow (project name, topic, audience)
- Session context / contradiction flagging
- Chat affordance buttons (Pause, Skip, Rephrase, Summarize)
- Answer mode buttons (Quick bullets, Tell a story, Give steps)
- Observability / telemetry logging
- Anti-generic filter and guardrails (beyond basic dedup)

---

## End-to-End Flow

```
User types message ──▶ Frontend sends POST /chat_turn
                              │
                              ▼
                    ┌─────────────────────┐
                    │  1. Ingest input     │
                    │     Parse message,   │
                    │     store chat turn  │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  2. Extract nuggets  │
                    │     LLM structured   │
                    │     output call      │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  3. Score nuggets    │
                    │     Per-dimension +  │
                    │     total score      │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  4. Dedup / merge    │
                    │     Embedding sim    │
                    │     against existing │
                    │     nodes            │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  5. Graph write      │
                    │     Insert nodes,    │
                    │     edges, nuggets,  │
                    │     provenance       │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  6. Select next-best │
                    │     question         │
                    │     1 primary +      │
                    │     2 alternates +   │
                    │     "why this next"  │
                    └────────┬────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  7. Compose response │
                    │     Structured JSON  │
                    │     with all parts   │
                    └────────┬────────────┘
                             │
                             ▼
              Frontend receives response
              ├── Chat panel: show captured nuggets + next question
              └── Mind map: GET /graph_view, render updated graph
```

### Step-by-step detail

1. **Ingest input** — Frontend sends user message to `POST /chat_turn`. Backend stores the raw message as a chat turn row (session_id, turn_number, role=user, content, timestamp).

2. **Extract nuggets** — Backend sends the user message + existing session context to the LLM with a structured-output prompt. The LLM returns a JSON array of candidate nodes, each with: type, title, summary, key_phrases.

3. **Score nuggets** — For each candidate, compute NuggetScore across 6 dimensions (Specificity, Novelty, Authority, Actionability, Story Energy, Audience Resonance). Also compute missing_fields checklist. This can be part of the same LLM call as extraction (consolidated call — see `risks.md` Risk 5).

4. **Dedup / merge** — Embed each candidate's title+summary. Query pgvector for existing nodes above a similarity threshold. If a match is found, link the new candidate as `expands_on` rather than creating a duplicate node. If no match, proceed to insert.

5. **Graph write** — Insert new nodes into the `nodes` table. Insert edges (e.g., `related_to` between co-extracted nodes, `expands_on` for dedup matches). Insert nugget records into the `nuggets` table. Record provenance linking each node to the chat_turn_id.

6. **Select next-best question** — From the current set of nuggets (new + existing), evaluate candidate deep-dive questions using the NextBestDiveScore dimensions (Impact, Leverage, Momentum, Connectivity, Gap Criticality). Return 1 primary question, 2 alternates, and a "Why this next" sentence.

7. **Compose response** — Assemble the structured API response: captured nuggets (2–4 bullets), graph update summary (1 sentence), next question, rationale, and alternates. Store the assistant response as a chat turn row.

---

## Minimal API Contracts

### POST /chat_turn

**Request:**
```json
{
  "session_id": "uuid",
  "message": "string (user's brain-dump text)"
}
```

**Response:**
```json
{
  "turn_id": "uuid",
  "captured_nuggets": [
    {
      "nugget_id": "uuid",
      "node_id": "uuid",
      "title": "string",
      "nugget_type": "Idea | Story | Framework",
      "score": 0-100,
      "is_new": true
    }
  ],
  "graph_update_summary": "string (1 sentence)",
  "next_question": {
    "question": "string",
    "target_nugget_id": "uuid",
    "gap_type": "example | evidence | steps | counterpoint | definition | audience | outcome",
    "why_this_next": "string (1 sentence)"
  },
  "alternate_paths": [
    {
      "question": "string",
      "target_nugget_id": "uuid",
      "gap_type": "string"
    }
  ]
}
```

### GET /graph_view

**Request:** `GET /graph_view?session_id={uuid}`

**Response:**
```json
{
  "nodes": [
    {
      "node_id": "uuid",
      "node_type": "Idea | Story | Framework | Definition | Evidence | Theme",
      "title": "string",
      "summary": "string",
      "score": 0-100
    }
  ],
  "edges": [
    {
      "edge_id": "uuid",
      "source_id": "uuid",
      "target_id": "uuid",
      "edge_type": "supports | example_of | expands_on | related_to | contradicts"
    }
  ]
}
```

### GET /node/:id

**Request:** `GET /node/{node_id}`

**Response:**
```json
{
  "node_id": "uuid",
  "node_type": "string",
  "title": "string",
  "summary": "string",
  "provenance": [
    {
      "source_type": "chat",
      "source_id": "uuid (chat_turn_id)",
      "timestamp": "ISO-8601",
      "confidence": "low | med | high"
    }
  ],
  "nugget": {
    "nugget_id": "uuid",
    "score": 0-100,
    "dimension_scores": {
      "specificity": 0-100,
      "novelty": 0-100,
      "authority": 0-100,
      "actionability": 0-100,
      "story_energy": 0-100,
      "audience_resonance": 0-100
    },
    "missing_fields": ["example", "evidence"],
    "next_questions": ["string"]
  }
}
```

---

## Minimal Persistence Required

All tables reside in PostgreSQL (see [`technical-decisions.md`](./technical-decisions.md) Decision 1).

### Tables

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| **sessions** | `id (uuid PK)`, `project_name`, `topic`, `created_at` | Group chat turns and graph into a session |
| **chat_turns** | `id (uuid PK)`, `session_id (FK)`, `turn_number (int)`, `role (user\|assistant)`, `content (text)`, `created_at` | Store conversation history |
| **nodes** | `id (uuid PK)`, `session_id (FK)`, `node_type (enum)`, `title (text)`, `summary (text)`, `embedding (vector(1536))`, `created_at` | Knowledge graph nodes |
| **edges** | `id (uuid PK)`, `session_id (FK)`, `source_id (FK→nodes)`, `target_id (FK→nodes)`, `edge_type (enum)`, `created_at` | Knowledge graph edges |
| **nuggets** | `id (uuid PK)`, `node_id (FK→nodes)`, `nugget_type (enum)`, `title (text)`, `short_summary (text)`, `score (int)`, `dimension_scores (jsonb)`, `missing_fields (jsonb)`, `next_questions (jsonb)`, `status (enum: new\|explored\|parked)`, `created_at` | Prioritization wrapper around high-value nodes |
| **provenance** | `id (uuid PK)`, `node_id (FK→nodes)`, `source_type (enum: chat\|upload)`, `source_id (uuid)`, `confidence (enum: low\|med\|high)`, `created_at` | Track where each node came from |

### Indexes (required for steel thread)

- `nodes(session_id)` — filter nodes by session
- `nodes` HNSW index on `embedding` column — vector similarity for dedup (pgvector)
- `edges(source_id)`, `edges(target_id)` — graph traversal
- `edges(session_id, edge_type)` — filtered graph view
- `nuggets(node_id)` — join nugget data to nodes
- `chat_turns(session_id, turn_number)` — ordered conversation retrieval

---

## Demo Acceptance Criteria

**The steel thread passes when all of the following are true:**

1. **Chat input works:** A user can type a free-text message in the UI and submit it. The message is sent to `POST /chat_turn` and stored as a chat turn.

2. **Nuggets are extracted:** The API response contains 1–4 captured nuggets with titles, types, and scores. Each nugget corresponds to a real idea from the user's input (not generic filler).

3. **Scores are meaningful:** Each nugget has a total NuggetScore (0–100) and per-dimension breakdowns. Scores vary across nuggets (not all identical).

4. **Dedup works:** Sending the same idea twice in separate messages does not create duplicate nodes. The second occurrence links to the first via `expands_on` or merges.

5. **Graph is persisted:** After 3 chat turns, `GET /graph_view` returns at least 3 nodes and 2 edges with correct types.

6. **Next question is relevant:** The response includes exactly 1 primary question targeting a specific nugget and gap type, plus 2 alternates. The "Why this next" sentence references the target nugget.

7. **UI renders the response:** The chat panel displays the captured nuggets and next question. The mind map pane renders the current graph with clickable nodes and visible edges.

8. **Round-trip latency:** The full `POST /chat_turn` request completes in under 8 seconds (p95). First token streams to the UI in under 4 seconds (p50).

---

## What Comes After the Steel Thread

Once the steel thread passes, extend it in this order (all P0):

1. Onboarding flow (session context: project name, topic, audience)
2. Resource upload ingestion (`POST /upload`)
3. Nugget Inbox view (list, filter, sort by score)
4. Node Detail Drawer (provenance, gap checklist, deep-dive questions)
5. Chat affordance buttons (Pause, Skip, Rephrase)
6. Observability + telemetry logging
7. Guardrails (anti-generic filter, contradiction flagging)
