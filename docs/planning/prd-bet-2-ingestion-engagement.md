# PRD-lite: Bet 2 — Content Ingestion & Engagement Surfaces

**Timeframe:** Weeks 7–9 | **Effort:** ~15 dev-days | **Owner:** Eng Lead
**Epics:** 9 (Upload Ingestion) + new work (Nugget Inbox, Node Detail Drawer, Onboarding)

---

## Problem Statement

The steel thread proves the core loop via chat, but executives often have existing materials (notes, transcripts, docs) they want to feed into the system. They also need ways to browse, manage, and drill into what the system has found — the chat alone is not enough for review and triage.

## Objective

Enable document upload ingestion into the same graph pipeline as chat. Add a Nugget Inbox for browsing/sorting extracted nuggets, a Node Detail Drawer for inspecting any node's provenance and gaps, and a lightweight onboarding flow for session context.

## Success Criteria

| Metric | Target |
|--------|--------|
| Upload → nuggets | .txt/.docx file produces 3+ nuggets with provenance |
| Post-upload response | Shows "I found X ideas, Y stories" + top 3 nuggets + 3 deep-dive choices |
| Nugget Inbox | Displays all nuggets sorted by score with type filter |
| Node Detail Drawer | Shows provenance, gap checklist, deep-dive questions for any node |
| Onboarding | User sets project name, topic, optional audience before first turn |

## User Flows

### Upload Flow
```
1. User clicks upload button → selects .txt or .docx file
2. System parses, chunks (semantic), extracts nuggets per chunk
3. Response: "I found 4 strong ideas and 2 supporting stories"
4. Shows top 3 nuggets + 3 deep-dive question choices
5. Nuggets appear in mind map + inbox with document provenance
```

### Inbox Flow
```
1. User opens Nugget Inbox (tab or side panel)
2. Sees ranked list: title, type badge, score, status (New/Explored/Parked)
3. Sorts by score, filters by type, searches by keyword
4. Clicks a nugget → opens Node Detail Drawer
```

### Node Detail Drawer
```
1. User clicks a node (from mind map or inbox)
2. Drawer shows: title, type, summary, provenance sources, gap checklist
3. "What's missing" section shows gaps (example, evidence, steps, etc.)
4. Top 5 deep-dive questions listed
5. Actions: Explore now (sets next question), Park, Merge duplicate
```

## Components

### Upload Ingestion (Epic 9)

| Component | Description | Size |
|-----------|-------------|------|
| FileStore abstraction | `save`, `get`, `delete` with local filesystem backend | 0.5d |
| Text parser | Extract plain text from .txt and .docx files | 1d |
| Semantic chunker | Split text into coherent paragraph/topic-based chunks | 1d |
| `POST /upload` endpoint | Accept file, parse, chunk, run extraction pipeline per chunk | 1.5d |
| Upload response composer | Summarize findings, return top 3 nuggets + 3 deep-dive options | 0.5d |
| Upload UI | Upload button in frontend, display response in chat | 1d |

### Engagement Surfaces (new)

| Component | Description | Size |
|-----------|-------------|------|
| Nugget Inbox component | List view with sort (score), filter (type), search (keyword) | 1.5d |
| `POST /nugget/:id/status` | Update nugget status (New → Explored / Parked) | 0.5d |
| Node Detail Drawer | Slide-out panel: title, summary, provenance, gaps, questions, actions | 2d |
| Onboarding flow | Project name, topic, audience inputs before first session turn | 1d |
| Session context integration | Pass onboarding data to LLM context assembly | 0.5d |

## API Additions

**POST /upload** — file multipart → `{ document_id, summary, top_nuggets[], deep_dive_choices[] }`

**POST /nugget/:id/status** — `{ status: "explored" | "parked" }` → `{ nugget_id, status }`

**GET /nuggets?session_id=X** — → `{ nuggets[] }` (sorted by score, filterable)

## Technical Notes

- Semantic chunking: split on paragraph boundaries, merge short paragraphs, respect topic shifts. Prefer simple heuristic over ML-based chunking for P0.
- DOCX parsing: use `python-docx` library. PDF is best-effort (use `pymupdf` or `pdfplumber`).
- Provenance must link nuggets back to document_id + chunk index.
- FileStore interface enables future S3 migration with zero application code changes.

## Risks (Bet 2-specific)

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF parsing unreliable | Medium | Start with .txt/.docx only; PDF as "best effort" with disclaimer |
| Chunking fragments ideas | Medium | Semantic chunking by paragraph/topic; show extracted content to user for correction |
| Inbox overwhelms with low-quality nuggets | Medium | Sort by score; anti-generic filter suppresses low-novelty items |

## Out of Scope (Bet 2)

- Voice transcription
- Google Docs / URL import
- Bulk upload (multiple files at once)
- Chat affordance buttons
- Observability / telemetry

## Definition of Done

A user can: (1) upload a .txt or .docx document and see extracted nuggets with provenance, (2) browse all session nuggets in a sortable/filterable inbox, (3) click any node to see its detail drawer with gaps and questions, and (4) set project context via onboarding before their first chat turn.
