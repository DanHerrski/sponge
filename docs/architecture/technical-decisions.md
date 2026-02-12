# Sponge MVP — Technical Decisions (P0)

Reference: [`mvp_spec.md`](../../mvp_spec.md) (P0 scope only)

These decisions cover only P0-essential infrastructure choices. Each decision is scoped to what we need for MVP — not what we might need at scale.

---

## Decision 1 — Graph Storage: PostgreSQL with nodes/edges tables

### Decision
Use PostgreSQL with relational `nodes` and `edges` tables to store the knowledge graph. Do not use a dedicated graph database (Neo4j, etc.) for P0.

### Rationale
- The P0 graph is small and well-defined: 6 node types, 5 edge types (spec §5.1, §5.2). Traversal depth is shallow (mind map shows 5–20 nodes).
- PostgreSQL handles adjacency-list graph queries efficiently at this scale with simple JOINs or recursive CTEs.
- Eliminates the operational overhead of running and maintaining a second database.
- The team can use a single query language (SQL) and a single connection pool.
- JSONB columns provide schema flexibility for node metadata that may evolve (spec §5.3, §5.4 — nugget properties, provenance).

### Alternatives considered
| Alternative | Pros | Cons |
|-------------|------|------|
| **Neo4j** | Native graph traversal (Cypher), optimized for deep/complex queries | Separate infrastructure, Cypher learning curve, overkill for 5–20 node views, harder to host cheaply |
| **SQLite** | Zero-ops, single file | No concurrent writes, no vector extension maturity, doesn't scale to multi-user |

### Consequences
- Graph queries beyond 2–3 hops will require recursive CTEs, which are less ergonomic than Cypher. Acceptable for P0 where max traversal depth is ~2.
- If the graph grows to 10k+ nodes with deep traversal needs (post-MVP), migration to Neo4j becomes a real option. The nodes/edges table design maps cleanly to a graph DB import.
- Must add proper indexes on `edges(source_id, target_id, edge_type)` from day one.

---

## Decision 2 — Vector Storage: pgvector (PostgreSQL extension)

### Decision
Use pgvector as the vector storage backend for embeddings, running inside the same PostgreSQL instance as the relational data.

### Rationale
- Keeps all data in a single database — simplifies deployment, backups, and transactions.
- pgvector supports HNSW and IVFFlat indexes, which are sufficient for MVP-scale similarity search (hundreds to low thousands of embeddings).
- Deduplication (spec §6.3) and retrieval (spec §11) both need vector similarity. Co-locating vectors with their source rows enables efficient joins (e.g., find similar nodes AND return their metadata in one query).
- No additional service to manage or pay for.

### Alternatives considered
| Alternative | Pros | Cons |
|-------------|------|------|
| **Pinecone** | Managed, scalable, fast at high volume | External service dependency, network latency for every query, cost at scale, data leaves your infra |
| **Weaviate** | Hybrid search (vector + keyword), self-hostable | Another service to run, more complex setup, overkill for P0 |
| **ChromaDB** | Simple API, good for prototyping | Ephemeral/in-memory by default, less mature for production use |

### Consequences
- pgvector performance degrades at very high embedding counts (100k+). Not a concern for P0 (expecting < 5k embeddings in active use).
- Must choose an embedding model and dimension upfront. Recommend starting with OpenAI `text-embedding-3-small` (1536 dims) for cost/quality balance.
- If retrieval quality is insufficient, can swap to an external vector DB later without changing the application interface — abstract behind a `VectorStore` service interface.

---

## Decision 3 — Backend Framework: Python + FastAPI

### Decision
Use Python with FastAPI as the backend framework.

### Rationale
- The MVP is heavily LLM-driven: nugget extraction, scoring, question generation, dedup, retrieval (spec §3, §6, §7, §8). Python has the strongest ecosystem for LLM integration (OpenAI SDK, LangChain components, tiktoken, etc.).
- FastAPI provides async request handling (important for non-blocking LLM calls), automatic OpenAPI docs, and Pydantic-based request/response validation — which maps well to the structured outputs in the spec (spec §6.2, §5.3).
- The 6 API endpoints (spec §13.2) are straightforward CRUD + LLM orchestration — FastAPI handles this cleanly without heavy framework overhead.
- Type hints + Pydantic give meaningful type safety without the verbosity of a statically-typed language.

### Alternatives considered
| Alternative | Pros | Cons |
|-------------|------|------|
| **Node.js (Express/Fastify)** | Shared language with frontend (if Next.js), strong async model | LLM ecosystem is weaker in JS, no Pydantic equivalent for structured LLM output validation |
| **Django** | Batteries-included (ORM, admin, auth) | Heavier than needed for 6 endpoints, sync-first architecture is suboptimal for LLM call patterns |
| **Go** | Fast, compiled, strong concurrency | Poor LLM ecosystem, slower iteration speed for prompt engineering and pipeline changes |

### Consequences
- Frontend and backend use different languages (Python + TypeScript). This is a standard and well-understood split.
- Must use an async ORM or query builder (SQLAlchemy 2.0 async or asyncpg) to avoid blocking the event loop during DB queries.
- Use Alembic for database migrations from the start (aligns with Risk 10 mitigation in `risks.md`).

---

## Decision 4 — Frontend Framework: Next.js (React)

### Decision
Use Next.js (React) with TypeScript for the frontend.

### Rationale
- The UI has three interactive, real-time panels: Chat, Mind Map, and Next Question card (spec §4.1). React's component model handles this composition well.
- The mind map visualization requires a graph rendering library. React has mature options: React Flow for node-based UIs, or D3.js for custom force-directed layouts.
- Next.js provides file-based routing, SSR for initial load performance, and API route capability if lightweight BFF patterns are needed.
- TypeScript provides type safety for the complex data structures (nodes, edges, nuggets, scores).
- Large ecosystem and hiring pool.

### Alternatives considered
| Alternative | Pros | Cons |
|-------------|------|------|
| **Svelte/SvelteKit** | Smaller bundle, simpler reactivity model | Smaller ecosystem for graph visualization libraries, smaller hiring pool |
| **Vue/Nuxt** | Good DX, moderate ecosystem | Fewer graph visualization options, less community momentum for this use case |
| **Plain React (Vite)** | Simpler build, no SSR overhead | Loses file-based routing, SSR, and other Next.js conveniences; would need to add routing manually |

### Consequences
- Next.js adds build complexity compared to plain React. Acceptable tradeoff for the routing and SSR benefits.
- Must choose a graph visualization library early. Recommend starting with React Flow (purpose-built for interactive node graphs) and evaluating if custom D3 is needed.
- Streaming LLM responses to the chat will use server-sent events (SSE) or WebSockets — Next.js supports both patterns.

---

## Decision 5 — LLM Orchestration: Simple Router (not LangGraph)

### Decision
Use a simple sequential pipeline with a thin router layer for LLM orchestration. Do not adopt LangGraph or a full agent framework for P0.

### Rationale
- The P0 core loop (spec §3) is a deterministic sequence: Ingest → Extract → Score → Link → Prioritize → Respond. There are no conditional branches, cycles, or autonomous agent decisions in P0.
- A simple pipeline (Python functions chained together) is easier to debug, test, and profile than a graph-based orchestration framework.
- LangGraph's value is in complex multi-agent workflows with branching and state machines — none of which exist in P0 scope.
- Keeping orchestration simple makes it straightforward to consolidate LLM calls (a key latency mitigation — see `risks.md` Risk 5).

### Alternatives considered
| Alternative | Pros | Cons |
|-------------|------|------|
| **LangGraph** | Built-in state management, supports complex agent loops, good for multi-step reasoning | Over-engineered for a linear pipeline, adds abstraction layers that obscure latency, harder to debug |
| **LangChain (full)** | Rich tooling, prompt templates, output parsers | Heavy dependency, frequent breaking changes, abstractions add complexity without P0 benefit |
| **CrewAI / AutoGen** | Multi-agent orchestration | Designed for autonomous agents, not applicable to P0's deterministic pipeline |

### Consequences
- If post-MVP features require agent-like behavior (e.g., autonomous research, multi-step content generation), we may need to adopt LangGraph or similar. The simple router design doesn't prevent this — it's an additive change, not a rewrite.
- Must build our own lightweight abstractions for: structured output parsing, retry/fallback on LLM errors, and prompt management. Keep these minimal — functions, not frameworks.
- Use LangChain's individual components (e.g., text splitters, output parsers) à la carte if useful, without adopting the full chain abstraction.

---

## Decision 6 — Upload Storage: Local filesystem with S3-compatible abstraction

### Decision
Store uploaded files on the local filesystem for P0 development, behind an abstraction layer that can swap to S3-compatible storage later.

### Rationale
- P0 is single-user and likely running on a single server or local dev machine. Local filesystem is the simplest option with zero configuration.
- The spec (§10) requires storing uploaded files for provenance — the actual content is parsed and chunked at upload time, so the stored file is a reference/backup, not a hot-path read.
- An abstraction layer (e.g., a `FileStore` interface with `save`, `get`, `delete` methods) makes the S3 migration trivial when deploying to production.

### Alternatives considered
| Alternative | Pros | Cons |
|-------------|------|------|
| **S3 from day one** | Production-ready, scalable, durable | Requires AWS setup, IAM config, and network calls for every upload — unnecessary complexity for P0 dev |
| **Database BLOBs** | Everything in one place | Bloats the database, bad for large files, complicates backups |
| **MinIO (local S3)** | S3-compatible API locally | Another service to run, overkill for P0 |

### Consequences
- File uploads are not durable beyond the local machine. Acceptable for P0/dev. Must migrate to S3 before any production deployment.
- Must set a reasonable file size limit (e.g., 10MB) to avoid filling local disk.
- The `FileStore` abstraction adds minimal code (~50 lines) but saves significant migration effort later.

---

## Summary

| Concern | P0 Decision | Migrate when… |
|---------|-------------|---------------|
| Graph storage | PostgreSQL (nodes/edges tables) | Graph exceeds 10k nodes with deep traversal needs |
| Vector storage | pgvector | Embedding count exceeds 100k or retrieval quality insufficient |
| Backend | Python + FastAPI | N/A (long-term choice) |
| Frontend | Next.js (React + TypeScript) | N/A (long-term choice) |
| LLM orchestration | Simple router / pipeline | Post-MVP features require agent loops or branching workflows |
| Upload storage | Local filesystem + abstraction | Any deployment beyond local dev |
